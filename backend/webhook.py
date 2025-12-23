"""
YouTube PubSubHubbub Webhook Handler
Handles real-time notifications for new video uploads
"""
import os
import logging
import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional
import httpx

from database import db
from handlers import YouTubeHandler, GeminiAnalyzer, EmailService

logger = logging.getLogger(__name__)

# PubSubHubbub hub URL
PUBSUB_HUB_URL = "https://pubsubhubbub.appspot.com/subscribe"

# Backend URL for webhook callback (must be publicly accessible)
WEBHOOK_CALLBACK_URL = os.getenv("WEBHOOK_CALLBACK_URL", "http://localhost:8001/api/webhook/youtube")


class WebhookHandler:
    """Handle YouTube PubSubHubbub webhooks"""
    
    def __init__(self):
        self.youtube = YouTubeHandler()
        self.gemini = GeminiAnalyzer()
        self.email_service = EmailService()
    
    async def subscribe_to_channel(self, channel_id: str) -> bool:
        """Subscribe to PubSubHubbub notifications for a channel"""
        topic_url = f"https://www.youtube.com/xml/feeds/videos.xml?channel_id={channel_id}"
        
        data = {
            "hub.mode": "subscribe",
            "hub.topic": topic_url,
            "hub.callback": WEBHOOK_CALLBACK_URL,
            "hub.verify": "async",
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(PUBSUB_HUB_URL, data=data)
                if resp.status_code in [202, 204]:
                    logger.info(f"Subscription request sent for channel {channel_id}")
                    return True
                else:
                    logger.error(f"PubSubHubbub subscription failed: {resp.status_code} - {resp.text}")
                    return False
        except Exception as e:
            logger.error(f"Failed to subscribe to channel {channel_id}: {e}")
            return False
    
    async def unsubscribe_from_channel(self, channel_id: str) -> bool:
        """Unsubscribe from PubSubHubbub notifications for a channel"""
        topic_url = f"https://www.youtube.com/xml/feeds/videos.xml?channel_id={channel_id}"
        
        data = {
            "hub.mode": "unsubscribe",
            "hub.topic": topic_url,
            "hub.callback": WEBHOOK_CALLBACK_URL,
            "hub.verify": "async",
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(PUBSUB_HUB_URL, data=data)
                return resp.status_code in [202, 204]
        except Exception as e:
            logger.error(f"Failed to unsubscribe from channel {channel_id}: {e}")
            return False
    
    def verify_callback(self, hub_challenge: str) -> str:
        """Handle PubSubHubbub verification callback"""
        return hub_challenge
    
    async def handle_notification(self, body: bytes) -> None:
        """Handle incoming PubSubHubbub notification"""
        try:
            # Parse Atom feed notification
            root = ET.fromstring(body)
            
            # Define namespaces
            ns = {
                "atom": "http://www.w3.org/2005/Atom",
                "yt": "http://www.youtube.com/xml/schemas/2015",
            }
            
            # Extract video info from entry
            entry = root.find("atom:entry", ns)
            if entry is None:
                logger.warning("No entry found in notification")
                return
            
            video_id = entry.find("yt:videoId", ns)
            channel_id = entry.find("yt:channelId", ns)
            title = entry.find("atom:title", ns)
            
            if video_id is None or channel_id is None:
                logger.warning("Missing video_id or channel_id in notification")
                return
            
            video_id_text = video_id.text
            channel_id_text = channel_id.text
            title_text = title.text if title is not None else "Unknown"
            
            logger.info(f"Received notification for video {video_id_text} from channel {channel_id_text}")
            
            # Check if already processed
            if await db.is_video_processed(video_id_text):
                logger.info(f"Video {video_id_text} already processed, skipping")
                return
            
            # Add to pending queue for transcript check
            await db.add_pending_video(video_id_text, channel_id_text, title_text)
            logger.info(f"Added video {video_id_text} to pending queue")
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse notification XML: {e}")
        except Exception as e:
            logger.error(f"Error handling notification: {e}")
    
    async def process_pending_videos(self) -> None:
        """Process pending videos that might have transcripts available"""
        pending = await db.get_pending_videos()
        
        for video in pending:
            video_id = video["video_id"]
            channel_id = video["channel_id"]
            video_title = video.get("video_title", "Unknown")
            retry_count = video.get("retry_count", 0)
            
            logger.info(f"Checking transcript for video {video_id} (attempt {retry_count + 1})")
            
            try:
                # Try to get transcript
                transcript = await self.youtube.get_captions(video_id)
                
                if transcript:
                    logger.info(f"Transcript found for video {video_id}")
                    
                    # Get subscribers for this channel
                    subscribers = await db.get_subscribers_for_channel(channel_id)
                    
                    if not subscribers:
                        logger.info(f"No subscribers for channel {channel_id}")
                        await db.remove_pending_video(video_id)
                        await db.mark_video_processed(video_id, channel_id)
                        continue
                    
                    # Process for each subscriber's language preference
                    for subscriber in subscribers:
                        email = subscriber["email"]
                        language = subscriber.get("language", "en")
                        
                        try:
                            # Analyze with Gemini
                            companies = await self.gemini.analyze_companies(transcript, language)
                            
                            # Send email
                            await self.email_service.send_report(
                                recipient=email,
                                video_title=video_title,
                                companies=companies,
                                language=language,
                                video_id=video_id,
                            )
                            logger.info(f"Sent analysis email to {email}")
                            
                        except Exception as e:
                            logger.error(f"Failed to process for subscriber {email}: {e}")
                    
                    # Mark as processed and remove from pending
                    await db.remove_pending_video(video_id)
                    await db.mark_video_processed(video_id, channel_id)
                    
                else:
                    # No transcript yet, update retry count
                    await db.update_pending_video_retry(video_id, retry_count)
                    logger.info(f"No transcript for video {video_id}, scheduled for retry")
                    
            except Exception as e:
                logger.error(f"Error processing video {video_id}: {e}")
                await db.update_pending_video_retry(video_id, retry_count)


# Singleton instance
webhook_handler = WebhookHandler()


async def start_pending_video_processor() -> None:
    """Background task to periodically check pending videos"""
    logger.info("Starting pending video processor")
    
    while True:
        try:
            await webhook_handler.process_pending_videos()
        except Exception as e:
            logger.error(f"Error in pending video processor: {e}")
        
        # Check every 5 minutes
        await asyncio.sleep(300)
