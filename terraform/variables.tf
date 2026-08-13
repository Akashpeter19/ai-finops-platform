variable "aws_region" {
  description = "AWS region for all resources"
  default     = "us-east-1"
}

variable "project_name" {
  description = "Prefix for all resource names"
  default     = "ai-finops"
}

variable "environment" {
  description = "Environment name"
  default     = "dev"
}

variable "aws_profile" {
  description = "AWS CLI profile — leave empty in CI, use finops locally"
  default     = ""
}
