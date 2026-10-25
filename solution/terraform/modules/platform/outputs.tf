output "cluster_name" {
  value = module.eks.cluster_name
}

output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "ecr_repository_url" {
  value = aws_ecr_repository.orders.repository_url
}

output "ci_deploy_role_arn" {
  value = aws_iam_role.ci_deploy.arn
}
