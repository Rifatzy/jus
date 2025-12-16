from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import Optional, List, Dict

# Emoji
E = {
    "loading": "⏳", "success": "✅", "error": "❌", "warning": "⚠️",
    "video": "🎬", "photo": "📸", "music": "🎵", "download": "📥",
    "tiktok": "🎵", "instagram": "📷", "twitter": "🐦",
    "stats": "📊", "info": "ℹ️", "history": "📜", "settings": "⚙️",
    "quality": "🎨", "fire": "🔥", "star": "⭐", "rocket": "🚀",
    "sparkles": "✨", "link": "🔗", "folder": "📁", "clock": "🕐",
    "user": "👤", "users": "👥", "heart": "❤️", "crown": "👑",
    "ban": "🚫", "home": "🏠", "broadcast": "📢", "backup": "💾",
    "trash": "🗑️", "calendar": "📅", "trophy": "🏆", "chart": "📈",
    "check": "✓", "left": "◀️", "right": "▶️", "lang": "🌐",
    "premium": "💎", "limit": "🚦", "lock": "🔒", "unlock": "🔓",
    "search": "🔍", "export": "📤", "maintenance": "🔧", "vip": "👑",
    "notify": "🔔", "feedback": "💬", "copy": "📋", "refresh": "🔄",
    # New - Gamification & AI
    "game": "🎮", "coin": "🪙", "xp": "⚡", "level": "📊",
    "achievement": "🏅", "streak": "🔥", "referral": "🤝",
    "spin": "🎰", "gift": "🎁", "shop": "🛒", "leaderboard": "🏆",
    "ai": "🤖", "chat": "💬", "translate": "🌐", "caption": "📝",
    "pay": "💳", "wallet": "👛", "money": "💰", "daily": "📅",
}


# ==================== MAIN MENU ====================

def get_main_menu(lang: str = "id") -> InlineKeyboardMarkup:
    """Main menu with all features"""
    return InlineKeyboardMarkup([
        # Row 1: Platforms
        [
            InlineKeyboardButton(f"{E['tiktok']} TikTok", callback_data="help_tiktok"),
            InlineKeyboardButton(f"{E['instagram']} Instagram", callback_data="help_instagram"),
            InlineKeyboardButton(f"{E['twitter']} Twitter", callback_data="help_twitter"),
        ],
        # Row 2: User features
        [
            InlineKeyboardButton(f"{E['history']} History", callback_data="history:1"),
            InlineKeyboardButton(f"{E['stats']} Stats", callback_data="mystats"),
            InlineKeyboardButton(f"{E['settings']} Settings", callback_data="settings"),
        ],
        # Row 3: Gamification
        [
            InlineKeyboardButton(f"{E['game']} Games", callback_data="games"),
            InlineKeyboardButton(f"{E['leaderboard']} Rank", callback_data="leaderboard"),
            InlineKeyboardButton(f"{E['daily']} Daily", callback_data="daily"),
        ],
        # Row 4: Premium & AI
        [
            InlineKeyboardButton(f"{E['premium']} Premium", callback_data="premium"),
            InlineKeyboardButton(f"{E['shop']} Shop", callback_data="shop"),
            InlineKeyboardButton(f"{E['ai']} AI", callback_data="ai_menu"),
        ],
        # Row 5: Help & Feedback
        [
            InlineKeyboardButton(f"{E['feedback']} Feedback", callback_data="feedback"),
            InlineKeyboardButton(f"{E['info']} Help", callback_data="help"),
        ]
    ])


def get_back_keyboard(to: str = "main", lang: str = "id") -> InlineKeyboardMarkup:
    """Back button"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{E['left']} Back", callback_data=f"back:{to}")]
    ])


def get_home_keyboard(lang: str = "id") -> InlineKeyboardMarkup:
    """Home button"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{E['home']} Main Menu", callback_data="back:main")]
    ])


# ==================== DOWNLOAD ====================

