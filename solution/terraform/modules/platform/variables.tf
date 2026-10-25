variable "env" {
  type        = string
  description = "Environment name (staging | production)"
}

variable "region" {
  type    = string
  default = "eu-north-1" # Stockholm: keeps data in the EU (GDPR)
}

variable "vpc_cidr" {
  type = string
}

variable "cluster_version" {
  type    = string
  default = "1.30"
}

variable "node_instance_types" {
  type    = list(string)
  default = ["t3.large"]
}

variable "node_min" {
  type = number
}

variable "node_max" {
  type = number
}

variable "github_repo" {
  type        = string
  description = "owner/repo allowed to assume the CI deploy role via OIDC"
}
