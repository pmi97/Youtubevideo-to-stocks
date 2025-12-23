"""
NoSQL Database Module for YouTube Channel Subscriptions
Compatible with AWS DynamoDB (via boto3) or local DynamoDB
"""
import os
import logging
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# DynamoDB configuration
DYNAMODB_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT", None)  # http://db:8000 for docker, http://localhost:8000 for local
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
TABLE_PREFIX = os.getenv("DYNAMODB_TABLE_PREFIX", "youtube_")

# If we are running in a known local environment without an endpoint set,
# we can try to default to localhost for easier developer experience.
if not DYNAMODB_ENDPOINT and os.getenv("ENV") != "production":
    # Optional: check if something is on 8000
    pass


class DecimalEncoder(json.JSONEncoder):
    """Helper to convert Decimal to float for JSON serialization"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def decimal_to_python(obj: Any) -> Any:
    """Recursively convert Decimal to Python types"""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_python(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_python(i) for i in obj]
    return obj


class Database:
    """DynamoDB database handler for subscriptions"""
    
    def __init__(self):
        self.dynamodb = None
        self.tables = {}
    
    async def connect(self) -> None:
        """Initialize DynamoDB connection"""
        try:
            # Configure DynamoDB client
            config = {
                "region_name": AWS_REGION,
            }
            if DYNAMODB_ENDPOINT:
                config["endpoint_url"] = DYNAMODB_ENDPOINT
            
            self.dynamodb = boto3.resource("dynamodb", **config)
            logger.info(f"DynamoDB connected (endpoint: {DYNAMODB_ENDPOINT or 'AWS'})")
            await self._init_tables()
        except Exception as e:
            logger.error(f"Failed to connect to DynamoDB: {e}")
            raise
    
    async def close(self) -> None:
        """Close DynamoDB connection (no-op for boto3)"""
        logger.info("DynamoDB connection closed")
    
    async def _init_tables(self) -> None:
        """Create tables if they don't exist"""
        table_definitions = [
            {
                "name": f"{TABLE_PREFIX}subscribers",
                "key_schema": [{"AttributeName": "email", "KeyType": "HASH"}],
                "attribute_definitions": [{"AttributeName": "email", "AttributeType": "S"}],
            },
            {
                "name": f"{TABLE_PREFIX}subscriptions",
                "key_schema": [
                    {"AttributeName": "subscriber_email", "KeyType": "HASH"},
                    {"AttributeName": "channel_url", "KeyType": "RANGE"},
                ],
                "attribute_definitions": [
                    {"AttributeName": "subscriber_email", "AttributeType": "S"},
                    {"AttributeName": "channel_url", "AttributeType": "S"},
                    {"AttributeName": "channel_id", "AttributeType": "S"},
                ],
                "gsi": [
                    {
                        "IndexName": "channel_id-index",
                        "KeySchema": [{"AttributeName": "channel_id", "KeyType": "HASH"}],
                        "Projection": {"ProjectionType": "ALL"},
                    }
                ],
            },
            {
                "name": f"{TABLE_PREFIX}processed_videos",
                "key_schema": [{"AttributeName": "video_id", "KeyType": "HASH"}],
                "attribute_definitions": [{"AttributeName": "video_id", "AttributeType": "S"}],
            },
            {
                "name": f"{TABLE_PREFIX}pending_videos",
                "key_schema": [{"AttributeName": "video_id", "KeyType": "HASH"}],
                "attribute_definitions": [{"AttributeName": "video_id", "AttributeType": "S"}],
            },
            {
                "name": f"{TABLE_PREFIX}video_analysis",
                "key_schema": [{"AttributeName": "video_id", "KeyType": "HASH"}],
                "attribute_definitions": [{"AttributeName": "video_id", "AttributeType": "S"}],
            },
        ]
        
        for table_def in table_definitions:
            table_name = table_def["name"]
            try:
                table = self.dynamodb.Table(table_name)
                table.load()
                self.tables[table_name] = table
                logger.info(f"Table {table_name} already exists")
            except ClientError as e:
                if e.response["Error"]["Code"] == "ResourceNotFoundException":
                    # Create table
                    create_params = {
                        "TableName": table_name,
                        "KeySchema": table_def["key_schema"],
                        "AttributeDefinitions": table_def["attribute_definitions"],
                        "BillingMode": "PAY_PER_REQUEST",  # On-demand pricing
                    }
                    if "gsi" in table_def:
                        create_params["GlobalSecondaryIndexes"] = [
                            {
                                **gsi,
                                "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
                            } if DYNAMODB_ENDPOINT else gsi
                            for gsi in table_def["gsi"]
                        ]
                        # For local DynamoDB, we need the attribute in definitions
                        for gsi in table_def["gsi"]:
                            for key in gsi["KeySchema"]:
                                attr_name = key["AttributeName"]
                                if not any(a["AttributeName"] == attr_name for a in create_params["AttributeDefinitions"]):
                                    create_params["AttributeDefinitions"].append(
                                        {"AttributeName": attr_name, "AttributeType": "S"}
                                    )
                    
                    self.dynamodb.create_table(**create_params)
                    table = self.dynamodb.Table(table_name)
                    table.wait_until_exists()
                    self.tables[table_name] = table
                    logger.info(f"Created table {table_name}")
                else:
                    raise
    
    def _get_table(self, name: str):
        """Get table by short name"""
        return self.tables.get(f"{TABLE_PREFIX}{name}")
    
    # =========================================
    # Subscriber methods
    # =========================================
    
    async def add_subscriber(self, email: str, language: str = "en") -> int:
        """Add a new subscriber, return subscriber ID (email hash)"""
        table = self._get_table("subscribers")
        table.put_item(
            Item={
                "email": email,
                "language": language,
                "created_at": datetime.now().isoformat(),
            }
        )
        return hash(email) % 1000000  # Fake ID for compatibility
    
    async def get_subscriber(self, email: str) -> Optional[Dict[str, Any]]:
        """Get subscriber by email"""
        table = self._get_table("subscribers")
        response = table.get_item(Key={"email": email})
        item = response.get("Item")
        if item:
            return {
                "id": hash(email) % 1000000,
                "email": item["email"],
                "language": item.get("language", "en"),
                "created_at": item.get("created_at"),
            }
        return None
    
    async def delete_subscriber(self, email: str) -> bool:
        """Delete subscriber and all their subscriptions"""
        # Delete subscriber
        table = self._get_table("subscribers")
        table.delete_item(Key={"email": email})
        
        # Delete all subscriptions for this subscriber
        subs_table = self._get_table("subscriptions")
        response = subs_table.query(
            KeyConditionExpression=Key("subscriber_email").eq(email)
        )
        for item in response.get("Items", []):
            subs_table.delete_item(
                Key={"subscriber_email": email, "channel_url": item["channel_url"]}
            )
        return True
    
    # =========================================
    # Subscription methods
    # =========================================
    
    async def add_subscription(
        self,
        subscriber_id: int,
        channel_url: str,
        channel_id: Optional[str] = None,
        email: Optional[str] = None
    ) -> int:
        """Add a channel subscription for a subscriber"""
        # For DynamoDB, we need the email (not just subscriber_id)
        # This is a slight API difference - caller should provide email
        if not email:
            # Try to reverse lookup (inefficient, but maintains compatibility)
            logger.warning("add_subscription called without email, this is inefficient for DynamoDB")
            return 0
        
        table = self._get_table("subscriptions")
        item = {
            "subscriber_email": email,
            "channel_url": channel_url,
            "created_at": datetime.now().isoformat(),
        }
        if channel_id:
            item["channel_id"] = channel_id
        
        table.put_item(Item=item)
        return hash(f"{email}:{channel_url}") % 1000000
    
    async def get_subscriptions(self, email: str) -> List[Dict[str, Any]]:
        """Get all subscriptions for a subscriber"""
        table = self._get_table("subscriptions")
        response = table.query(
            KeyConditionExpression=Key("subscriber_email").eq(email)
        )
        return [
            {
                "id": hash(f"{item['subscriber_email']}:{item['channel_url']}") % 1000000,
                "channel_url": item["channel_url"],
                "channel_id": item.get("channel_id"),
                "created_at": item.get("created_at"),
            }
            for item in response.get("Items", [])
        ]
    
    async def get_subscribers_for_channel(self, channel_id: str) -> List[Dict[str, Any]]:
        """Get all subscribers following a specific channel"""
        table = self._get_table("subscriptions")
        
        try:
            response = table.query(
                IndexName="channel_id-index",
                KeyConditionExpression=Key("channel_id").eq(channel_id)
            )
        except ClientError:
            # Fallback: scan (less efficient)
            response = table.scan(
                FilterExpression=Attr("channel_id").eq(channel_id)
            )
        
        results = []
        for item in response.get("Items", []):
            email = item["subscriber_email"]
            subscriber = await self.get_subscriber(email)
            if subscriber:
                results.append(subscriber)
        return results
    
    async def update_channel_id(self, channel_url: str, channel_id: str) -> None:
        """Update channel ID for all subscriptions with this URL"""
        table = self._get_table("subscriptions")
        # Scan for items with this channel_url (inefficient but necessary for NoSQL)
        response = table.scan(
            FilterExpression=Attr("channel_url").eq(channel_url)
        )
        for item in response.get("Items", []):
            if not item.get("channel_id"):
                table.update_item(
                    Key={
                        "subscriber_email": item["subscriber_email"],
                        "channel_url": channel_url,
                    },
                    UpdateExpression="SET channel_id = :cid",
                    ExpressionAttributeValues={":cid": channel_id}
                )
    
    # =========================================
    # Processed videos methods
    # =========================================
    
    async def is_video_processed(self, video_id: str) -> bool:
        """Check if a video has already been processed"""
        table = self._get_table("processed_videos")
        response = table.get_item(Key={"video_id": video_id})
        return "Item" in response
    
    async def mark_video_processed(self, video_id: str, channel_id: str) -> None:
        """Mark a video as processed"""
        table = self._get_table("processed_videos")
        table.put_item(
            Item={
                "video_id": video_id,
                "channel_id": channel_id,
                "processed_at": datetime.now().isoformat(),
            }
        )
    
    # =========================================
    # Pending videos methods
    # =========================================
    
    async def add_pending_video(
        self,
        video_id: str,
        channel_id: str,
        video_title: Optional[str] = None
    ) -> None:
        """Add a video to the pending queue"""
        table = self._get_table("pending_videos")
        table.put_item(
            Item={
                "video_id": video_id,
                "channel_id": channel_id,
                "video_title": video_title or "",
                "retry_count": 0,
                "next_check": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat(),
            }
        )
    
    async def get_pending_videos(self) -> List[Dict[str, Any]]:
        """Get videos pending transcript check"""
        table = self._get_table("pending_videos")
        now = datetime.now().isoformat()
        
        # Scan for items ready to check (DynamoDB doesn't support < on non-key attrs in query)
        response = table.scan(
            FilterExpression=Attr("next_check").lte(now) & Attr("retry_count").lt(7)
        )
        
        items = response.get("Items", [])[:20]  # Limit to 20
        return [decimal_to_python(item) for item in items]
    
    async def update_pending_video_retry(self, video_id: str, retry_count: int) -> None:
        """Update retry count and schedule next check"""
        # Retry schedule for slow transcripts (up to ~48 hours)
        delays = [60, 240, 480, 720, 1440, 2160, 2880]
        
        if retry_count >= len(delays):
            delay_minutes = 1440
        else:
            delay_minutes = delays[retry_count]
        
        next_check = (datetime.now() + timedelta(minutes=delay_minutes)).isoformat()
        
        table = self._get_table("pending_videos")
        table.update_item(
            Key={"video_id": video_id},
            UpdateExpression="SET retry_count = :rc, next_check = :nc",
            ExpressionAttributeValues={
                ":rc": retry_count + 1,
                ":nc": next_check,
            }
        )
    
    async def remove_pending_video(self, video_id: str) -> None:
        """Remove a video from pending queue"""
        table = self._get_table("pending_videos")
        table.delete_item(Key={"video_id": video_id})
    
    async def get_all_unique_channel_ids(self) -> List[str]:
        """Get all unique channel IDs that have subscribers"""
        table = self._get_table("subscriptions")
        response = table.scan(ProjectionExpression="channel_id")
        
        channel_ids = set()
        for item in response.get("Items", []):
            if item.get("channel_id"):
                channel_ids.add(item["channel_id"])
        return list(channel_ids)
    
    # =========================================
    # Analysis Caching methods
    # =========================================
    
    async def get_video_analysis(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get cached analysis for a video"""
        table = self._get_table("video_analysis")
        response = table.get_item(Key={"video_id": video_id})
        item = response.get("Item")
        if item and item.get("analysis"):
            try:
                analysis = item["analysis"]
                if isinstance(analysis, str):
                    return json.loads(analysis)
                return decimal_to_python(analysis)
            except Exception:
                return None
        return None
    
    async def save_video_analysis(self, video_id: str, analysis: Dict[str, Any]) -> None:
        """Save analysis to cache"""
        table = self._get_table("video_analysis")
        table.put_item(
            Item={
                "video_id": video_id,
                "analysis": analysis,
                "created_at": datetime.now().isoformat(),
            }
        )


# Singleton instance
db = Database()