def get_quality_keyboard(platform: str, lang: str = "id") -> InlineKeyboardMarkup:
    """Quality selection"""
    if platform == "tiktok":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{E['video']} Video HD (No WM)", callback_data="dl:video:hd")],
            [
                InlineKeyboardButton(f"{E['video']} Video SD", callback_data="dl:video:sd"),
                InlineKeyboardButton(f"{E['music']} Audio MP3", callback_data="dl:audio:mp3"),
            ],
            [InlineKeyboardButton(f"{E['error']} Cancel", callback_data="cancel")]
        ])
    elif platform == "instagram":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{E['video']} Best Quality", callback_data="dl:video:best")],
            [InlineKeyboardButton(f"{E['photo']} Photo Only", callback_data="dl:photo:best")],
            [InlineKeyboardButton(f"{E['error']} Cancel", callback_data="cancel")]
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{E['video']} Best Quality", callback_data="dl:video:best")],
            [
                InlineKeyboardButton(f"{E['video']} 720p", callback_data="dl:video:720"),
                InlineKeyboardButton(f"{E['video']} 480p", callback_data="dl:video:480"),
            ],
            [InlineKeyboardButton(f"{E['error']} Cancel", callback_data="cancel")]
        ])


def get_quick_or_quality_keyboard(lang: str = "id") -> InlineKeyboardMarkup:
    """Quick download or select quality"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{E['rocket']} Quick Download", callback_data="quick")],
        [InlineKeyboardButton(f"{E['quality']} Select Quality", callback_data="selectquality")],
        [InlineKeyboardButton(f"{E['error']} Cancel", callback_data="cancel")]
    ])


# ==================== HISTORY ====================

def get_history_keyboard(page: int, total_pages: int, has_data: bool, lang: str = "id") -> InlineKeyboardMarkup:
    """History pagination"""
    buttons = []

    if has_data:
        nav = []
        if page > 1:
            nav.append(InlineKeyboardButton("◀️", callback_data=f"history:{page-1}"))
        nav.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
        if page < total_pages:
            nav.append(InlineKeyboardButton("▶️", callback_data=f"history:{page+1}"))
        if nav:
            buttons.append(nav)
        buttons.append([InlineKeyboardButton(f"{E['trash']} Clear", callback_data="clearhistory")])

    buttons.append([InlineKeyboardButton(f"{E['home']} Menu", callback_data="back:main")])
    return InlineKeyboardMarkup(buttons)


def get_confirm_clear_keyboard(lang: str = "id") -> InlineKeyboardMarkup:
    """Confirm clear"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"{E['success']} Yes", callback_data="clearhistory:yes"),
            InlineKeyboardButton(f"{E['error']} No", callback_data="history:1"),
        ]
    ])


# ==================== STATS ====================

def get_stats_keyboard(lang: str = "id") -> InlineKeyboardMarkup:
    """Stats keyboard"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"{E['history']} History", callback_data="history:1"),
            InlineKeyboardButton(f"{E['refresh']} Refresh", callback_data="mystats"),
        ],
        [
            InlineKeyboardButton(f"{E['achievement']} Achievements", callback_data="achievements"),
            InlineKeyboardButton(f"{E['leaderboard']} Leaderboard", callback_data="leaderboard"),
        ],
        [InlineKeyboardButton(f"{E['home']} Menu", callback_data="back:main")]
    ])


# ==================== SETTINGS ====================

def get_settings_keyboard(quality_mode: str, notif: bool, lang: str, user_lang: str = "id") -> InlineKeyboardMarkup:
    """Settings keyboard"""
    q_text = "🔵 Ask" if quality_mode == "ask" else "🟢 Auto"
    n_text = f"ON" if notif else f"OFF"
    l_text = "🇮🇩 ID" if user_lang == "id" else "🇬🇧 EN"

    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{E['quality']} Quality: {q_text}", callback_data="setting:quality")],
        [InlineKeyboardButton(f"{E['notify']} Notifications: {n_text}", callback_data="setting:notif")],
        [InlineKeyboardButton(f"{E['lang']} Language: {l_text}", callback_data="setting:lang")],
        [InlineKeyboardButton(f"{E['home']} Menu", callback_data="back:main")]
    ])


def get_quality_setting_keyboard(lang: str = "id") -> InlineKeyboardMarkup:
    """Quality mode selection"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔵 Always Ask", callback_data="setquality:ask")],
        [InlineKeyboardButton("🟢 Auto Best", callback_data="setquality:auto")],
        [InlineKeyboardButton(f"{E['left']} Back", callback_data="settings")]
    ])


