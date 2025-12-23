"""
Core handler classes for YouTube, Gemini AI, and Email services
"""
import os
import logging
import asyncio
from typing import List, Optional, Dict, Any
import re
import httpx
from datetime import datetime

from litellm import acompletion
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class YouTubeHandler:
    """Handle YouTube API operations"""
    
    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY")
        if not self.api_key:
            logger.warning("YOUTUBE_API_KEY not configured")
    
    async def resolve_channel_url(self, url_or_name: str) -> str:
        """Resolve YouTube channel URL or username to channel ID"""
        # If it already looks like a channel ID (starts with UC), return it
        if url_or_name.startswith("UC"):
            return url_or_name
        
        # Extract username from URL or use directly
        name = url_or_name.strip().lstrip("@")
        
        # If no API key, raise error
        if not self.api_key:
            raise ValueError("YouTube API key not configured")
        
        # Call YouTube API to search for channel
        async with httpx.AsyncClient(timeout=30.0) as client:
            params = {
                "q": name,
                "part": "snippet",
                "type": "channel",
                "maxResults": 1,
                "key": self.api_key,
            }
            resp = await client.get(
                "https://www.googleapis.com/youtube/v3/search",
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()
            
            items = data.get("items", [])
            if not items:
                raise ValueError(f"Channel '{url_or_name}' not found")
            
            return items[0]["snippet"]["channelId"]
    
    async def get_latest_video(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """Get latest video from a channel"""
        if not self.api_key:
            raise ValueError("YouTube API key not configured")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            params = {
                "channelId": channel_id,
                "part": "snippet",
                "order": "date",
                "maxResults": 1,
                "type": "video",
                "key": self.api_key,
            }
            resp = await client.get(
                "https://www.googleapis.com/youtube/v3/search",
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()
            
            items = data.get("items", [])
            if not items:
                logger.info(f"No videos found for channel {channel_id}")
                return None
            
            snippet = items[0]["snippet"]
            return {
                "video_id": items[0]["id"]["videoId"],
                "title": snippet["title"],
                "channel_name": snippet["channelTitle"],
                "published_at": snippet["publishedAt"],
                "description": snippet.get("description", ""),
            }
    
    async def get_captions(self, video_id: str, language: str = "en") -> Optional[str]:
        """Get transcript/captions for a video with timestamps"""
        try:
            # New youtube-transcript-api v1.x uses instance methods
            ytt_api = YouTubeTranscriptApi()
            
            # Try to fetch transcript with language preferences
            try:
                languages_to_try = [language]
                if language != "en":
                    languages_to_try.append("en")
                languages_to_try.extend([f"{language}-auto", "en-auto"])
                
                transcript_data = ytt_api.fetch(video_id, languages=languages_to_try)
            except Exception:
                logger.info(f"Trying to fetch any available transcript for {video_id}")
                transcript_data = ytt_api.fetch(video_id)
            
            # Build transcript WITH timestamps for better context
            entries = []
            for entry in transcript_data:
                # Convert seconds to MM:SS format
                start_seconds = int(entry.start)
                minutes = start_seconds // 60
                seconds = start_seconds % 60
                timestamp = f"[{minutes:02d}:{seconds:02d}]"
                entries.append(f"{timestamp} {entry.text}")
            
            full_text = "\n".join(entries)
            return full_text
        except TranscriptsDisabled:
            logger.warning(f"Transcripts disabled for video {video_id}")
            return None
        except NoTranscriptFound:
            logger.warning(f"No transcript found for video {video_id}")
            return None
        except Exception as e:
            logger.error(f"Error fetching transcript for {video_id}: {e}")
            return None


class GeminiAnalyzer:
    """Handle Gemini AI analysis"""
    
    SYSTEM_PROMPT = """You are a professional investment analyst assistant. Your task is to analyze video transcripts and extract all investment-related mentions.

## Instructions
1. **Language of Output**: You MUST respond with the description, context, and summary in {language_name}.
2. **Verify Company Details**: Before outputting any company, verify its full legal name and the primary stock ticker symbol.
3. **Extract individual COMPANIES mentioned**
   - **EXCLUDE** broad market indices (S&P 500, Nasdaq, Dow Jones)
   - **EXCLUDE** generic funds or ETFs unless a specific ticker/product is analyzed in depth
3. **Identify any stocks the presenter adds to their watchlist** - look for phrases like the ones listed below or similar expressions:
   - English: "I'm saving this", "adding to my watchlist", "one to watch", "I'll keep an eye on"
   - Spanish: "me la guardo", "la voy a seguir", "la tengo en el radar", "la apunto"
   - Other languages: similar expressions indicating interest in tracking a stock
4. **Provide the timestamp** where each mention occurs (use the [MM:SS] format from the transcript)

## Output Format
Return ONLY a valid JSON object.
{{
  "companies": [
    {{
      "name": "Company Name",
      "ticker": "TICKER",
      "description": "Description",
      "sentiment": "positive|negative|neutral",
      "timestamp": "MM:SS",
      "context": "Context"
    }}
  ],
  "watchlist": [
    {{
      "name": "Company Name",
      "ticker": "TICKER",
      "reason": "Why the presenter is adding this to their watchlist",
      "timestamp": "MM:SS"
    }}
  ],
  "summary": "Summary"
}}

## Sentiment Guidelines
- **positive**: Buy/Bullish
- **negative**: Sell/Bearish
- **neutral**: Informational

**CRITICAL**: ensure all double quotes inside strings are escaped (e.g. \\"text\\"). Return ONLY the JSON."""
    
    # Ordered models from highest to lowest performance
    # based on user availability and benchmarks
    MODELS_ORDER = [
        "gemini/gemini-flash-latest",
        "gemini/gemini-flash-lite-latest",
        "gemini/gemini-2.5-flash",
        "gemini/gemini-2.5-flash-lite",
        "gemini/gemma-3-27b",
        "gemini/gemma-3-12b",
        "gemini/gemma-3-4b",
        "gemini/gemma-3-2b",
        "gemini/gemma-3-1b",
        "gemini/gemini-robotics-er-1.5-preview",
        "gemini/gemini-2.5-flash-tts",
        "gemini/gemini-2.5-flash-native-audio-dialog"
    ]
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.default_model = os.getenv("LLM_MODEL", self.MODELS_ORDER[0])
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not configured")
    
    async def analyze_companies(self, transcript: str, language: str = "en") -> Dict[str, Any]:
        """Analyze transcript and extract companies mentioned with timestamps"""
        if not self.api_key:
            raise ValueError("Gemini API key not configured")
        
        # Sanitize transcript to prevent prompt injection
        transcript = re.sub(r'(?i)(ignore|forget|disregard)\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?|context)', '[REMOVED]', transcript)
        transcript = re.sub(r'(?i)you\s+are\s+(now|a|an)\s+', '', transcript)
        transcript = re.sub(r'(?i)(system|assistant|user)\s*:', '', transcript)
        
        # Determine retry models list starting from default if specified, else use full list
        try_models = self.MODELS_ORDER.copy()
        if self.default_model in try_models:
            # Reorder to start with default_model
            idx = try_models.index(self.default_model)
            try_models = try_models[idx:] + try_models[:idx]

        # Get human-readable language name
        language_map = {"en": "English", "es": "Spanish", "sv": "Swedish"}
        language_name = language_map.get(language, "English")
        
        system_prompt = self.SYSTEM_PROMPT.format(language_name=language_name)

        last_error = None
        for model in try_models:
            try:
                logger.info(f"Attempting analysis with model: {model}")
                response = await acompletion(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": transcript}
                    ],
                    api_key=self.api_key,
                    temperature=0.2,
                    max_tokens=15000,
                    response_format={"type": "json_object"},  # Force valid JSON output
                )
                
                raw_content = response.choices[0].message.content
                if not raw_content:
                    logger.warning(f"Empty response from {model}")
                    continue
                
                # Successful response!
                result = self._process_response(raw_content)
                if not result.get("companies") and not result.get("watchlist") and not result.get("summary"):
                    logger.warning(f"Model {model} returned an empty or unparsable result. Retrying next.")
                    continue
                
                result["model"] = model.split("/")[-1]
                return result
                
            except Exception as e:
                error_msg = str(e).lower()
                # Check for rate limits, quota issues, or "not found" errors
                is_retryable = any(term in error_msg for term in [
                    "rate limit", "429", "quota", "exhausted", "limit exceeded",
                    "not found", "404", "not supported"
                ])
                
                if is_retryable:
                    logger.warning(f"Model {model} failed or is unavailable. Skipping. Error: {e}")
                    last_error = e
                    continue # Try next model
                else:
                    logger.error(f"Gemini analysis failed on {model} with critical error: {e}")
                    last_error = e
                    continue # Still try next model just in case it's model-specific
        
        logger.error(f"All models exhausted. Last error: {last_error}")
        return {"companies": [], "watchlist": [], "summary": ""}

    def _process_response(self, raw_content: str) -> Dict[str, Any]:
        """Process raw LLM response into structured JSON"""
        content = raw_content.strip()
        
        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = re.sub(r'^```(?:json)?\s*\n?', '', content)
            content = re.sub(r'\n?```\s*$', '', content)
        
        # Parse JSON
        import json
        try:
            result = json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"Initial JSON parse failed: {e}. Attempting cleanup.")
            
            # Attempt to clean common JSON errors explicitly
            cleaned_content = self._clean_json_string(content)
            try:
                result = json.loads(cleaned_content)
                logger.info("JSON parsed successfully after cleanup")
            except json.JSONDecodeError as e2:
                logger.warning(f"Cleanup failed: {e2}. Attempting regex extraction.")
                # Last resort: Try explicit regex extraction
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                        logger.info("JSON parsed successfully via regex")
                    except json.JSONDecodeError:
                        logger.error("Failed to parse JSON even after cleanup and regex")
                        return {}
                else:
                    logger.warning(f"Could not parse JSON response")
                    return {} # Return empty to signal failure to caller
        
        # Normalize the structure
        companies = [
            {
                "name": str(c.get("name", "Unknown")),
                "ticker": str(c.get("ticker", "")),
                "description": str(c.get("description", "")),
                "sentiment": str(c.get("sentiment", "neutral")).lower(),
                "timestamp": str(c.get("timestamp", "")),
                "context": str(c.get("context", "")),
            }
            for c in result.get("companies", []) if isinstance(c, dict)
        ]

        watchlist = [
            {
                "name": str(w.get("name", "Unknown")),
                "ticker": str(w.get("ticker", "")),
                "reason": str(w.get("reason", "")),
                "timestamp": str(w.get("timestamp", "")),
            }
            for w in result.get("watchlist", []) if isinstance(w, dict)
        ]
        
        return {
            "companies": companies,
            "watchlist": watchlist,
            "summary": str(result.get("summary", ""))
        }

    def _clean_json_string(self, content: str) -> str:
        """Attempt to fix common JSON errors without external deps"""
        # Fix unescaped newlines in strings
        try:
            content = re.sub(r'(?<=: ")(.*?)(?=")', lambda m: m.group(1).replace('\n', ' '), content, flags=re.DOTALL)
            
            # Remove trailing commas
            content = re.sub(r',\s*([}\]])', r'\1', content)
        except Exception:
            pass
        
        return content



class EmailService:
    """Handle email delivery"""
    
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("FROM_EMAIL")
        self.sender_password = os.getenv("SMTP_PASS")
        
        if not all([self.sender_email, self.sender_password]):
            logger.warning("Email not configured (FROM_EMAIL or SMTP_PASS missing)")
    
    async def send_report(
        self,
        recipient: str,
        video_title: str,
        analysis: Dict[str, Any],
        language: str = "en",
        video_id: Optional[str] = None,
    ) -> None:
        """Send HTML email report with analysis"""
        if not self.sender_email or not self.sender_password:
            raise ValueError("Email service not configured")
        
        # Language-specific content
        content = {
            "en": {
                "subject": f"📊 Video Analysis: {video_title}",
                "greeting": "Hello,",
                "analysis": "Investment Analysis Report",
                "summary_heading": "Summary",
                "companies_heading": "📈 Companies Mentioned",
                "watchlist_heading": "👀 Added to Watchlist",
                "no_companies": "No companies were identified in this video.",
                "no_watchlist": "No stocks added to watchlist.",
                "sentiment": "Sentiment",
                "positive": "Bullish",
                "negative": "Bearish",
                "neutral": "Neutral",
                "at": "at",
                "reason": "Reason",
            },
            "es": {
                "subject": f"📊 Análisis: {video_title}",
                "greeting": "Hola,",
                "analysis": "Informe de Análisis de Inversión",
                "summary_heading": "Resumen",
                "companies_heading": "📈 Empresas Mencionadas",
                "watchlist_heading": "👀 Añadidas a Seguimiento",
                "no_companies": "No se identificaron empresas en este video.",
                "no_watchlist": "No se añadieron acciones a la lista de seguimiento.",
                "sentiment": "Sentimiento",
                "positive": "Alcista",
                "negative": "Bajista",
                "neutral": "Neutral",
                "at": "en",
                "reason": "Razón",
            },
            "sv": {
                "subject": f"📊 Analys: {video_title}",
                "greeting": "Hej,",
                "analysis": "Investeringsanalysrapport",
                "summary_heading": "Sammanfattning",
                "companies_heading": "📈 Nämnda Företag",
                "watchlist_heading": "👀 Lagda till Bevakningslista",
                "no_companies": "Inga företag identifierades i denna video.",
                "no_watchlist": "Inga aktier lades till bevakningslistan.",
                "sentiment": "Sentiment",
                "positive": "Hausse",
                "negative": "Baisse",
                "neutral": "Neutral",
                "at": "vid",
                "reason": "Anledning",
            },
        }
        
        text = content.get(language, content["en"])
        
        # Build HTML email
        video_url = f"https://www.youtube.com/watch?v={video_id}" if video_id else None
        model_name = analysis.get("model", "unknown")
        html_content = self._build_html_email(video_title, analysis, text, video_url, recipient, model_name)
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = text["subject"]
        message["From"] = self.sender_email
        message["To"] = recipient
        
        # Attach HTML
        message.attach(MIMEText(html_content, "html"))
        
        # Send via SMTP
        try:
            async with aiosmtplib.SMTP(hostname=self.smtp_server, port=self.smtp_port) as smtp:
                await smtp.login(self.sender_email, self.sender_password)
                await smtp.send_message(message)
            logger.info(f"Email sent to {recipient}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise
    
    def _build_html_email(
        self,
        video_title: str,
        analysis: Dict[str, Any],
        text: Dict[str, str],
        video_url: Optional[str] = None,
        recipient_email: Optional[str] = None,
        model_name: str = "unknown"
    ) -> str:
        """Build HTML email content with companies and watchlist"""
        
        # Extract data from analysis
        companies = analysis.get("companies", [])
        watchlist = analysis.get("watchlist", [])
        summary = analysis.get("summary", "")
        
        # Video link section
        video_link_html = ""
        if video_url:
            video_link_html = f'''
            <div style="margin: 20px 0; display: flex; align-items: center; gap: 12px;">
                <a href="{video_url}" style="display: inline-block; background: linear-gradient(135deg, #208296, #1a6b7a); color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600;">▶ Watch Video</a>
                <span style="background: #f8f9fa; color: #6c757d; padding: 12px 16px; border-radius: 6px; font-size: 13px; border: 1px solid #dee2e6;">🤖 AI: {model_name}</span>
            </div>
            '''
        
        # Summary section
        summary_html = ""
        if summary:
            summary_html = f'''
            <div style="background: #e8f4f8; padding: 16px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #208296;">
                <h3 style="margin: 0 0 8px 0; color: #208296;">{text.get("summary_heading", "Summary")}</h3>
                <p style="margin: 0; color: #333;">{summary}</p>
            </div>
            '''
        
        # Companies section
        companies_html = ""
        if companies:
            for company in companies:
                sentiment = company.get("sentiment", "neutral").lower()
                sentiment_colors = {
                    "positive": ("#198754", text.get("positive", "Bullish")),
                    "negative": ("#dc3545", text.get("negative", "Bearish")),
                    "neutral": ("#6c757d", text.get("neutral", "Neutral")),
                }
                color, label = sentiment_colors.get(sentiment, ("#6c757d", "Neutral"))
                
                # Build timestamp link
                timestamp = company.get("timestamp", "")
                timestamp_html = ""
                if timestamp and video_url:
                    # Convert MM:SS to seconds for YouTube URL
                    try:
                        parts = timestamp.replace("[", "").replace("]", "").split(":")
                        if len(parts) == 2:
                            seconds = int(parts[0]) * 60 + int(parts[1])
                            timestamp_html = f' <a href="{video_url}&t={seconds}s" style="color: #208296; font-size: 12px;">⏱ {timestamp}</a>'
                    except:
                        timestamp_html = f' <span style="color: #6c757d; font-size: 12px;">⏱ {timestamp}</span>'
                
                ticker_html = ""
                if company.get("ticker"):
                    ticker_html = f' <span style="background: #e9ecef; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: 600;">{company.get("ticker")}</span>'
                
                companies_html += f"""
                <div style="background: #f8f9fa; padding: 16px; margin: 12px 0; border-radius: 8px; border-left: 4px solid {color};">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <h3 style="margin: 0; color: #212529;">{company.get("name", "Unknown")}{ticker_html}</h3>
                        <span style="background: {color}; color: white; padding: 4px 10px; border-radius: 4px; font-size: 12px;">{label}</span>
                    </div>
                    <p style="margin: 0 0 8px 0; color: #495057;">{company.get("description", "")}</p>
                    {f'<p style="margin: 0; color: #6c757d; font-size: 12px; font-style: italic;">&quot;{company.get("context", "")}&quot;</p>' if company.get("context") else ""}
                    {timestamp_html}
                </div>
                """
        else:
            companies_html = f'<p style="color: #6c757d;">{text.get("no_companies", "No companies identified")}</p>'
        
        # Watchlist section
        watchlist_html = ""
        if watchlist:
            watchlist_html = f'<h2 style="color: #198754; margin-top: 32px;">{text.get("watchlist_heading", "Added to Watchlist")}</h2>'
            for item in watchlist:
                timestamp = item.get("timestamp", "")
                timestamp_html = ""
                if timestamp and video_url:
                    try:
                        parts = timestamp.replace("[", "").replace("]", "").split(":")
                        if len(parts) == 2:
                            seconds = int(parts[0]) * 60 + int(parts[1])
                            timestamp_html = f' <a href="{video_url}&t={seconds}s" style="color: #198754; font-size: 12px;">⏱ {timestamp}</a>'
                    except:
                        timestamp_html = f' <span style="color: #6c757d; font-size: 12px;">⏱ {timestamp}</span>'
                
                ticker_html = ""
                if item.get("ticker"):
                    ticker_html = f' <span style="background: #d4edda; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: 600; color: #155724;">{item.get("ticker")}</span>'
                
                watchlist_html += f"""
                <div style="background: #d4edda; padding: 16px; margin: 12px 0; border-radius: 8px; border-left: 4px solid #198754;">
                    <h3 style="margin: 0 0 8px 0; color: #155724;">⭐ {item.get("name", "Unknown")}{ticker_html}</h3>
                    <p style="margin: 0; color: #155724;"><strong>{text.get("reason", "Reason")}:</strong> {item.get("reason", "")}</p>
                    {timestamp_html}
                </div>
                """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; line-height: 1.6; color: #212529; background: #f5f5f5; }}
                .container {{ max-width: 650px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #208296, #1a6b7a); color: white; padding: 28px; border-radius: 12px 12px 0 0; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .content {{ background: white; padding: 24px; border-radius: 0 0 12px 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Investment Streamer Analyzer</h1>
                    <p style="margin: 8px 0 0 0; opacity: 0.9;">{text.get("analysis", "Investment Analysis Report")}</p>
                </div>
                <div class="content">
                    <p>{text.get("greeting", "Hello")}</p>
                    <p>Analysis for: <strong>{video_title}</strong></p>
                    {video_link_html}
                    {summary_html}
                    
                    <h2 style="color: #208296; margin-top: 24px;">{text.get("companies_heading", "Companies Mentioned")}</h2>
                    {companies_html}
                    
                    {watchlist_html}
                    
                    <p style="margin-top: 32px; padding-top: 16px; border-top: 1px solid #dee2e6; color: #6c757d; font-size: 12px;">
                        Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")} • 
                        <a href="#" style="color: #6c757d;">Unsubscribe</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

