import os
import re
import asyncio
import yt_dlp
import httpx
from dataclasses import dataclass
from typing import Optional, List
from config import Config
from utils.helpers import get_timestamp, sanitize_filename

@dataclass
class TikTokResult:
    success: bool
    video_path: Optional[str] = None
    audio_path: Optional[str] = None
    thumbnail: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    duration: Optional[int] = None
    views: Optional[int] = None
    likes: Optional[int] = None
    error: Optional[str] = None
    media_type: str = "video"

class TikTokDownloader:
    def __init__(self):
        self.download_dir = Config.DOWNLOAD_DIR

    async def download(self, url: str, audio_only: bool = False) -> TikTokResult:
        """Download TikTok video or audio"""
        try:
            # Clean URL
            url = self._clean_url(url)

            # Get video info first
            info = await self._get_video_info(url)
            if not info:
                return TikTokResult(success=False, error="Gagal mendapatkan info video")

            # Download video/audio
            timestamp = get_timestamp()

            if audio_only:
                filepath = await self._download_audio(url, timestamp, info)
                if filepath:
                    return TikTokResult(
                        success=True,
                        audio_path=filepath,
                        title=info.get("title", "TikTok Audio"),
                        author=info.get("uploader", "Unknown"),
                        duration=info.get("duration", 0),
                        thumbnail=info.get("thumbnail"),
                        media_type="audio"
                    )
            else:
                filepath = await self._download_video(url, timestamp, info)
                if filepath:
                    return TikTokResult(
                        success=True,
                        video_path=filepath,
                        title=info.get("title", "TikTok Video"),
                        author=info.get("uploader", "Unknown"),
                        duration=info.get("duration", 0),
                        views=info.get("view_count", 0),
                        likes=info.get("like_count", 0),
                        thumbnail=info.get("thumbnail"),
                        media_type="video"
                    )

            return TikTokResult(success=False, error="Gagal mendownload media")

        except Exception as e:
            return TikTokResult(success=False, error=str(e))

    def _clean_url(self, url: str) -> str:
        """Clean and normalize TikTok URL"""
        # Remove tracking parameters
        url = re.sub(r'\?.*$', '', url)
        return url

    async def _get_video_info(self, url: str) -> Optional[dict]:
        """Get video information"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }

        try:
            loop = asyncio.get_event_loop()
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
                return info
        except Exception as e:
            print(f"Error getting info: {e}")
            return None

    async def _download_video(self, url: str, timestamp: str, info: dict) -> Optional[str]:
        """Download video file"""
        filename = f"tiktok_{timestamp}.mp4"
        filepath = os.path.join(self.download_dir, filename)

        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': filepath,
            'quiet': True,
            'no_warnings': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        }

        try:
            loop = asyncio.get_event_loop()
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                await loop.run_in_executor(None, lambda: ydl.download([url]))

            if os.path.exists(filepath):
                return filepath
        except Exception as e:
            print(f"Download video error: {e}")

        return None

    async def _download_audio(self, url: str, timestamp: str, info: dict) -> Optional[str]:
        """Download audio only"""
        filename = f"tiktok_{timestamp}.mp3"
        filepath = os.path.join(self.download_dir, filename)

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': filepath.replace('.mp3', '.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        try:
            loop = asyncio.get_event_loop()
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                await loop.run_in_executor(None, lambda: ydl.download([url]))

            if os.path.exists(filepath):
                return filepath
        except Exception as e:
            print(f"Download audio error: {e}")

        return None