def get_language_keyboard(lang: str = "id") -> InlineKeyboardMarkup:
    """Language selection"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇮🇩 Indonesia", callback_data="setlang:id")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="setlang:en")],
        [InlineKeyboardButton(f"{E['left']} Back", callback_data="settings")]
    ])


# ==================== GAMIFICATION ====================

def get_games_menu_keyboard(lang: str = "id") -> InlineKeyboardMarkup:
    """Games menu"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"{E['daily']} Daily Bonus", callback_data="daily"),
            InlineKeyboardButton(f"{E['spin']} Spin Wheel", callback_data="spin"),
        ],
        [
            InlineKeyboardButton(f"{E['achievement']} Achievements", callback_data="achievements"),
            InlineKeyboardButton(f"{E['leaderboard']} Leaderboard", callback_data="leaderboard"),
        ],
        [
            InlineKeyboardButton(f"{E['referral']} Referral", callback_data="referral"),
            InlineKeyboardButton(f"{E['streak']} Streak", callback_data="streak"),
        ],
        [InlineKeyboardButton(f"{E['home']} Menu", callback_data="back:main")]
    ])


def get_daily_keyboard(claimed: bool, lang: str = "id") -> InlineKeyboardMarkup:
    """Daily bonus keyboard"""
    if claimed:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"✅ Already Claimed Today", callback_data="noop")],
            [InlineKeyboardButton(f"{E['home']} Menu", callback_data="back:main")]
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{E['gift']} Claim Daily Bonus!", callback_data="claim_daily")],
            [InlineKeyboardButton(f"{E['home']} Menu", callback_data="back:main")]
        ])


def get_spin_keyboard(spins_left: int, lang: str = "id") -> InlineKeyboardMarkup:
    """Spin wheel keyboard"""
    buttons = []

    if spins_left > 0:
        buttons.append([InlineKeyboardButton(f"{E['spin']} SPIN! ({spins_left} left)", callback_data="do_spin")])
    else:
        buttons.append([InlineKeyboardButton(f"❌ No Spins Left", callback_data="noop")])
        buttons.append([InlineKeyboardButton(f"{E['coin']} Buy Spin (30 coins)", callback_data="buy:spin_ticket")])

    buttons.append([InlineKeyboardButton(f"{E['home']} Menu", callback_data="back:main")])
    return InlineKeyboardMarkup(buttons)


def get_leaderboard_keyboard(current_type: str = "xp", lang: str = "id") -> InlineKeyboardMarkup:
    """Leaderboard type selection"""
    types = [
        ("xp", f"{E['xp']} XP"),
        ("coins", f"{E['coin']} Coins"),
        ("downloads", f"{E['download']} Downloads"),
        ("streak", f"{E['streak']} Streak"),
    ]

    buttons = []
    row = []
    for type_id, label in types:
        prefix = "✓ " if type_id == current_type else ""
        row.append(InlineKeyboardButton(f"{prefix}{label}", callback_data=f"lb:{type_id}"))
        if len(row) == 2:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(f"{E['home']} Menu", callback_data="back:main")])
    return InlineKeyboardMarkup(buttons)


def get_achievements_keyboard(page: int, total_pages: int, lang: str = "id") -> InlineKeyboardMarkup:
    """Achievements pagination"""
    buttons = []

    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"ach:{page-1}"))
    nav.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"ach:{page+1}"))

    if nav:
        buttons.append(nav)

    buttons.append([InlineKeyboardButton(f"{E['home']} Menu", callback_data="back:main")])
    return InlineKeyboardMarkup(buttons)


def get_referral_keyboard(ref_code: str, lang: str = "id") -> InlineKeyboardMarkup:
    """Referral keyboard"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📋 Copy Code: {ref_code}", callback_data=f"copy_ref:{ref_code}")],
        [InlineKeyboardButton(f"{E['referral']} Enter Referral Code", callback_data="enter_referral")],
        [InlineKeyboardButton(f"{E['home']} Menu", callback_data="back:main")]
    ])


# ==================== AI FEATURES ====================

def get_ai_menu_keyboard(lang: str = "id") -> InlineKeyboardMarkup:
    """AI features menu"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"{E['chat']} AI Chat", callback_data="ai:chat"),
            InlineKeyboardButton(f"{E['translate']} Translate", callback_data="ai:translate"),
        ],
        [
            InlineKeyboardButton(f"{E['caption']} Caption Generator", callback_data="ai:caption"),
            InlineKeyboardButton(f"#️⃣ Hashtags", callback_data="ai:hashtags"),
        ],
        [
            InlineKeyboardButton(f"❓ Ask Question", callback_data="ai:ask"),
            InlineKeyboardButton(f"📝 Summarize", callback_data="ai:summarize"),
        ],
        [InlineKeyboardButton(f"{E['home']} Menu", callback_data="back:main")]
    ])


