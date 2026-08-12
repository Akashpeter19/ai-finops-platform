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
