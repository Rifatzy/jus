import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Bot
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    BOT_USERNAME = os.getenv("BOT_USERNAME", "MediaDownloaderBot")

    # Admin
    _admin_ids = os.getenv("ADMIN_IDS", "0")
    ADMIN_IDS = [int(x.strip()) for x in _admin_ids.split(",") if x.strip().isdigit()]

    # Paths
    DOWNLOAD_DIR = "downloads"
    DATABASE_PATH = "bot_database.db"

    # Limits
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "50"))
    DAILY_LIMIT = int(os.getenv("DAILY_LIMIT", "50"))
    RATE_LIMIT_SECONDS = int(os.getenv("RATE_LIMIT_SECONDS", "5"))
    MAX_REQUESTS_PER_MINUTE = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "10"))

    # Premium
    PREMIUM_DAILY_LIMIT = int(os.getenv("PREMIUM_DAILY_LIMIT", "200"))
    PREMIUM_MAX_FILE_SIZE = int(os.getenv("PREMIUM_MAX_FILE_SIZE", "100"))
    PREMIUM_PRICE_MONTHLY = int(os.getenv("PREMIUM_PRICE_MONTHLY", "50000"))
    PREMIUM_PRICE_YEARLY = int(os.getenv("PREMIUM_PRICE_YEARLY", "500000"))

    # AI Features
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    AI_ENABLED = os.getenv("AI_ENABLED", "true").lower() == "true"

    # Gamification
    XP_PER_DOWNLOAD = int(os.getenv("XP_PER_DOWNLOAD", "10"))
    XP_PER_REFERRAL = int(os.getenv("XP_PER_REFERRAL", "100"))
    DAILY_BONUS_COINS = int(os.getenv("DAILY_BONUS_COINS", "5"))
    REFERRAL_BONUS_COINS = int(os.getenv("REFERRAL_BONUS_COINS", "50"))

    # Payment
    MIDTRANS_SERVER_KEY = os.getenv("MIDTRANS_SERVER_KEY", "")
    MIDTRANS_CLIENT_KEY = os.getenv("MIDTRANS_CLIENT_KEY", "")
    PAYMENT_ENABLED = os.getenv("PAYMENT_ENABLED", "false").lower() == "true"

    # Maintenance
    MAINTENANCE_MODE = os.getenv("MAINTENANCE_MODE", "false").lower() == "true"

    # Platforms
    PLATFORMS = {
        "tiktok": ["tiktok.com", "vm.tiktok.com", "vt.tiktok.com"],
        "instagram": ["instagram.com", "instagr.am"],
        "twitter": ["twitter.com", "x.com", "t.co"],
    }

    # Levels Configuration
    LEVELS = {
        1: {"name": "Newbie", "xp": 0, "badge": "🌱"},
        2: {"name": "Beginner", "xp": 100, "badge": "🌿"},
        3: {"name": "Regular", "xp": 300, "badge": "🌳"},
        4: {"name": "Active", "xp": 600, "badge": "⭐"},
        5: {"name": "Pro", "xp": 1000, "badge": "🌟"},
        6: {"name": "Expert", "xp": 1500, "badge": "💫"},
        7: {"name": "Master", "xp": 2500, "badge": "🔥"},
        8: {"name": "Legend", "xp": 4000, "badge": "👑"},
        9: {"name": "Champion", "xp": 6000, "badge": "🏆"},
        10: {"name": "Ultimate", "xp": 10000, "badge": "💎"},
    }

    # Achievements
    ACHIEVEMENTS = {
        "first_download": {"name": "First Step", "desc": "Download pertama", "xp": 20, "badge": "🎯"},
        "download_10": {"name": "Getting Started", "desc": "10 downloads", "xp": 50, "badge": "📥"},
        "download_50": {"name": "Downloader", "desc": "50 downloads", "xp": 100, "badge": "📦"},
        "download_100": {"name": "Pro Downloader", "desc": "100 downloads", "xp": 200, "badge": "🚀"},
        "download_500": {"name": "Download Master", "desc": "500 downloads", "xp": 500, "badge": "👑"},
        "streak_7": {"name": "Weekly Warrior", "desc": "7 hari berturut-turut", "xp": 100, "badge": "🔥"},
        "streak_30": {"name": "Monthly Master", "desc": "30 hari berturut-turut", "xp": 500, "badge": "💪"},
        "referral_1": {"name": "Friendly", "desc": "Invite 1 teman", "xp": 50, "badge": "🤝"},
        "referral_5": {"name": "Influencer", "desc": "Invite 5 teman", "xp": 200, "badge": "📢"},
        "referral_10": {"name": "Ambassador", "desc": "Invite 10 teman", "xp": 500, "badge": "🌟"},
        "premium_member": {"name": "VIP", "desc": "Jadi Premium", "xp": 200, "badge": "💎"},
        "feedback_given": {"name": "Voice", "desc": "Kirim feedback", "xp": 30, "badge": "💬"},
        "all_platforms": {"name": "Explorer", "desc": "Download dari semua platform", "xp": 100, "badge": "🌍"},
    }

    DEFAULT_LANG = "id"

os.makedirs(Config.DOWNLOAD_DIR, exist_ok=True)