def get_translate_lang_keyboard(lang: str = "id") -> InlineKeyboardMarkup:
    """Translation language selection"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇬🇧 English", callback_data="translate_to:en"),
            InlineKeyboardButton("🇮🇩 Indonesia", callback_data="translate_to:id"),
        ],
        [
            InlineKeyboardButton("🇯🇵 Japanese", callback_data="translate_to:ja"),
            InlineKeyboardButton("🇰🇷 Korean", callback_data="translate_to:ko"),
        ],
        [
            InlineKeyboardButton("🇨🇳 Chinese", callback_data="translate_to:zh"),
            InlineKeyboardButton("🇪🇸 Spanish", callback_data="translate_to:es"),
        ],
        [
            InlineKeyboardButton("🇫🇷 French", callback_data="translate_to:fr"),
            InlineKeyboardButton("🇩🇪 German", callback_data="translate_to:de"),
        ],
        [InlineKeyboardButton(f"{E['left']} Back", callback_data="ai_menu")]
    ])


# ==================== SHOP & PREMIUM ====================

def get_premium_keyboard(is_premium: bool, lang: str = "id") -> InlineKeyboardMarkup:
    """Premium menu"""
    if is_premium:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{E['premium']} ✓ Premium Active!", callback_data="noop")],
            [InlineKeyboardButton(f"{E['shop']} Coin Shop", callback_data="shop")],
            [InlineKeyboardButton(f"{E['home']} Menu", callback_data="back:main")]
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{E['premium']} Premium Monthly - Rp 50.000", callback_data="buy_plan:premium_monthly")],
            [InlineKeyboardButton(f"{E['premium']} Premium Yearly - Rp 500.000 (Save 17%!)", callback_data="buy_plan:premium_yearly")],
            [InlineKeyboardButton(f"{E['coin']} Buy with Coins", callback_data="buy_premium_coins")],
            [InlineKeyboardButton(f"{E['home']} Menu", callback_data="back:main")]
        ])


def get_shop_keyboard(lang: str = "id") -> InlineKeyboardMarkup:
    """Shop menu"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"─── {E['coin']} Buy Coins ───", callback_data="noop")],
        [
            InlineKeyboardButton("100 Coins - Rp 10K", callback_data="buy_plan:coins_100"),
            InlineKeyboardButton("550 Coins - Rp 45K", callback_data="buy_plan:coins_500"),
        ],
        [InlineKeyboardButton("1200 Coins - Rp 80K (Best!)", callback_data="buy_plan:coins_1000")],
        [InlineKeyboardButton(f"─── {E['shop']} Spend Coins ───", callback_data="noop")],
        [
            InlineKeyboardButton(f"+10 Downloads (20{E['coin']})", callback_data="buy:extra_download_10"),
            InlineKeyboardButton(f"+50 Downloads (80{E['coin']})", callback_data="buy:extra_download_50"),
        ],
        [
            InlineKeyboardButton(f"Premium 1D (50{E['coin']})", callback_data="buy:premium_1day"),
            InlineKeyboardButton(f"Premium 7D (250{E['coin']})", callback_data="buy:premium_7day"),
        ],
        [InlineKeyboardButton(f"Extra Spin (30{E['coin']})", callback_data="buy:spin_ticket")],
        [InlineKeyboardButton(f"{E['home']} Menu", callback_data="back:main")]
    ])


def get_buy_premium_coins_keyboard(lang: str = "id") -> InlineKeyboardMarkup:
    """Buy premium with coins"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"1 Day - 50 {E['coin']}", callback_data="buy:premium_1day")],
        [InlineKeyboardButton(f"3 Days - 120 {E['coin']}", callback_data="buy:premium_3day")],
        [InlineKeyboardButton(f"7 Days - 250 {E['coin']}", callback_data="buy:premium_7day")],
        [InlineKeyboardButton(f"{E['left']} Back", callback_data="premium")]
    ])


def get_payment_keyboard(order_id: str, payment_url: str, lang: str = "id") -> InlineKeyboardMarkup:
    """Payment keyboard"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{E['pay']} Pay Now", url=payment_url)],
        [InlineKeyboardButton(f"{E['success']} I've Paid", callback_data=f"check_payment:{order_id}")],
        [InlineKeyboardButton(f"{E['error']} Cancel", callback_data="cancel_order")]
    ])


def get_promo_keyboard(lang: str = "id") -> InlineKeyboardMarkup:
    """Promo code keyboard"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🎫 Enter Promo Code", callback_data="enter_promo")],
        [InlineKeyboardButton(f"{E['left']} Back", callback_data="shop")]
    ])


# ==================== FEEDBACK ====================

def get_feedback_keyboard(lang: str = "id") -> InlineKeyboardMarkup:
    """Feedback keyboard"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{E['left']} Cancel", callback_data="back:main")]
    ])


