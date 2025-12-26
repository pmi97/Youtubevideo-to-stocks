resource "aws_ecr_repository" "backend" {
  name                 = "${var.project_name}-backend"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.common_tags
}

resource "aws_lambda_function" "backend" {
  function_name = "${var.project_name}-backend"
  role          = aws_iam_role.lambda_exec.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.backend.repository_url}:latest"
  
  # Security: Limit concurrency to prevent runaway costs during an attack
  # reserved_concurrent_executions = 5
  
  timeout     = 300 # 5 minutes (matches our previous Nginx timeout)
  memory_size = 512 # Adjust based on Python needs

  environment {
    variables = {
      ENVIRONMENT           = var.environment
      DYNAMODB_ENDPOINT     = "" # Empty for production (uses AWS default)
      DYNAMODB_TABLE_PREFIX = "youtube_"
      # Other secrets like GEMINI_API_KEY should be added manually in AWS Console or Secrets Manager
    }
  }

  tags = local.common_tags
}

resource "aws_lambda_function_url" "backend_url" {
  function_name      = aws_lambda_function.backend.function_name
  authorization_type = "NONE"

  cors {
    allow_credentials = true
    allow_origins     = ["https://${aws_cloudfront_distribution.frontend.domain_name}"]
    allow_methods     = ["*"]
    allow_headers     = ["*"]
    expose_headers    = ["keep-alive", "date"]
    max_age           = 86400
  }
}

output "backend_url" {
  value = aws_lambda_function_url.backend_url.function_url
}

output "ecr_repository_url" {
  value = aws_ecr_repository.backend.repository_url
}
