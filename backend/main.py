"""
Investment Streamer Analyzer - FastAPI Backend
Production-ready application for analyzing YouTube investment channels
"""
import os
import logging
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, EmailStr, field_validator
import uvicorn
from dotenv import load_dotenv

# Load environment variables from secrets directory (parent of workspace)
secrets_path = os.path.join(os.path.dirname(__file__), "..", "..", "secrets", "Youtube-agent", ".env")
load_dotenv(dotenv_path=secrets_path)

# Import handlers
import sys
sys.path.insert(0, os.path.dirname(__file__))
from handlers import YouTubeHandler, GeminiAnalyzer, EmailService
from database import db
from webhook import webhook_handler, start_pending_video_processor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting application...")
    await db.connect()
    
    # Start background task for processing pending videos
    asyncio.create_task(start_pending_video_processor())
    logger.info("Background video processor started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    await db.close()


# Initialize FastAPI
app = FastAPI(
    title="Investment Streamer Analyzer",
    description="Analyze YouTube investment channels and extract company mentions",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== Input Sanitization ==============

import re
import html

# Security patterns
YOUTUBE_VIDEO_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{11}$')
YOUTUBE_CHANNEL_PATTERN = re.compile(r'^@?[a-zA-Z0-9_.-]{1,100}$')
YOUTUBE_URL_PATTERN = re.compile(
    r'^https?://(www\.)?(youtube\.com|youtu\.be)/'
)

# Maximum lengths
MAX_CHANNEL_URL_LENGTH = 200
MAX_VIDEO_URL_LENGTH = 300
MAX_EMAIL_LENGTH = 254

def sanitize_text(text: str, max_length: int = 500) -> str:
    """Sanitize text input to prevent XSS and injection attacks"""
    if not text:
        return ""
    # Truncate to max length
    text = text[:max_length]
    # HTML escape
    text = html.escape(text)
    # Remove any control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    return text.strip()

def validate_youtube_url(url: str) -> str:
    """Validate and sanitize YouTube URL or channel identifier"""
    url = url.strip()
    
    if len(url) > MAX_CHANNEL_URL_LENGTH:
        raise ValueError(f"URL too long (max {MAX_CHANNEL_URL_LENGTH} characters)")
    
    # Allow @username format
    if url.startswith('@'):
        if not YOUTUBE_CHANNEL_PATTERN.match(url):
            raise ValueError("Invalid channel name format")
        return sanitize_text(url, MAX_CHANNEL_URL_LENGTH)
    
    # Allow full URLs
    if url.startswith('http'):
        if not YOUTUBE_URL_PATTERN.match(url):
            raise ValueError("Invalid YouTube URL")
        return sanitize_text(url, MAX_CHANNEL_URL_LENGTH)
    
    # Allow channel usernames without @
    if YOUTUBE_CHANNEL_PATTERN.match(url):
        return sanitize_text(url, MAX_CHANNEL_URL_LENGTH)
    
    raise ValueError("Invalid channel URL or username format")

def validate_video_url(url: str) -> str:
    """Validate and sanitize video URL or ID"""
    url = url.strip()
    
    if len(url) > MAX_VIDEO_URL_LENGTH:
        raise ValueError(f"URL too long (max {MAX_VIDEO_URL_LENGTH} characters)")
    
    # Direct video ID (11 characters)
    if len(url) == 11 and YOUTUBE_VIDEO_ID_PATTERN.match(url):
        return url
    
    # Full URL
    if url.startswith('http'):
        if not YOUTUBE_URL_PATTERN.match(url):
            raise ValueError("Invalid YouTube URL")
        return sanitize_text(url, MAX_VIDEO_URL_LENGTH)
    
    raise ValueError("Invalid video URL or ID format")


# ============== Pydantic Models ==============

class Channel(BaseModel):
    url: str
    
    @field_validator("url")
    def validate_url(cls, v):
        if not v:
            raise ValueError("Channel URL cannot be empty")
        return validate_youtube_url(v)


class SubscriptionRequest(BaseModel):
    email: EmailStr
    language: str = "en"
    channels: List[Channel]
    
    @field_validator("language")
    def validate_language(cls, v):
        if v not in ["en", "es", "sv"]:
            raise ValueError("Language must be 'en', 'es', or 'sv'")
        return v
    
    @field_validator("channels")
    def validate_channels_count(cls, v):
        if len(v) > 20:
            raise ValueError("Maximum 20 channels allowed")
        if len(v) == 0:
            raise ValueError("At least one channel required")
        return v


class CheckVideoRequest(BaseModel):
    channels: List[Channel]
    language: str = "en"
    
    @field_validator("language")
    def validate_language(cls, v):
        if v not in ["en", "es", "sv"]:
            raise ValueError("Language must be 'en', 'es', or 'sv'")
        return v


class AnalyzeVideoRequest(BaseModel):
    """Request to analyze a single video"""
    video_url: str
    email: Optional[EmailStr] = None
    language: str = "en"
    
    @field_validator("video_url")
    def validate_video_url(cls, v):
        if not v:
            raise ValueError("Video URL cannot be empty")
        return validate_video_url(v)
    
    @field_validator("language")
    def validate_language(cls, v):
        if v not in ["en", "es", "sv"]:
            raise ValueError("Language must be 'en', 'es', or 'sv'")
        return v


class Company(BaseModel):
    name: str
    description: str
    sentiment: str  # positive, negative, neutral


class VideoAnalysis(BaseModel):
    video_id: str
    video_title: str
    channel_name: str
    published_at: str
    companies: List[Company]


class HealthCheckResponse(BaseModel):
    status: str
    has_youtube_key: bool
    has_gemini_key: bool
    has_email_config: bool
    has_database: bool


# Initialize handlers
youtube_handler = YouTubeHandler()
gemini_analyzer = GeminiAnalyzer()
email_service = EmailService()


# ============== Health Check ==============

@app.get("/api/health", response_model=HealthCheckResponse)
async def health_check():
    """Check API health and configuration status"""
    db_connected = db.pool is not None
    return HealthCheckResponse(
        status="healthy" if db_connected else "degraded",
        has_youtube_key=bool(os.getenv("YOUTUBE_API_KEY")),
        has_gemini_key=bool(os.getenv("GEMINI_API_KEY")),
        has_email_config=bool(os.getenv("FROM_EMAIL")) and bool(os.getenv("SMTP_PASS")),
        has_database=db_connected,
    )


# ============== Subscription Endpoints ==============

@app.post("/api/subscribe")
async def subscribe(request: SubscriptionRequest, background_tasks: BackgroundTasks):
    """Subscribe to channel notifications"""
    try:
        # Add subscriber
        subscriber_id = await db.add_subscriber(request.email, request.language)
        
        subscribed_channels = []
        for channel in request.channels:
            try:
                # Resolve channel URL to ID
                channel_id = await youtube_handler.resolve_channel_url(channel.url)
                
                # Add subscription
                await db.add_subscription(subscriber_id, channel.url, channel_id, email=request.email)
                
                # Subscribe to PubSubHubbub in background
                background_tasks.add_task(webhook_handler.subscribe_to_channel, channel_id)
                
                subscribed_channels.append({
                    "url": channel.url,
                    "channel_id": channel_id,
                })
                
            except Exception as e:
                logger.error(f"Failed to process channel {channel.url}: {e}")
                subscribed_channels.append({
                    "url": channel.url,
                    "error": str(e),
                })
        
        return {
            "status": "ok",
            "email": request.email,
            "language": request.language,
            "channels": subscribed_channels,
            "message": "Subscription created successfully. You will receive emails when new videos are analyzed.",
        }
        
    except Exception as e:
        logger.error(f"Subscription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/subscriptions/{email}")
async def get_subscriptions(email: EmailStr):
    """Get all subscriptions for an email"""
    try:
        subscriber = await db.get_subscriber(email)
        if not subscriber:
            raise HTTPException(status_code=404, detail="Subscriber not found")
        
        subscriptions = await db.get_subscriptions(email)
        
        return {
            "email": email,
            "language": subscriber["language"],
            "subscriptions": subscriptions,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get subscriptions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/unsubscribe/{email}")
async def unsubscribe(email: EmailStr):
    """Unsubscribe from all notifications"""
    try:
        deleted = await db.delete_subscriber(email)
        if not deleted:
            raise HTTPException(status_code=404, detail="Subscriber not found")
        
        return {
            "status": "ok",
            "message": f"Successfully unsubscribed {email}",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unsubscribe failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== YouTube Webhook Endpoints ==============

@app.get("/api/webhook/youtube")
async def webhook_verification(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_topic: Optional[str] = Query(None, alias="hub.topic"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    hub_lease_seconds: Optional[int] = Query(None, alias="hub.lease_seconds"),
):
    """Handle PubSubHubbub verification"""
    if hub_mode == "subscribe" and hub_challenge:
        logger.info(f"PubSubHubbub verification for topic: {hub_topic}")
        return PlainTextResponse(content=hub_challenge)
    
    return PlainTextResponse(content="OK")


@app.post("/api/webhook/youtube")
async def webhook_notification(request: Request, background_tasks: BackgroundTasks):
    """Handle PubSubHubbub notification for new videos"""
    try:
        body = await request.body()
        logger.info(f"Received webhook notification: {len(body)} bytes")
        
        # Process notification in background
        background_tasks.add_task(webhook_handler.handle_notification, body)
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Webhook notification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== Manual Video Analysis ==============

@app.post("/api/check-videos")
async def check_videos(request: CheckVideoRequest, background_tasks: BackgroundTasks):
    """Trigger video check and analysis for all channels"""
    try:
        results = []
        
        for channel in request.channels:
            try:
                # Get channel ID from URL/username
                channel_id = await youtube_handler.resolve_channel_url(channel.url)
                
                # Get latest video
                video_data = await youtube_handler.get_latest_video(channel_id)
                if not video_data:
                    continue
                
                # Get captions/transcript
                transcript = await youtube_handler.get_captions(video_data["video_id"])
                if not transcript:
                    continue
                
                # Analyze with Gemini
                companies = await gemini_analyzer.analyze_companies(transcript, request.language)
                
                # Create analysis result
                analysis = VideoAnalysis(
                    video_id=video_data["video_id"],
                    video_title=video_data["title"],
                    channel_name=video_data["channel_name"],
                    published_at=video_data["published_at"],
                    companies=companies,
                )
                results.append(analysis.model_dump())
                
            except Exception as e:
                logger.error(f"Error processing channel {channel.url}: {e}")
                continue
        
        return {
            "status": "ok",
            "results": results,
            "timestamp": datetime.now().isoformat(),
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# ============== Single Video Analysis ==============

@app.post("/api/analyze-video")
async def analyze_video(request: AnalyzeVideoRequest, background_tasks: BackgroundTasks):
    """Analyze a single YouTube video and extract companies"""
    import re
    
    try:
        # Extract video ID from URL
        video_id = None
        patterns = [
            r'(?:v=|/)([0-9A-Za-z_-]{11})(?:[&?]|$)',  # Standard and shortened URLs
            r'youtu\.be/([0-9A-Za-z_-]{11})',  # youtu.be URLs
            r'embed/([0-9A-Za-z_-]{11})',  # Embed URLs
        ]
        
        for pattern in patterns:
            match = re.search(pattern, request.video_url)
            if match:
                video_id = match.group(1)
                break
        
        if not video_id:
            # Maybe it's just the video ID directly
            if len(request.video_url) == 11 and re.match(r'^[0-9A-Za-z_-]+$', request.video_url):
                video_id = request.video_url
            else:
                raise HTTPException(status_code=400, detail="Could not extract video ID from URL")
        
        # Check cache first
        analysis = await db.get_video_analysis(video_id)
        is_cached = False
        if analysis:
            logger.info(f"Cache hit for video {video_id}")
            is_cached = True
        else:
            logger.info(f"Cache miss for video {video_id}, analyzing...")
            # Get transcript
            transcript = await youtube_handler.get_captions(video_id, request.language)
            if not transcript:
                raise HTTPException(status_code=404, detail="No transcript available for this video")
            
            # Analyze with Gemini (returns dict with companies, watchlist, summary)
            analysis = await gemini_analyzer.analyze_companies(transcript, request.language)
            
            # Save to cache
            if analysis.get("companies") or analysis.get("watchlist") or analysis.get("summary"):
                await db.save_video_analysis(video_id, analysis)
        
        # Optionally send email
        if request.email and (analysis.get("companies") or analysis.get("watchlist")):
            background_tasks.add_task(
                email_service.send_report,
                request.email,
                f"Video Analysis: {video_id}",
                analysis,
                request.language,
                video_id,
            )
        
        return {
            "status": "ok",
            "video_id": video_id,
            "video_url": f"https://www.youtube.com/watch?v={video_id}",
            "companies": analysis.get("companies", []),
            "watchlist": analysis.get("watchlist", []),
            "summary": analysis.get("summary", ""),
            "email_sent": bool(request.email),
            "model": analysis.get("model", "unknown"),
            "cached": is_cached,
            "timestamp": datetime.now().isoformat(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# ============== Root Endpoint ==============

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Investment Streamer Analyzer API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/health",
        "endpoints": {
            "subscribe": "POST /api/subscribe",
            "unsubscribe": "DELETE /api/unsubscribe/{email}",
            "get_subscriptions": "GET /api/subscriptions/{email}",
            "webhook": "POST /api/webhook/youtube",
        },
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8001)),
        reload=os.getenv("ENV", "development") == "development",
    )

