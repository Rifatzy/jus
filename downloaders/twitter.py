import os
import re
import asyncio
import yt_dlp
from dataclasses import dataclass
from typing import Optional, List
from config import Config
from utils.helpers import get_timestamp

@dataclass
class TwitterResult:
    success: bool
    video_path: Optional[str] = None
    image_paths: List[str] = None
    thumbnail: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    views: Optional[int] = None
    likes: Optional[int] = None
    retweets: Optional[int] = None
    error: Optional[str] = None
    media_type: str = "video"

class TwitterDownloader:
    def __init__(self):
        self.download_dir = Config.DOWNLOAD_DIR

    async def download(self, url: str) -> TwitterResult:
        """Download Twitter/X content"""
        try:
            # Clean and normalize URL
            url = self._clean_url(url)

            # Get tweet info
            info = await self._get_tweet_info(url)
            if not info:
                return TwitterResult(success=False, error="Gagal mendapatkan info tweet")

            # Download media
            timestamp = get_timestamp()

            # Check for video
            if info.get('ext') in ['mp4', 'webm'] or 'video' in info.get('format', '').lower():
                filepath = await self._download_video(url, timestamp)
                if filepath:
                    return TwitterResult(
                        success=True,
                        video_path=filepath,
                        title=info.get('title', 'Twitter Video')[:100],
                        author=info.get('uploader', 'Unknown'),
                        views=info.get('view_count'),
                        likes=info.get('like_count'),
                        retweets=info.get('repost_count'),
                        thumbnail=info.get('thumbnail'),
                        media_type="video"
                    )

            # Check for images
            elif 'entries' in info or info.get('ext') in ['jpg', 'jpeg', 'png']:
                image_paths = await self._download_images(url, timestamp, info)
                if image_paths:
                    return TwitterResult(
                        success=True,
                        image_paths=image_paths,
                        title=info.get('title', 'Twitter Images')[:100],
                        author=info.get('uploader', 'Unknown'),
                        media_type="image"
                    )

            return TwitterResult(success=False, error="Tidak ada media yang dapat didownload")

        except Exception as e:
            return TwitterResult(success=False, error=str(e))

    def _clean_url(self, url: str) -> str:
        """Clean and normalize Twitter URL"""
        # Convert x.com to twitter.com for compatibility
        url = re.sub(r'(https?://)x\.com', r'\1twitter.com', url)
        # Remove query parameters
        url = re.sub(r'\?.*$', '', url)
        return url

    async def _get_tweet_info(self, url: str) -> Optional[dict]:
        """Get tweet information"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        }

        try:
            loop = asyncio.get_event_loop()
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
                return info
        except Exception as e:
            print(f"Error getting Twitter info: {e}")
            return None

    async def _download_video(self, url: str, timestamp: str) -> Optional[str]:
        """Download Twitter video"""
        filename = f"twitter_{timestamp}.mp4"
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
            print(f"Download Twitter video error: {e}")

        return None

    async def _download_images(self, url: str, timestamp: str, info: dict) -> List[str]:
        """Download Twitter images"""
        image_paths = []

        # Handle multiple images
        entries = info.get('entries', [info])

        for i, entry in enumerate(entries):
            filename = f"twitter_{timestamp}_{i}.jpg"
            filepath = os.path.join(self.download_dir, filename)

            ydl_opts = {
                'outtmpl': filepath,
                'quiet': True,
                'no_warnings': True,
            }

            try:
                entry_url = entry.get('url') or entry.get('webpage_url') or url
                loop = asyncio.get_event_loop()
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    await loop.run_in_executor(None, lambda: ydl.download([entry_url]))

                if os.path.exists(filepath):
                    image_paths.append(filepath)
            except Exception as e:
                print(f"Download Twitter image error: {e}")

        return image_paths