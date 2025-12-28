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

# Sensitive variables for Lambda environment
variable "gemini_api_key" {
  description = "Gemini API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "youtube_api_key" {
  description = "YouTube Data API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "smtp_host" {
  description = "SMTP server hostname"
  type        = string
  default     = "smtp.gmail.com"
}

variable "smtp_port" {
  description = "SMTP server port"
  type        = string
  default     = "587"
}

variable "smtp_user" {
  description = "SMTP username (email)"
  type        = string
  default     = ""
}

variable "smtp_pass" {
  description = "SMTP password (app password)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "from_email" {
  description = "From email address for notifications"
  type        = string
  default     = ""
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
