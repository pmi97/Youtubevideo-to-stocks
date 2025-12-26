resource "aws_dynamodb_table" "youtube_video_analysis" {
  name         = "youtube_video_analysis"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "video_id"

  attribute {
    name = "video_id"
    type = "S"
  }

  tags = local.common_tags
}

resource "aws_dynamodb_table" "youtube_subscribers" {
  name         = "youtube_subscribers"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "email"

  attribute {
    name = "email"
    type = "S"
  }

  tags = local.common_tags
}

resource "aws_dynamodb_table" "youtube_subscriptions" {
  name         = "youtube_subscriptions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "channel_id"
  range_key    = "email"

  attribute {
    name = "channel_id"
    type = "S"
  }

  attribute {
    name = "email"
    type = "S"
  }

  tags = local.common_tags
}

resource "aws_dynamodb_table" "youtube_processed_videos" {
  name         = "youtube_processed_videos"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "video_id"

  attribute {
    name = "video_id"
    type = "S"
  }

  tags = local.common_tags
}

resource "aws_dynamodb_table" "youtube_pending_videos" {
  name         = "youtube_pending_videos"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "video_id"

  attribute {
    name = "video_id"
    type = "S"
  }

  tags = local.common_tags
}
