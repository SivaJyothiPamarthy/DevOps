terraform {
  required_version = ">= 1.10"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.70" }
  }
  backend "s3" {
    bucket       = "fikapay-tfstate-123456789012" # from bootstrap/
    key          = "production/platform.tfstate"
    region       = "eu-north-1"
    encrypt      = true
    use_lockfile = true # native S3 locking (Terraform >= 1.10); older setups use a DynamoDB table
  }
}

provider "aws" {
  region = "eu-north-1"
  default_tags {
    tags = {
      Environment = "production"
      ManagedBy   = "terraform"
      Owner       = "platform-team"
      CostCenter  = "orders"
    }
  }
}

module "platform" {
  source = "../../modules/platform"

  env         = "production"
  vpc_cidr    = "10.20.0.0/16"
  node_min    = 3
  node_max    = 10
  github_repo = "SivaJyothiPamarthy/DevOps"
}

output "platform" {
  value = module.platform
}
