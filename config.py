import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env file
load_dotenv()

class Config:
    """Konfigurasi bot dari environment variables"""

    # ═══════════════════════════════════════════════════════════
    # BOT CONFIGURATION
    # ═══════════════════════════════════════════════════════════

    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    BOT_USERNAME = os.getenv("BOT_USERNAME", "MediaMuncherBot")

    # ═══════════════════════════════════════════════════════════
    # ADMIN CONFIGURATION
    # ═══════════════════════════════════════════════════════════

    # Parse admin IDs dari string ke list of integers
    _admin_ids = os.getenv("ADMIN_IDS", "")
    ADMIN_IDS = [int(x.strip()) for x in _admin_ids.split(",") if x.strip().isdigit()]

    OWNER_ID = int(os.getenv("OWNER_ID", "0"))
    OWNER_USERNAME = os.getenv("OWNER_USERNAME", "")

    # ═══════════════════════════════════════════════════════════
    # CHANNEL CONFIGURATION
    # ═══════════════════════════════════════════════════════════

    FORCE_SUBSCRIBE_CHANNEL = os.getenv("FORCE_SUBSCRIBE_CHANNEL", "")
    LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID", "")

    # ═══════════════════════════════════════════════════════════
    # BOT SETTINGS
    # ═══════════════════════════════════════════════════════════

    DOWNLOAD_PATH = os.getenv("DOWNLOAD_PATH", "downloads")
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    DAILY_LIMIT = int(os.getenv("DAILY_LIMIT", "50"))
    MAINTENANCE_MODE = os.getenv("MAINTENANCE_MODE", "false").lower() == "true"

    # ═══════════════════════════════════════════════════════════
    # DATABASE
    # ═══════════════════════════════════════════════════════════

    DATABASE_PATH = os.getenv("DATABASE_PATH", "database/bot_database.db")

    # ═══════════════════════════════════════════════════════════
    # RATE LIMITING
    # ═══════════════════════════════════════════════════════════

    RATE_LIMIT_SECONDS = int(os.getenv("RATE_LIMIT_SECONDS", "5"))
    MAX_CONCURRENT_DOWNLOADS = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "3"))

    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        """Cek apakah user adalah admin"""
        return user_id in cls.ADMIN_IDS or user_id == cls.OWNER_ID

    @classmethod
    def is_owner(cls, user_id: int) -> bool:
        """Cek apakah user adalah owner"""
        return user_id == cls.OWNER_ID

    @classmethod
    def validate(cls) -> bool:
        """Validasi konfigurasi"""
        if not cls.BOT_TOKEN:
            raise ValueError("❌ BOT_TOKEN tidak ditemukan di .env!")
        if not cls.ADMIN_IDS and not cls.OWNER_ID:
            raise ValueError("❌ ADMIN_IDS atau OWNER_ID harus diisi!")
        return True

# Buat folder yang diperlukan
Path(Config.DOWNLOAD_PATH).mkdir(parents=True, exist_ok=True)
Path(Config.DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)