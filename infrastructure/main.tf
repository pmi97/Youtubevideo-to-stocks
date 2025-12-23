terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "youtube-agent"
}

variable "environment" {
  description = "Environment (dev/prod)"
  type        = string
  default     = "prod"
}

variable "alert_email" {
  description = "Email address for billing alerts"
  type        = string
}

locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

output "aws_region" {
  value = var.aws_region
}
