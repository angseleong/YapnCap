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

import os
import tempfile
from yapncap.config import YapnCapConfig

def _download_audio_temp(url: str, output_dir: str) -> str:
    opts = {
        'format': 'm4a/bestaudio/best',
        'outtmpl': f'{output_dir}/%(id)s.%(ext)s',
        'quiet': True
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if not info:
            raise ValueError("Could not extract video metadata.")
        return ydl.prepare_filename(info)

def _transcribe_audio(audio_path: str, config: YapnCapConfig) -> str:
    if config.provider == "groq":
        import groq
        client = groq.Groq(api_key=config.api_key)
        with open(audio_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(audio_path), file.read()),
                model="whisper-large-v3",
                response_format="verbose_json"
            )
        if isinstance(transcription, dict):
            segments = transcription.get("segments", [])
        else:
            segments = getattr(transcription, "segments", [])
            
        lines = []
        if segments:
            for s in segments:
                start_val = s.get("start", 0) if isinstance(s, dict) else getattr(s, "start", 0)
                end_val = s.get("end", 0) if isinstance(s, dict) else getattr(s, "end", 0)
                text_val = s.get("text", "") if isinstance(s, dict) else getattr(s, "text", "")
                
                start_str = format_duration(int(start_val or 0))
                end_str = format_duration(int(end_val or 0))
                lines.append(f"[{start_str} - {end_str}] {(text_val or '').strip()}")
        return "\n".join(lines)
        
    elif config.provider == "openai":
        import openai
        client = openai.OpenAI(api_key=config.api_key)
        with open(audio_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=file,
                model="whisper-1",
                response_format="verbose_json"
            )
        if isinstance(transcription, dict):
            segments = transcription.get("segments", [])
        else:
            segments = getattr(transcription, "segments", [])
            
        lines = []
        if segments:
            for s in segments:
                # Handle both dicts and objects for OpenAI backwards compatibility
                start = s.get("start") if isinstance(s, dict) else getattr(s, "start", 0)
                end = s.get("end") if isinstance(s, dict) else getattr(s, "end", 0)
                text = s.get("text") if isinstance(s, dict) else getattr(s, "text", "")
                
                start_str = format_duration(int(start or 0))
                end_str = format_duration(int(end or 0))
                lines.append(f"[{start_str} - {end_str}] {(text or '').strip()}")
        return "\n".join(lines)
        
    elif config.provider == "gemini":
        from google import genai
        client = genai.Client(api_key=config.api_key)
        # Upload file to Gemini
        uploaded_file = client.files.upload(file=audio_path)
        prompt = "Transcribe the following audio. Output ONLY the transcript lines formatted EXACTLY as '[MM:SS - MM:SS] Spoken text here'. Do not include any other commentary."
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[uploaded_file, prompt]
        )
        # Clean up file from Gemini
        if uploaded_file and getattr(uploaded_file, "name", None):
            client.files.delete(name=uploaded_file.name)
        return response.text if response.text else "[Gemini returned empty transcription]"
        
    else:
        raise ValueError(f"Unknown provider for STT: {config.provider}")

def get_transcript(url: str, config: YapnCapConfig) -> TranscriptResult:
    """Extracts metadata and CC transcript from a YouTube URL. Falls back to AI STT if no CC."""
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
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)  # type: ignore
        try:
            transcript = transcript_list.find_transcript([config.language])
        except Exception:
            # Fallback to whatever is available if preferred lang is missing
            available = [t.language_code for t in transcript_list]
            langs = ['en', 'id'] + available
            transcript = transcript_list.find_transcript(langs)
            
        transcript_data = transcript.fetch()
        
        # Build text string with timestamps so the AI engine can extract them
        formatted_lines = []
        for item in transcript_data:
            start_str = format_duration(int(item.start))
            end_str = format_duration(int(item.start + item.duration))
            clean_text = item.text.replace("\n", " ")
            formatted_lines.append(f"[{start_str} - {end_str}] {clean_text}")
            
        text = "\n".join(formatted_lines)
        
        source = "cc"
        language = transcript.language_code
        
    except Exception as cc_err:
        # 3. Fallback: Download audio and transcribe
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                audio_path = _download_audio_temp(url, temp_dir)
                text = _transcribe_audio(audio_path, config)
                source = f"stt ({config.provider})"
                language = config.language
        except Exception as stt_err:
            text = f"[No CC found ({str(cc_err)}) AND STT failed ({str(stt_err)})]"
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
