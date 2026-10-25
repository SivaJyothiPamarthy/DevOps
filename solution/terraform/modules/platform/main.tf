data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  name = "fikapay-${var.env}"
  azs  = slice(data.aws_availability_zones.available.names, 0, 3)
}

# ---------------- Network: 3 AZs, public + private subnets ----------------
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.13"

  name = local.name
  cidr = var.vpc_cidr
  azs  = local.azs

  private_subnets = [for i, _ in local.azs : cidrsubnet(var.vpc_cidr, 4, i)]
  public_subnets  = [for i, _ in local.azs : cidrsubnet(var.vpc_cidr, 8, 48 + i)]

  enable_nat_gateway = true
  # Cost vs. resilience trade-off: one NAT in staging, one per AZ in production.
  single_nat_gateway     = var.env != "production"
  one_nat_gateway_per_az = var.env == "production"

  enable_dns_hostnames = true

  # Tags so the AWS Load Balancer Controller can discover subnets
  public_subnet_tags  = { "kubernetes.io/role/elb" = 1 }
  private_subnet_tags = { "kubernetes.io/role/internal-elb" = 1 }
}

# ---------------- Kubernetes: EKS with nodes in private subnets ----------------
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.24"

  cluster_name    = local.name
  cluster_version = var.cluster_version

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  cluster_endpoint_public_access           = true # restrict with cluster_endpoint_public_access_cidrs in real life
  enable_cluster_creator_admin_permissions = true
  enable_irsa                              = true

  cluster_addons = {
    coredns                = {}
    kube-proxy             = {}
    vpc-cni                = {}
    eks-pod-identity-agent = {}
  }

  eks_managed_node_groups = {
    default = {
      instance_types = var.node_instance_types
      min_size       = var.node_min
      max_size       = var.node_max
      desired_size   = var.node_min
      capacity_type  = var.env == "production" ? "ON_DEMAND" : "SPOT"
    }
  }
}

# ---------------- Container registry ----------------
resource "aws_ecr_repository" "orders" {
  name                 = "orders-service"
  image_tag_mutability = "IMMUTABLE" # a SHA tag can never be overwritten
  image_scanning_configuration { scan_on_push = true }
  encryption_configuration { encryption_type = "KMS" }
  force_delete = var.env != "production"
}

resource "aws_ecr_lifecycle_policy" "orders" {
  repository = aws_ecr_repository.orders.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 50 images"
      selection    = { tagStatus = "any", countType = "imageCountMoreThan", countNumber = 50 }
      action       = { type = "expire" }
    }]
  })
}

# ---------------- CI access: GitHub Actions OIDC, no long-lived AWS keys ----------------
data "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com" # created once per account
}

data "aws_iam_policy_document" "github_trust" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [data.aws_iam_openid_connect_provider.github.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      # Only the matching GitHub Environment can assume this env's role
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repo}:environment:${var.env}"]
    }
  }
}

resource "aws_iam_role" "ci_deploy" {
  name               = "${local.name}-ci-deploy"
  assume_role_policy = data.aws_iam_policy_document.github_trust.json
}

data "aws_iam_policy_document" "ci_deploy" {
  statement {
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }
  statement {
    actions = [
      "ecr:BatchCheckLayerAvailability", "ecr:InitiateLayerUpload", "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload", "ecr:PutImage", "ecr:BatchGetImage", "ecr:DescribeImages",
    ]
    resources = [aws_ecr_repository.orders.arn]
  }
  statement {
    actions   = ["eks:DescribeCluster"]
    resources = [module.eks.cluster_arn]
  }
}

resource "aws_iam_role_policy" "ci_deploy" {
  role   = aws_iam_role.ci_deploy.id
  policy = data.aws_iam_policy_document.ci_deploy.json
}

# Let the CI role deploy into its namespace only (EKS access entries, no aws-auth editing)
resource "aws_eks_access_entry" "ci" {
  cluster_name  = module.eks.cluster_name
  principal_arn = aws_iam_role.ci_deploy.arn
}

resource "aws_eks_access_policy_association" "ci" {
  cluster_name  = module.eks.cluster_name
  principal_arn = aws_iam_role.ci_deploy.arn
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSEditPolicy"
  access_scope {
    type       = "namespace"
    namespaces = ["orders-${var.env}"]
  }
  depends_on = [aws_eks_access_entry.ci]
}
