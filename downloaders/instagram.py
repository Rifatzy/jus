import os
import re
import asyncio
import yt_dlp
from dataclasses import dataclass
from typing import Optional, List
from config import Config
from utils.helpers import get_timestamp

@dataclass
class InstagramResult:
    success: bool
    video_paths: List[str] = None
    image_paths: List[str] = None
    thumbnail: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    likes: Optional[int] = None
    error: Optional[str] = None
    media_type: str = "video"
    is_carousel: bool = False

class InstagramDownloader:
    def __init__(self):
        self.download_dir = Config.DOWNLOAD_DIR

    async def download(self, url: str) -> InstagramResult:
        """Download Instagram content"""
        try:
            # Clean URL
            url = self._clean_url(url)

            # Get media info
            info = await self._get_media_info(url)
            if not info:
                return InstagramResult(success=False, error="Gagal mendapatkan info media")

            # Check if carousel/album
            if 'entries' in info:
                return await self._download_carousel(info)
            else:
                return await self._download_single(url, info)

        except Exception as e:
            return InstagramResult(success=False, error=str(e))

    def _clean_url(self, url: str) -> str:
        """Clean Instagram URL"""
        # Remove query parameters
        url = re.sub(r'\?.*$', '', url)
        # Ensure proper format
        if not url.endswith('/'):
            url += '/'
        return url

    async def _get_media_info(self, url: str) -> Optional[dict]:
        """Get Instagram media information"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'cookiesfrombrowser': ('chrome',),  # Optional: use browser cookies
        }

        try:
            loop = asyncio.get_event_loop()
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
                return info
        except Exception as e:
            print(f"Error getting Instagram info: {e}")
            # Try alternative method
            return await self._get_info_alternative(url)

    async def _get_info_alternative(self, url: str) -> Optional[dict]:
        """Alternative method to get info"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15'
            }
        }

        try:
            loop = asyncio.get_event_loop()
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
                return info
        except:
            return None

    async def _download_single(self, url: str, info: dict) -> InstagramResult:
        """Download single video/image"""
        timestamp = get_timestamp()

        # Check if it's a video or image
        if info.get('ext') in ['jpg', 'jpeg', 'png', 'webp']:
            filepath = await self._download_image(url, timestamp)
            if filepath:
                return InstagramResult(
                    success=True,
                    image_paths=[filepath],
                    title=info.get('title', 'Instagram Post'),
                    author=info.get('uploader', 'Unknown'),
                    media_type="image"
                )
        else:
            filepath = await self._download_video(url, timestamp)
            if filepath:
                return InstagramResult(
                    success=True,
                    video_paths=[filepath],
                    title=info.get('title', 'Instagram Video'),
                    author=info.get('uploader', 'Unknown'),
                    likes=info.get('like_count'),
                    thumbnail=info.get('thumbnail'),
                    media_type="video"
                )

        return InstagramResult(success=False, error="Gagal mendownload media")

    async def _download_carousel(self, info: dict) -> InstagramResult:
        """Download carousel/album"""
        timestamp = get_timestamp()
        video_paths = []
        image_paths = []

        entries = info.get('entries', [])

        for i, entry in enumerate(entries):
            entry_url = entry.get('url') or entry.get('webpage_url')
            if not entry_url:
                continue

            ext = entry.get('ext', 'mp4')

            if ext in ['jpg', 'jpeg', 'png', 'webp']:
                filepath = await self._download_image(entry_url, f"{timestamp}_{i}")
                if filepath:
                    image_paths.append(filepath)
            else:
                filepath = await self._download_video(entry_url, f"{timestamp}_{i}")
                if filepath:
                    video_paths.append(filepath)

        if video_paths or image_paths:
            return InstagramResult(
                success=True,
                video_paths=video_paths if video_paths else None,
                image_paths=image_paths if image_paths else None,
                title=info.get('title', 'Instagram Album'),
                author=info.get('uploader', 'Unknown'),
                media_type="carousel",
                is_carousel=True
            )

        return InstagramResult(success=False, error="Gagal mendownload carousel")

    async def _download_video(self, url: str, timestamp: str) -> Optional[str]:
        """Download video file"""
        filename = f"instagram_{timestamp}.mp4"
        filepath = os.path.join(self.download_dir, filename)

        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': filepath,
            'quiet': True,
            'no_warnings': True,
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

    async def _download_image(self, url: str, timestamp: str) -> Optional[str]:
        """Download image file"""
        filename = f"instagram_{timestamp}.jpg"
        filepath = os.path.join(self.download_dir, filename)

        ydl_opts = {
            'outtmpl': filepath,
            'quiet': True,
            'no_warnings': True,
        }

        try:
            loop = asyncio.get_event_loop()
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                await loop.run_in_executor(None, lambda: ydl.download([url]))

            if os.path.exists(filepath):
                return filepath
        except Exception as e:
            print(f"Download image error: {e}")

        return None