# ==================== ADMIN ====================

def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Admin panel"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"{E['chart']} Stats", callback_data="admin:stats"),
            InlineKeyboardButton(f"{E['users']} Users", callback_data="admin:users:1"),
        ],
        [
            InlineKeyboardButton(f"{E['broadcast']} Broadcast", callback_data="admin:broadcast"),
            InlineKeyboardButton(f"{E['ban']} Ban/Unban", callback_data="admin:ban"),
        ],
        [
            InlineKeyboardButton(f"{E['search']} Search", callback_data="admin:search"),
            InlineKeyboardButton(f"{E['premium']} Premium", callback_data="admin:premium"),
        ],
        [
            InlineKeyboardButton(f"{E['money']} Revenue", callback_data="admin:revenue"),
            InlineKeyboardButton(f"🎫 Promo Codes", callback_data="admin:promo"),
        ],
        [
            InlineKeyboardButton(f"{E['maintenance']} Maintenance", callback_data="admin:maintenance"),
            InlineKeyboardButton(f"{E['backup']} Backup", callback_data="admin:backup"),
        ],
        [
            InlineKeyboardButton(f"{E['export']} Export", callback_data="admin:export"),
            InlineKeyboardButton(f"{E['feedback']} Feedbacks", callback_data="admin:feedbacks"),
        ],
        [InlineKeyboardButton(f"{E['home']} Menu", callback_data="back:main")]
    ])


def get_admin_back_keyboard() -> InlineKeyboardMarkup:
    """Back to admin"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{E['left']} Admin Panel", callback_data="admin:panel")]
    ])


def get_admin_users_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Admin users pagination"""
    buttons = []

    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"admin:users:{page-1}"))
    nav.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"admin:users:{page+1}"))

    if nav:
        buttons.append(nav)

    buttons.append([InlineKeyboardButton(f"{E['left']} Back", callback_data="admin:panel")])
    return InlineKeyboardMarkup(buttons)


def get_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    """Confirm broadcast"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"{E['success']} Send", callback_data="broadcast:send"),
            InlineKeyboardButton(f"{E['error']} Cancel", callback_data="admin:panel"),
        ]
    ])


def get_export_keyboard() -> InlineKeyboardMarkup:
    """Export options"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{E['users']} Export Users", callback_data="export:users")],
        [InlineKeyboardButton(f"{E['download']} Export Downloads", callback_data="export:downloads")],
        [InlineKeyboardButton(f"{E['money']} Revenue Report", callback_data="export:revenue")],
        [InlineKeyboardButton(f"{E['chart']} Analytics", callback_data="export:report")],
        [InlineKeyboardButton(f"{E['left']} Back", callback_data="admin:panel")]
    ])


def get_user_detail_keyboard(user_id: int, is_banned: bool, is_premium: bool) -> InlineKeyboardMarkup:
    """User detail actions"""
    ban_text = f"{E['unlock']} Unban" if is_banned else f"{E['ban']} Ban"
    premium_text = f"Remove {E['premium']}" if is_premium else f"Give {E['premium']}"

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(ban_text, callback_data=f"admin:toggleban:{user_id}"),
            InlineKeyboardButton(premium_text, callback_data=f"admin:togglepremium:{user_id}"),
        ],
        [
            InlineKeyboardButton(f"{E['coin']} Give Coins", callback_data=f"admin:givecoins:{user_id}"),
            InlineKeyboardButton(f"{E['xp']} Give XP", callback_data=f"admin:givexp:{user_id}"),
        ],
        [InlineKeyboardButton(f"{E['history']} Activity Log", callback_data=f"admin:userlog:{user_id}")],
        [InlineKeyboardButton(f"{E['left']} Back", callback_data="admin:users:1")]
    ])


def get_create_promo_keyboard() -> InlineKeyboardMarkup:
    """Create promo code menu"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("10% Discount", callback_data="create_promo:10:0")],
        [InlineKeyboardButton("20% Discount", callback_data="create_promo:20:0")],
        [InlineKeyboardButton("50% Discount", callback_data="create_promo:50:0")],
        [InlineKeyboardButton("Rp 10.000 Off", callback_data="create_promo:0:10000")],
        [InlineKeyboardButton("Rp 25.000 Off", callback_data="create_promo:0:25000")],
        [InlineKeyboardButton(f"{E['left']} Back", callback_data="admin:panel")]
    ])