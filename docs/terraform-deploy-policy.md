# Terraform Deploy Policy

IAM policy for the developer user to deploy this application via Terraform and deploy.sh.

## Setup

1. Go to **AWS Console → IAM → Policies → Create policy**
2. Click **JSON** tab
3. Paste the policy below
4. Name it: `TerraformDeployPolicy`
5. Attach to your developer user

## Policy

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "LambdaFullAccess",
            "Effect": "Allow",
            "Action": ["lambda:*"],
            "Resource": "*"
        },
        {
            "Sid": "ECRAccess",
            "Effect": "Allow",
            "Action": ["ecr:*"],
            "Resource": "*"
        },
        {
            "Sid": "S3Access",
            "Effect": "Allow",
            "Action": ["s3:*"],
            "Resource": "*"
        },
        {
            "Sid": "CloudFrontAccess",
            "Effect": "Allow",
            "Action": ["cloudfront:*"],
            "Resource": "*"
        },
        {
            "Sid": "DynamoDBAccess",
            "Effect": "Allow",
            "Action": ["dynamodb:*"],
            "Resource": "*"
        },
        {
            "Sid": "IAMRoleManagement",
            "Effect": "Allow",
            "Action": [
                "iam:CreateRole",
                "iam:DeleteRole",
                "iam:GetRole",
                "iam:AttachRolePolicy",
                "iam:DetachRolePolicy",
                "iam:PutRolePolicy",
                "iam:DeleteRolePolicy",
                "iam:GetRolePolicy",
                "iam:ListRolePolicies",
                "iam:ListAttachedRolePolicies",
                "iam:TagRole",
                "iam:UntagRole",
                "iam:CreatePolicy",
                "iam:DeletePolicy",
                "iam:GetPolicy",
                "iam:GetPolicyVersion",
                "iam:ListPolicyVersions",
                "iam:CreatePolicyVersion",
                "iam:DeletePolicyVersion",
                "iam:ListInstanceProfilesForRole"
            ],
            "Resource": "*"
        },
        {
            "Sid": "IAMPassRoleToLambda",
            "Effect": "Allow",
            "Action": "iam:PassRole",
            "Resource": "*",
            "Condition": {
                "StringEquals": {
                    "iam:PassedToService": "lambda.amazonaws.com"
                }
            }
        },
        {
            "Sid": "IAMPassRoleToBudgets",
            "Effect": "Allow",
            "Action": "iam:PassRole",
            "Resource": "*",
            "Condition": {
                "StringEquals": {
                    "iam:PassedToService": "budgets.amazonaws.com"
                }
            }
        },
        {
            "Sid": "BudgetsAccess",
            "Effect": "Allow",
            "Action": ["budgets:*"],
            "Resource": "*"
        },
        {
            "Sid": "CloudWatchLogs",
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:DeleteLogGroup",
                "logs:PutRetentionPolicy",
                "logs:DescribeLogGroups",
                "logs:TagResource",
                "logs:FilterLogEvents",
                "logs:GetLogEvents"
            ],
            "Resource": "*"
        },
        {
            "Sid": "STSGetCallerIdentity",
            "Effect": "Allow",
            "Action": ["sts:GetCallerIdentity"],
            "Resource": "*"
        }
    ]
}
```

## What's Included

| Permission | Purpose |
|------------|---------|
| Lambda | Create/update Lambda functions |
| ECR | Push Docker images |
| S3 | Host frontend files |
| CloudFront | CDN and cache invalidation |
| DynamoDB | Database operations |
| IAM (CreatePolicyVersion) | Update IAM policies via Terraform |
| Budgets | Cost alerts |
| CloudWatch Logs | View Lambda logs |
