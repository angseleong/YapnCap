import re
from dataclasses import dataclass
from typing import Any
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp

@dataclass
class TranscriptResult:
    title: str
    channel: str
    url: str
    duration: str
    text: str
    source: str
    language: str

def format_duration(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def extract_video_id(url: str) -> str:
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, url)
    if not match:
        raise ValueError("Invalid YouTube URL or unsupported format.")
    return match.group(1)

def get_transcript(url: str, preferred_lang: str) -> TranscriptResult:
    """Extracts metadata and CC transcript from a YouTube URL."""
    video_id = extract_video_id(url)
    
    # 1. Fetch Metadata (No download)
    ydl_opts: dict[str, Any] = {'quiet': True, 'skip_download': True, 'no_warnings': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
        info = ydl.extract_info(url, download=False)
        if not info:
            raise ValueError("Could not extract video metadata.")
            
        title = info.get('title') or 'Unknown Title'
        channel = info.get('uploader') or 'Unknown Channel'
        
        duration_val = info.get('duration')
        duration = format_duration(duration_val if duration_val is not None else 0)
        
    # 2. Fetch CC Transcript
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)  # type: ignore
        try:
            transcript = transcript_list.find_transcript([preferred_lang])
        except Exception:
            # Fallback to whatever is available if preferred lang is missing
            available = [t.language_code for t in transcript_list]
            langs = ['en', 'id'] + available
            transcript = transcript_list.find_transcript(langs)
            
        transcript_data = transcript.fetch()
        
        # Build text string (just raw text for now; timestamps will be used by engine later)
        text = "\n".join([item['text'] for item in transcript_data])
        
        source = "cc"
        language = transcript.language_code
        
    except Exception as e:
        # If CC fails, we'll return empty text for now. (Phase 3 will handle STT fallback)
        text = f"[No CC found: {str(e)}]"
        source = "none"
        language = "unknown"
        
    return TranscriptResult(
        title=title,
        channel=channel,
        url=url,
        duration=duration,
        text=text,
        source=source,
        language=language
    )
