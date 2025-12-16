import re
import os
from datetime import datetime
from typing import Optional, List


# ========== URL & PLATFORM ==========

def detect_platform(url: str) -> Optional[str]:
    """Detect platform from URL"""
    url = url.lower()

    platforms = {
        "tiktok": ["tiktok.com", "vm.tiktok.com", "vt.tiktok.com"],
        "instagram": ["instagram.com", "instagr.am"],
        "twitter": ["twitter.com", "x.com", "t.co"],
    }

    for platform, domains in platforms.items():
        for domain in domains:
            if domain in url:
                return platform
    return None


def extract_url(text: str) -> Optional[str]:
    """Extract URL from text"""
    pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    match = re.search(pattern, text)
    return match.group(0) if match else None


# ========== FORMATTING ==========

def format_size(size_bytes: int) -> str:
    """Format bytes to human readable"""
    if not size_bytes or size_bytes == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    unit_index = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    return f"{size:.1f} {units[unit_index]}"


def format_number(num: int) -> str:
    """Format number with K/M suffix"""
    if not num:
        return "0"

    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(num)


def format_duration(seconds: int) -> str:
    """Format seconds to MM:SS or HH:MM:SS"""
    if not seconds:
        return "00:00"

    seconds = int(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)

    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_date(iso_string: str) -> str:
    """Format ISO date to readable format (DD Mon YYYY)"""
    if not iso_string:
        return "N/A"

    try:
        dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        return dt.strftime("%d %b %Y")
    except:
        try:
            return iso_string[:10]
        except:
            return "N/A"


def format_datetime(iso_string: str) -> str:
    """Format ISO datetime to readable format"""
    if not iso_string:
        return "N/A"

    try:
        dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        return dt.strftime("%d %b %Y, %H:%M")
    except:
        try:
            return iso_string[:16]
        except:
            return "N/A"


def format_timestamp(dt: datetime = None) -> str:
    """Format datetime to timestamp string"""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# ========== FILE OPERATIONS ==========

def get_timestamp() -> str:
    """Get current timestamp for filenames"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def sanitize_filename(filename: str) -> str:
    """Sanitize filename - remove invalid characters"""
    if not filename:
        return "download"

    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*\n\r\t\x00'
    for char in invalid_chars:
        filename = filename.replace(char, '')

    # Replace spaces and special chars
    filename = filename.replace(' ', '_')
    filename = re.sub(r'[^\w\-_.]', '', filename)

    # Remove non-ASCII characters
    filename = filename.encode('ascii', 'ignore').decode('ascii')

    # Limit length
    max_length = 100
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext

    # If empty after sanitizing
    if not filename or filename in ['.', '..']:
        filename = "download"

    return filename


def cleanup_file(filepath: str) -> bool:
    """Delete file safely"""
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
            return True
    except Exception as e:
        print(f"Cleanup error: {e}")
    return False


def cleanup_files(filepaths: List[str]) -> int:
    """Delete multiple files, return count of deleted"""
    deleted = 0
    for filepath in filepaths:
        if cleanup_file(filepath):
            deleted += 1
    return deleted


def get_file_size(filepath: str) -> int:
    """Get file size in bytes"""
    try:
        if filepath and os.path.exists(filepath):
            return os.path.getsize(filepath)
    except:
        pass
    return 0


# ========== TEXT OPERATIONS ==========

def truncate(text: str, length: int = 30, suffix: str = "...") -> str:
    """Truncate text with suffix"""
    if not text:
        return ""

    text = str(text).strip()

    if len(text) <= length:
        return text

    return text[:length - len(suffix)] + suffix


def escape_markdown(text: str) -> str:
    """Escape Markdown special characters"""
    if not text:
        return ""

    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']

    for char in escape_chars:
        text = text.replace(char, f'\\{char}')

    return text


def clean_text(text: str) -> str:
    """Clean text from special characters"""
    if not text:
        return ""

    # Remove control characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


# ========== ADMIN & PERMISSIONS ==========

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    try:
        from config import Config
        return user_id in Config.ADMIN_IDS
    except:
        return False


def get_platform_emoji(platform: str) -> str:
    """Get emoji for platform"""
    emojis = {
        "tiktok": "🎵",
        "instagram": "📷",
        "twitter": "🐦",
        "youtube": "▶️",
        "facebook": "👤",
        "pinterest": "📌",
    }
    return emojis.get(platform.lower(), "📥")


def get_media_emoji(media_type: str) -> str:
    """Get emoji for media type"""
    emojis = {
        "video": "🎬",
        "audio": "🎵",
        "image": "📸",
        "photo": "📸",
        "carousel": "🎠",
    }
    return emojis.get(media_type.lower(), "📁")


# ========== VALIDATION ==========

def is_valid_url(url: str) -> bool:
    """Check if string is valid URL"""
    if not url:
        return False

    pattern = r'^https?://[^\s<>"{}|\\^`\[\]]+$'
    return bool(re.match(pattern, url))


def is_valid_user_id(user_id) -> bool:
    """Check if valid Telegram user ID"""
    try:
        uid = int(user_id)
        return uid > 0
    except:
        return False


# ========== MISC ==========

def get_progress_bar(current: int, total: int, length: int = 10) -> str:
    """Generate text progress bar"""
    if total <= 0:
        return "░" * length

    filled = int(length * current / total)
    empty = length - filled

    return "█" * filled + "░" * empty


def time_ago(iso_string: str) -> str:
    """Get relative time (e.g., '2 hours ago')"""
    if not iso_string:
        return "Unknown"

    try:
        dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        now = datetime.now()

        if dt.tzinfo:
            now = now.replace(tzinfo=dt.tzinfo)

        diff = now - dt
        seconds = diff.total_seconds()

        if seconds < 60:
            return "Just now"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes} min ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f"{days} day{'s' if days > 1 else ''} ago"
        else:
            return format_date(iso_string)
    except:
        return "Unknown"