resource "aws_budgets_budget" "monthly_budget" {
  name              = "${var.project_name}-monthly-budget"
  budget_type       = "COST"
  limit_amount      = "10"
  limit_unit        = "USD"
  time_period_start = "2024-01-01_00:00"
  time_unit         = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 50
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }
}

# --- KILL SWITCH MECHANISM ---

# 1. The "Deny All" Policy
resource "aws_iam_policy" "kill_switch_policy" {
  name        = "${var.project_name}-kill-switch"
  description = "Policy to disable all actions for the backend"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action   = "*"
      Effect   = "Deny"
      Resource = "*"
    }]
  })
}

# 2. IAM Role for Budgets to perform the action
resource "aws_iam_role" "budget_action_role" {
  name = "${var.project_name}-budget-action-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "budgets.amazonaws.com"
      }
    }]
  })
}

# Minimal policy for Budget Action to attach the kill-switch policy
resource "aws_iam_role_policy" "budget_action_attach_policy" {
  name = "${var.project_name}-budget-attach-policy"
  role = aws_iam_role.budget_action_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "iam:AttachRolePolicy",
          "iam:DetachRolePolicy"
        ]
        Resource = aws_iam_role.lambda_exec.arn
        Condition = {
          ArnEquals = {
            "iam:PolicyARN" = aws_iam_policy.kill_switch_policy.arn
          }
        }
      }
    ]
  })
}

# 3. The Actual Kill-Switch Action
resource "aws_budgets_budget_action" "kill_backend" {
  budget_name        = aws_budgets_budget.monthly_budget.name
  action_type        = "APPLY_IAM_POLICY"
  approval_model     = "AUTOMATIC"
  action_threshold {
    action_threshold_type  = "PERCENTAGE"
    action_threshold_value = 100
  }

  definition {
    iam_action_definition {
      policy_arn = aws_iam_policy.kill_switch_policy.arn
      roles      = [aws_iam_role.lambda_exec.name]
    }
  }

  execution_role_arn = aws_iam_role.budget_action_role.arn
  notification_type  = "ACTUAL"
  subscriber_email_addresses = [var.alert_email]
}
