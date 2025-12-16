import os
import asyncio
import logging
import random
from datetime import datetime
from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)
from telegram.constants import ParseMode

from config import Config
from languages import get_text
from utils import (
    # Database & Core
    db, rate_limiter, daily_limiter, Analytics,
    # Helpers
    detect_platform, extract_url, format_size, format_number,
    format_duration, format_date, format_datetime, get_timestamp,
    truncate, cleanup_file, is_admin, get_progress_bar,
    # Keyboards
    get_main_menu, get_back_keyboard, get_home_keyboard,
    get_quality_keyboard, get_quick_or_quality_keyboard,
    get_history_keyboard, get_confirm_clear_keyboard,
    get_stats_keyboard, get_settings_keyboard,
    get_quality_setting_keyboard, get_language_keyboard,
    get_premium_keyboard, get_feedback_keyboard,
    get_admin_keyboard, get_admin_back_keyboard,
    get_admin_users_keyboard, get_broadcast_confirm_keyboard,
    get_export_keyboard, get_user_detail_keyboard,
    # New keyboards
    get_games_menu_keyboard, get_daily_keyboard, get_spin_keyboard,
    get_leaderboard_keyboard, get_achievements_keyboard, get_referral_keyboard,
    get_ai_menu_keyboard, get_translate_lang_keyboard,
    get_shop_keyboard, get_buy_premium_coins_keyboard, get_payment_keyboard,
    get_create_promo_keyboard,
)
from utils.ai_features import ai_features, free_ai
from utils.gamification import Gamification
from utils.monetization import Monetization
from downloaders import TikTokDownloader, InstagramDownloader, TwitterDownloader

# ==================== LOGGING ====================
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ==================== INITIALIZE ====================
tiktok_dl = TikTokDownloader()
instagram_dl = InstagramDownloader()
twitter_dl = TwitterDownloader()
analytics = Analytics(db)
gamification = Gamification(db)
monetization = Monetization(db)

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
    "premium": "💎", "coin": "🪙", "xp": "⚡", "game": "🎮",
    "achievement": "🏅", "spin": "🎰", "gift": "🎁", "shop": "🛒",
    "ai": "🤖", "streak": "🔥", "referral": "🤝", "money": "💰",
}


# ==================== HELPER FUNCTIONS ====================

def get_lang(user_id: int) -> str:
    """Get user language"""
    return db.get_user_language(user_id)


def t(key: str, user_id: int, **kwargs) -> str:
    """Get translated text"""
    return get_text(key, get_lang(user_id), **kwargs)

# ==================== MESSAGE BUILDERS ====================

def build_welcome(user_id: int, name: str) -> str:
    lang = get_lang(user_id)
    is_prem = db.is_premium(user_id)
    game_stats = gamification.get_game_stats(user_id)

    badge = f" {E['premium']}" if is_prem else ""
    level_badge = game_stats.get('level_badge', '🌱')

    return f"""
{E['sparkles']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['sparkles']}
     {E['rocket']} *MEDIA DOWNLOADER BOT*
{E['sparkles']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['sparkles']}

{level_badge} Halo *{name}*!{badge}

{E['coin']} Coins: `{game_stats.get('coins', 0)}`
{E['xp']} Level: `{game_stats.get('level', 1)}` ({game_stats.get('level_name', 'Newbie')})
{E['streak']} Streak: `{game_stats.get('streak', 0)}` hari

{E['star']} *Platform:*
├ {E['tiktok']} TikTok
├ {E['instagram']} Instagram
└ {E['twitter']} Twitter/X

{E['link']} Kirim link untuk download!

{E['sparkles']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['sparkles']}
"""


def build_help(user_id: int) -> str:
    return f"""
{E['info']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['info']}
            *HELP*
{E['info']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['info']}

{E['download']} *Download:*
Kirim link TikTok/Instagram/Twitter

{E['game']} *Games:*
├ Daily Bonus - Klaim setiap hari
├ Spin Wheel - Menangkan hadiah
├ Achievements - Kumpulkan badge
└ Leaderboard - Bersaing dengan user lain

{E['ai']} *AI Features:*
├ AI Chat - Ngobrol dengan AI
├ Translate - Terjemahan
├ Caption - Generate caption
└ Hashtags - Generate hashtags

{E['shop']} *Shop:*
├ Premium - Fitur eksklusif
└ Coins - Beli item & fitur

{E['info']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['info']}
"""


def build_stats(user_id: int, name: str) -> str:
    stats = db.get_user_stats(user_id)
    game = gamification.get_game_stats(user_id)
    is_prem = db.is_premium(user_id)
    remaining = daily_limiter.get_remaining(user_id, is_prem)

    fav = stats.get('favorite', '-')
    if fav:
        fav = fav.title()

    status = f"{E['premium']} PREMIUM" if is_prem else "FREE"
    progress_bar = get_progress_bar(int(game['level_progress']), 100, 10)

    return f"""
{E['stats']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['stats']}
      *STATISTIK* {E['trophy']}
{E['stats']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['stats']}

{game['level_badge']} *{name}* ({status})
{E['calendar']} Joined: {format_date(stats['join_date']) if stats['join_date'] else 'N/A'}

{E['xp']} *Level {game['level']} - {game['level_name']}*
{progress_bar} {game['level_progress']:.0f}%
XP: `{game['xp']}/{game['next_xp']}`

{E['coin']} *Coins:* `{game['coins']}`
{E['streak']} *Streak:* `{game['streak']}` hari
{E['achievement']} *Achievements:* `{game['achievements_unlocked']}/{game['achievements_total']}`
{E['trophy']} *Rank:* #{game['xp_rank']}

{E['download']} *Downloads:* `{stats['total']}`
├ {E['tiktok']} TikTok: `{stats['tiktok']}`
├ {E['instagram']} Instagram: `{stats['instagram']}`
└ {E['twitter']} Twitter: `{stats['twitter']}`

{E['fire']} *Activity:*
├ Hari ini: `{stats['today']}`
├ Minggu ini: `{stats['this_week']}`
├ Favorit: `{fav}`
└ Sisa limit: `{remaining}`

{E['stats']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['stats']}
"""


def build_games_menu(user_id: int) -> str:
    game = gamification.get_game_stats(user_id)
    streak = gamification.get_streak(user_id)

    return f"""
{E['game']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['game']}
          *GAMES & REWARDS*
{E['game']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['game']}

{game['level_badge']} Level: *{game['level']}* ({game['level_name']})
{E['xp']} XP: `{game['xp']}`
{E['coin']} Coins: `{game['coins']}`
{E['streak']} Streak: `{streak}` hari

{E['gift']} *Daily Bonus* - Klaim setiap hari!
{E['spin']} *Spin Wheel* - Putar & menang!
{E['achievement']} *Achievements* - {game['achievements_unlocked']}/{game['achievements_total']}
{E['trophy']} *Leaderboard* - Rank #{game['xp_rank']}
{E['referral']} *Referral* - Invite teman!

{E['game']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['game']}
"""


def build_leaderboard(lb_type: str, data: list, user_rank: int) -> str:
    type_names = {
        "xp": f"{E['xp']} XP Ranking",
        "coins": f"{E['coin']} Coins Ranking",
        "downloads": f"{E['download']} Downloads Ranking",
        "streak": f"{E['streak']} Streak Ranking",
    }

    title = type_names.get(lb_type, "Ranking")
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    text = f"""
{E['trophy']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['trophy']}
       *{title}*
{E['trophy']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['trophy']}

"""

    for i, entry in enumerate(data[:10]):
        medal = medals[i] if i < len(medals) else f"{i+1}."
        badge = entry.get('badge', '')
        text += f"{medal} {badge} *{entry['name']}*\n"
        text += f"    └ `{entry['value']:,}`\n"

    if user_rank > 0:
        text += f"\n📊 *Rank kamu:* #{user_rank}"

    return text


def build_achievements(achievements: list, page: int, total_pages: int) -> str:
    text = f"""
{E['achievement']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['achievement']}
        *ACHIEVEMENTS*
{E['achievement']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['achievement']}

"""

    start = (page - 1) * 5
    end = start + 5

    for ach in achievements[start:end]:
        status = "✅" if ach.unlocked else "🔒"
        text += f"{status} {ach.badge} *{ach.name}*\n"
        text += f"    └ {ach.description} (+{ach.xp} XP)\n\n"

    unlocked = sum(1 for a in achievements if a.unlocked)
    text += f"📊 Progress: {unlocked}/{len(achievements)}"

    return text


def build_referral(user_id: int, ref_code: str) -> str:
    count = gamification.get_referral_count(user_id)

    return f"""
{E['referral']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['referral']}
          *REFERRAL PROGRAM*
{E['referral']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['referral']}

{E['gift']} *Bonus untuk kamu & temanmu!*

Kode Referral: `{ref_code}`

{E['coin']} *Rewards:*
├ Kamu dapat: 50 coins + 100 XP
└ Teman dapat: 50 coins

{E['users']} Total Referrals: `{count}`

{E['link']} *Cara share:*
1. Copy kode di atas
2. Kirim ke temanmu
3. Mereka input kode saat /start

{E['referral']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['referral']}
"""


def build_ai_menu(user_id: int) -> str:
    return f"""
{E['ai']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['ai']}
          *AI FEATURES*
{E['ai']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['ai']}

{E['ai']} *AI Chat* - Ngobrol dengan AI
🌐 *Translate* - Terjemahan bahasa
📝 *Caption* - Generate caption video
#️⃣ *Hashtags* - Generate hashtags
❓ *Ask* - Tanya apapun
📋 *Summarize* - Ringkas teks panjang

Pilih fitur di bawah:

{E['ai']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['ai']}
"""


def build_shop(user_id: int) -> str:
    coins = gamification.get_coins(user_id)
    is_prem = db.is_premium(user_id)

    return f"""
{E['shop']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['shop']}
             *SHOP*
{E['shop']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['shop']}

{E['coin']} *Coins kamu:* `{coins}`
{E['premium']} *Status:* {'PREMIUM ✓' if is_prem else 'FREE'}

━━━ {E['coin']} *Beli Coins* ━━━
• 100 Coins - Rp 10.000
• 550 Coins - Rp 45.000 (Best!)
• 1200 Coins - Rp 80.000

━━━ {E['shop']} *Tukar Coins* ━━━
• +10 Downloads - 20 coins
• +50 Downloads - 80 coins
• Premium 1 Hari - 50 coins
• Premium 7 Hari - 250 coins
• Extra Spin - 30 coins

{E['shop']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['shop']}
"""


def build_premium(user_id: int) -> str:
    is_prem = db.is_premium(user_id)

    if is_prem:
        return f"""
{E['premium']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['premium']}
         *PREMIUM ACTIVE* ✓
{E['premium']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['premium']}

{E['success']} Kamu adalah member Premium!

{E['star']} *Benefits aktif:*
├ 📥 200 downloads/hari
├ 📁 Max file 100MB
├ 🚀 Prioritas download
├ 🎰 3x spin per hari
└ ⭐ Badge Premium

Terima kasih atas dukunganmu! 💖

{E['premium']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['premium']}
"""
    else:
        return f"""
{E['premium']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['premium']}
            *PREMIUM*
{E['premium']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['premium']}

{E['star']} *Keuntungan Premium:*
├ 📥 200 downloads/hari
├ 📁 Max file 100MB
├ 🚀 Prioritas download
├ 🎰 3x spin per hari
├ ⭐ Badge Premium
└ 🎁 Bonus 100 coins

{E['money']} *Harga:*
├ Monthly: Rp 50.000
└ Yearly: Rp 500.000 (Hemat 17%!)

{E['coin']} Atau beli dengan Coins!

{E['premium']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['premium']}
"""


def build_processing(platform: str) -> str:
    return f"""
{E['loading']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['loading']}

{E.get(platform, '📥')} *Memproses...*

{E['clock']} Mohon tunggu...

{E['loading']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['loading']}
"""


def build_success(platform: str, title: str, author: str, **kw) -> str:
    extra = ""
    if kw.get('duration'):
        extra += f"\n{E['clock']} Duration: `{format_duration(kw['duration'])}`"
    if kw.get('views'):
        extra += f"\n👁 Views: `{format_number(kw['views'])}`"
    if kw.get('likes'):
        extra += f"\n{E['heart']} Likes: `{format_number(kw['likes'])}`"
    if kw.get('file_size'):
        extra += f"\n{E['folder']} Size: `{format_size(kw['file_size'])}`"
    if kw.get('xp_gained'):
        extra += f"\n{E['xp']} +{kw['xp_gained']} XP"

    return f"""
{E['success']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['success']}
      *DOWNLOAD BERHASIL!*
{E['success']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['success']}

{E.get(platform, '📥')} *{platform.title()}*
{E['user']} `{truncate(author, 20)}`
{E['video']} `{truncate(title, 30)}`{extra}

{E['star']} Thanks for using this bot!

{E['success']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['success']}
"""


def build_error(user_id: int, error: str) -> str:
    return f"""
{E['error']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['error']}
           *ERROR*
{E['error']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['error']}

{E['warning']} `{truncate(error, 80)}`

{E['info']} Coba lagi atau gunakan link lain.

{E['error']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['error']}
"""


def build_banned() -> str:
    return f"""
{E['ban']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['ban']}
        *AKSES DITOLAK*
{E['ban']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['ban']}

Akun kamu telah di-banned.
Hubungi admin untuk informasi.
"""


def build_maintenance() -> str:
    return f"""
{E['loading']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['loading']}
        *MAINTENANCE*
{E['loading']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['loading']}

Bot sedang dalam maintenance.
Silakan coba lagi nanti.
"""


# ==================== ADMIN BUILDERS ====================

def build_admin_panel() -> str:
    return f"""
{E['crown']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['crown']}
          *ADMIN PANEL*
{E['crown']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['crown']}

Selamat datang, Admin!
Pilih menu di bawah:
"""


def build_admin_stats() -> str:
    s = db.get_global_stats()

    platforms = ""
    for p, c in s.get('platforms', {}).items():
        platforms += f"\n├ {E.get(p, '📥')} {p.title()}: `{c}`"

    top = ""
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for i, u in enumerate(s.get('top_users', [])[:5]):
        top += f"\n{medals[i]} {u['name']}: `{u['downloads']}`"

    return f"""
{E['chart']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['chart']}
        *BOT STATISTICS*
{E['chart']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['chart']}

{E['users']} *Users:*
├ Total: `{s['total_users']}`
├ Aktif (7d): `{s['active_users']}`
├ Premium: `{s['premium']}`
├ Baru hari ini: `{s['new_today']}`
└ Banned: `{s['banned']}`

{E['download']} *Downloads:*
├ Total: `{s['total_downloads']}`
└ Hari ini: `{s['today_downloads']}`

{E['folder']} *Size:* `{format_size(s['total_size'])}`

{E['chart']} *Platform:*{platforms or ' N/A'}

{E['trophy']} *Top Users:*{top or ' N/A'}

{E['clock']} `{datetime.now().strftime('%d/%m/%Y %H:%M')}`

{E['chart']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['chart']}
"""


def build_revenue_stats() -> str:
    r = monetization.get_revenue_stats(30)

    by_plan = ""
    for plan_id, data in r.get('by_plan', {}).items():
        by_plan += f"\n├ {plan_id}: {data['count']}x = Rp {data['amount']:,}"

    return f"""
{E['money']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['money']}
        *REVENUE REPORT*
{E['money']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['money']}

📅 *Period:* Last 30 days

{E['money']} *Total Revenue:*
`Rp {r['total_revenue']:,}`

📦 *Total Orders:* `{r['total_orders']}`

📊 *By Plan:*{by_plan or ' No data'}

{E['money']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['money']}
"""

# ==================== COMMAND HANDLERS ====================

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    args = ctx.args

    # Check maintenance
    if Config.MAINTENANCE_MODE and not is_admin(user.id):
        await update.message.reply_text(build_maintenance(), parse_mode=ParseMode.MARKDOWN)
        return

    # Check banned
    if db.is_banned(user.id):
        await update.message.reply_text(build_banned(), parse_mode=ParseMode.MARKDOWN)
        return

    # Add user
    db.add_user(user.id, user.username or "", user.first_name or "", user.last_name or "")

    # Check referral code from args
    if args and args[0].startswith("ref_"):
        ref_code = args[0].replace("ref_", "")
        success, msg = gamification.apply_referral(user.id, ref_code)
        if success:
            await update.message.reply_text(f"{E['success']} {msg}", parse_mode=ParseMode.MARKDOWN)

    # Initialize gamification
    gamification._ensure_user_game(user.id)

    await update.message.reply_text(
        build_welcome(user.id, user.first_name),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_menu(get_lang(user.id))
    )


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await update.message.reply_text(
        build_help(update.effective_user.id),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_home_keyboard()
    )


async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command"""
    user = update.effective_user
    await update.message.reply_text(
        build_stats(user.id, user.first_name),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_stats_keyboard()
    )


async def cmd_daily(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /daily command"""
    user = update.effective_user
    success, reward = gamification.claim_daily(user.id)

    if success:
        text = f"""
{E['gift']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['gift']}
        *DAILY BONUS!*
{E['gift']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['gift']}

{E['calendar']} Hari ke-*{reward.day}*

{E['coin']} +{reward.coins} Coins
{E['xp']} +{reward.xp} XP
{reward.bonus}

Kembali besok untuk lanjut streak!

{E['gift']}━━━━━━━━━━━━━━━━━━━━━━━━━━{E['gift']}
"""
    else:
        text = f"{E['success']} Sudah klaim hari ini! Kembali besok."

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_home_keyboard())

    # Check achievements
    new_achievements = gamification.check_achievements(user.id)
    for ach in new_achievements:
        await update.message.reply_text(
            f"{E['achievement']} *ACHIEVEMENT UNLOCKED!*\n\n{ach.badge} *{ach.name}*\n{ach.description}\n+{ach.xp} XP",
            parse_mode=ParseMode.MARKDOWN
        )


async def cmd_spin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /spin command"""
    user = update.effective_user
    is_prem = db.is_premium(user.id)
    max_spins = 3 if is_prem else 1

    # Get spins used today (simple approach)
    spins_left = max_spins  # You might want to track this properly

    await update.message.reply_text(
        f"{E['spin']} *SPIN WHEEL*\n\nPutar dan menangkan hadiah!",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_spin_keyboard(spins_left)
    )


async def cmd_referral(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /referral command"""
    user = update.effective_user
    ref_code = gamification.get_referral_code(user.id)

    await update.message.reply_text(
        build_referral(user.id, ref_code),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_referral_keyboard(ref_code)
    )


async def cmd_shop(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /shop command"""
    user = update.effective_user

    await update.message.reply_text(
        build_shop(user.id),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_shop_keyboard()
    )


async def cmd_premium(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /premium command"""
    user = update.effective_user
    is_prem = db.is_premium(user.id)

    await update.message.reply_text(
        build_premium(user.id),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_premium_keyboard(is_prem)
    )


async def cmd_ai(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /ai command"""
    await update.message.reply_text(
        build_ai_menu(update.effective_user.id),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_ai_menu_keyboard()
    )


async def cmd_leaderboard(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /leaderboard command"""
    user = update.effective_user
    lb_data = gamification.get_leaderboard("xp", 10)
    user_rank = gamification.get_user_rank(user.id, "xp")

    await update.message.reply_text(
        build_leaderboard("xp", lb_data, user_rank),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_leaderboard_keyboard("xp")
    )


async def cmd_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(f"{E['error']} Not authorized!")
        return

    await update.message.reply_text(
        build_admin_panel(),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_admin_keyboard()
    )

# ==================== CALLBACK HANDLER ====================

async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries"""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    data = query.data
    lang = get_lang(user.id)

    # Check maintenance
    if Config.MAINTENANCE_MODE and not is_admin(user.id):
        await query.edit_message_text(build_maintenance(), parse_mode=ParseMode.MARKDOWN)
        return

    # Check banned
    if db.is_banned(user.id) and not is_admin(user.id):
        await query.edit_message_text(build_banned(), parse_mode=ParseMode.MARKDOWN)
        return

    # ===== NAVIGATION =====
    if data == "back:main":
        await query.edit_message_text(
            build_welcome(user.id, user.first_name),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_menu(lang)
        )

    elif data == "help":
        await query.edit_message_text(
            build_help(user.id),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_home_keyboard()
        )

    elif data == "noop":
        pass

    elif data.startswith("help_"):
        platform = data.split("_")[1]
        await show_platform_help(query, platform, user.id)

    # ===== HISTORY =====
    elif data.startswith("history:"):
        page = int(data.split(":")[1])
        await show_history(query, user.id, page)

    elif data == "clearhistory":
        await query.edit_message_text(
            f"{E['warning']} Hapus semua history?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_confirm_clear_keyboard()
        )

    elif data == "clearhistory:yes":
        db.clear_user_history(user.id)
        await query.edit_message_text(
            f"{E['success']} History dihapus!",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_home_keyboard()
        )

    # ===== STATS =====
    elif data == "mystats":
        await query.edit_message_text(
            build_stats(user.id, user.first_name),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_stats_keyboard()
        )

    # ===== SETTINGS =====
    elif data == "settings":
        q_mode = db.get_quality_mode(user.id)
        notif = db.get_notifications(user.id)
        await query.edit_message_text(
            f"{E['settings']} *PENGATURAN*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_settings_keyboard(q_mode, notif, lang, lang)
        )

    elif data == "setting:quality":
        await query.edit_message_text(
            f"{E['quality']} *Pilih mode kualitas:*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_quality_setting_keyboard()
        )

    elif data.startswith("setquality:"):
        mode = data.split(":")[1]
        db.set_quality_mode(user.id, mode)
        await query.edit_message_text(
            f"{E['success']} Mode: *{'Always Ask' if mode == 'ask' else 'Auto Best'}*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_settings_keyboard(mode, db.get_notifications(user.id), lang, lang)
        )

    elif data == "setting:notif":
        current = db.get_notifications(user.id)
        db.set_notifications(user.id, not current)
        await query.edit_message_text(
            f"{E['success']} Notifikasi: *{'ON' if not current else 'OFF'}*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_settings_keyboard(db.get_quality_mode(user.id), not current, lang, lang)
        )

    elif data == "setting:lang":
        await query.edit_message_text(
            f"{E['lang']} *Pilih bahasa:*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_language_keyboard()
        )

    elif data.startswith("setlang:"):
        new_lang = data.split(":")[1]
        db.set_user_language(user.id, new_lang)
        msg = "✅ Language: English!" if new_lang == "en" else "✅ Bahasa: Indonesia!"
        await query.edit_message_text(
            msg,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_settings_keyboard(db.get_quality_mode(user.id), db.get_notifications(user.id), new_lang, new_lang)
        )

    # ===== DOWNLOAD =====
    elif data == "quick":
        await handle_download(query, ctx, "video", "best")

    elif data == "selectquality":
        pending = ctx.user_data.get('pending', {})
        platform = pending.get('platform', 'tiktok')
        url = pending.get('url', '')
        await query.edit_message_text(
            f"{E['quality']} *Pilih Kualitas:*\n\n{E['link']} `{truncate(url, 35)}`",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_quality_keyboard(platform)
        )

    elif data.startswith("dl:"):
        parts = data.split(":")
        media_type = parts[1]
        quality = parts[2] if len(parts) > 2 else "best"
        await handle_download(query, ctx, media_type, quality)

    elif data == "cancel":
        ctx.user_data.clear()
        await query.edit_message_text(
            f"{E['success']} Dibatalkan.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_home_keyboard()
        )

    # ===== GAMES =====
    elif data == "games":
        await query.edit_message_text(
            build_games_menu(user.id),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_games_menu_keyboard()
        )

    elif data == "daily":
        success, reward = gamification.claim_daily(user.id)
        if success:
            text = f"{E['gift']} *DAILY BONUS!*\n\nHari ke-{reward.day}\n+{reward.coins} Coins\n+{reward.xp} XP\n{reward.bonus}"
            # Check achievements
            new_ach = gamification.check_achievements(user.id)
            for ach in new_ach:
                text += f"\n\n{E['achievement']} *{ach.name}* unlocked!"
        else:
            text = f"{E['success']} Sudah klaim hari ini! Kembali besok."

        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_daily_keyboard(not success))

    elif data == "claim_daily":
        success, reward = gamification.claim_daily(user.id)
        if success:
            text = f"{E['gift']} *DAILY BONUS!*\n\nHari ke-{reward.day}\n+{reward.coins} Coins\n+{reward.xp} XP\n{reward.bonus}"
        else:
            text = f"{E['success']} Sudah klaim hari ini!"
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_daily_keyboard(True))

    elif data == "spin":
        is_prem = db.is_premium(user.id)
        max_spins = 3 if is_prem else 1
        await query.edit_message_text(
            f"{E['spin']} *SPIN WHEEL*\n\nPutar dan menangkan hadiah!",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_spin_keyboard(max_spins)
        )

    elif data == "do_spin":
        success, prize_name, prize_value = gamification.spin_wheel(user.id)
        if success:
            text = f"{E['spin']} *SPIN RESULT!*\n\n🎉 {prize_name}"
            if prize_value > 0:
                text += f"\n\nSelamat! Kamu menang!"
        else:
            text = f"{E['error']} Tidak ada spin tersisa!"

        is_prem = db.is_premium(user.id)
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_spin_keyboard(0))

    elif data == "leaderboard":
        lb_data = gamification.get_leaderboard("xp", 10)
        user_rank = gamification.get_user_rank(user.id, "xp")
        await query.edit_message_text(
            build_leaderboard("xp", lb_data, user_rank),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_leaderboard_keyboard("xp")
        )

    elif data.startswith("lb:"):
        lb_type = data.split(":")[1]
        lb_data = gamification.get_leaderboard(lb_type, 10)
        user_rank = gamification.get_user_rank(user.id, lb_type)
        await query.edit_message_text(
            build_leaderboard(lb_type, lb_data, user_rank),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_leaderboard_keyboard(lb_type)
        )

    elif data == "achievements":
        achievements = gamification.get_achievements(user.id)
        total_pages = max(1, (len(achievements) + 4) // 5)
        await query.edit_message_text(
            build_achievements(achievements, 1, total_pages),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_achievements_keyboard(1, total_pages)
        )

    elif data.startswith("ach:"):
        page = int(data.split(":")[1])
        achievements = gamification.get_achievements(user.id)
        total_pages = max(1, (len(achievements) + 4) // 5)
        await query.edit_message_text(
            build_achievements(achievements, page, total_pages),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_achievements_keyboard(page, total_pages)
        )

    elif data == "referral":
        ref_code = gamification.get_referral_code(user.id)
        await query.edit_message_text(
            build_referral(user.id, ref_code),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_referral_keyboard(ref_code)
        )

    elif data == "enter_referral":
        ctx.user_data['awaiting_referral'] = True
        await query.edit_message_text(
            f"{E['referral']} Kirim kode referral:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_back_keyboard("games")
        )

    elif data == "streak":
        streak = gamification.get_streak(user.id)
        await query.edit_message_text(
            f"{E['streak']} *STREAK*\n\nStreak saat ini: *{streak}* hari\n\nDownload setiap hari untuk menjaga streak!",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_home_keyboard()
        )

    # ===== AI FEATURES =====
    elif data == "ai_menu":
        await query.edit_message_text(
            build_ai_menu(user.id),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_ai_menu_keyboard()
        )

    elif data == "ai:chat":
        ctx.user_data['ai_mode'] = 'chat'
        await query.edit_message_text(
            f"{E['ai']} *AI Chat*\n\nKirim pesanmu:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_back_keyboard("ai_menu")
        )

    elif data == "ai:translate":
        await query.edit_message_text(
            f"🌐 *Translate*\n\nPilih bahasa tujuan:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_translate_lang_keyboard()
        )

    elif data.startswith("translate_to:"):
        target = data.split(":")[1]
        ctx.user_data['ai_mode'] = 'translate'
        ctx.user_data['translate_target'] = target
        await query.edit_message_text(
            f"🌐 *Translate ke {target.upper()}*\n\nKirim teks untuk diterjemahkan:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_back_keyboard("ai_menu")
        )

    elif data == "ai:caption":
        ctx.user_data['ai_mode'] = 'caption'
        await query.edit_message_text(
            f"📝 *Caption Generator*\n\nKirim judul video:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_back_keyboard("ai_menu")
        )

    elif data == "ai:hashtags":
        ctx.user_data['ai_mode'] = 'hashtags'
        await query.edit_message_text(
            f"#️⃣ *Hashtag Generator*\n\nKirim judul/deskripsi:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_back_keyboard("ai_menu")
        )

    elif data == "ai:ask":
        ctx.user_data['ai_mode'] = 'ask'
        await query.edit_message_text(
            f"❓ *Ask AI*\n\nKirim pertanyaanmu:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_back_keyboard("ai_menu")
        )

    elif data == "ai:summarize":
        ctx.user_data['ai_mode'] = 'summarize'
        await query.edit_message_text(
            f"📋 *Summarize*\n\nKirim teks panjang untuk diringkas:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_back_keyboard("ai_menu")
        )

    # ===== SHOP & PREMIUM =====
    elif data == "shop":
        await query.edit_message_text(
            build_shop(user.id),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_shop_keyboard()
        )

    elif data == "premium":
        is_prem = db.is_premium(user.id)
        await query.edit_message_text(
            build_premium(user.id),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_premium_keyboard(is_prem)
        )

    elif data == "buy_premium_coins":
        await query.edit_message_text(
            f"{E['premium']} *Beli Premium dengan Coins:*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_buy_premium_coins_keyboard()
        )

    elif data.startswith("buy_plan:"):
        plan_id = data.split(":")[1]
        success, msg, order = monetization.create_order(user.id, plan_id)

        if success and order:
            await query.edit_message_text(
                f"{E['money']} *Order Created*\n\nOrder: `{order.order_id}`\nTotal: Rp {order.amount:,}\n\n⚠️ Demo mode - pembayaran tidak aktif",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_payment_keyboard(order.order_id, order.payment_url)
            )
        else:
            await query.edit_message_text(f"{E['error']} {msg}", parse_mode=ParseMode.MARKDOWN, reply_markup=get_home_keyboard())

    elif data.startswith("buy:"):
        item_id = data.split(":")[1]
        success, msg = monetization.buy_with_coins(user.id, item_id)

        if success:
            await query.edit_message_text(
                f"{E['success']} *Pembelian Berhasil!*\n\n{msg}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_home_keyboard()
            )
        else:
            await query.edit_message_text(
                f"{E['error']} {msg}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_shop_keyboard()
            )

    elif data.startswith("check_payment:"):
        order_id = data.split(":")[1]
        # In demo mode, auto-confirm
        success, msg = monetization.confirm_payment(order_id)
        if success:
            await query.edit_message_text(
                f"{E['success']} *Pembayaran Berhasil!*\n\nTerima kasih!",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_home_keyboard()
            )
        else:
            await query.edit_message_text(f"{E['error']} {msg}", parse_mode=ParseMode.MARKDOWN)

    elif data == "cancel_order":
        await query.edit_message_text(
            f"{E['error']} Order dibatalkan.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_home_keyboard()
        )

    # ===== FEEDBACK =====
    elif data == "feedback":
        ctx.user_data['awaiting_feedback'] = True
        await query.edit_message_text(
            f"{E['feedback']} *FEEDBACK*\n\nKirim saran, kritik, atau laporan bug:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_feedback_keyboard()
        )

    # ===== ADMIN =====
    elif data == "admin:panel":
        if not is_admin(user.id):
            return
        await query.edit_message_text(
            build_admin_panel(),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_admin_keyboard()
        )

    elif data == "admin:stats":
        if not is_admin(user.id):
            return
        await query.edit_message_text(
            build_admin_stats(),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_admin_back_keyboard()
        )

    elif data == "admin:revenue":
        if not is_admin(user.id):
            return
        await query.edit_message_text(
            build_revenue_stats(),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_admin_back_keyboard()
        )

    elif data.startswith("admin:users:"):
        if not is_admin(user.id):
            return
        page = int(data.split(":")[2])
        await show_admin_users(query, page)

    elif data == "admin:broadcast":
        if not is_admin(user.id):
            return
        ctx.user_data['awaiting_broadcast'] = True
        await query.edit_message_text(
            f"{E['broadcast']} Kirim pesan broadcast:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_admin_back_keyboard()
        )

    elif data == "broadcast:send":
        if not is_admin(user.id):
            return
        await do_broadcast(query, ctx)

    elif data == "admin:ban":
        if not is_admin(user.id):
            return
        ctx.user_data['awaiting_ban'] = True
        await query.edit_message_text(
            f"{E['ban']} Kirim User ID untuk ban/unban:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_admin_back_keyboard()
        )

    elif data.startswith("admin:toggleban:"):
        if not is_admin(user.id):
            return
        target_id = int(data.split(":")[2])
        if db.is_banned(target_id):
            db.unban_user(target_id)
            await query.edit_message_text(f"{E['success']} User `{target_id}` unbanned!", parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_back_keyboard())
        else:
            db.ban_user(target_id)
            await query.edit_message_text(f"{E['success']} User `{target_id}` banned!", parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_back_keyboard())

    elif data.startswith("admin:togglepremium:"):
        if not is_admin(user.id):
            return
        target_id = int(data.split(":")[2])
        if db.is_premium(target_id):
            db.remove_premium(target_id)
            await query.edit_message_text(f"{E['success']} Premium removed from `{target_id}`!", parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_back_keyboard())
        else:
            db.set_premium(target_id, 30)
            await query.edit_message_text(f"{E['success']} Premium given to `{target_id}`!", parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_back_keyboard())

    elif data.startswith("admin:givecoins:"):
        if not is_admin(user.id):
            return
        target_id = int(data.split(":")[2])
        ctx.user_data['give_coins_to'] = target_id
        await query.edit_message_text(
            f"{E['coin']} Kirim jumlah coins untuk user `{target_id}`:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_admin_back_keyboard()
        )

    elif data == "admin:maintenance":
        if not is_admin(user.id):
            return
        Config.MAINTENANCE_MODE = not Config.MAINTENANCE_MODE
        status = "ON" if Config.MAINTENANCE_MODE else "OFF"
        await query.edit_message_text(
            f"🔧 Maintenance: *{status}*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_admin_back_keyboard()
        )

    elif data == "admin:backup":
        if not is_admin(user.id):
            return
        try:
            from config import Config as C
            with open(C.DATABASE_PATH, 'rb') as f:
                await query.message.reply_document(document=f, filename=f"backup_{get_timestamp()}.db")
            await query.edit_message_text(f"{E['success']} Backup sent!", parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_back_keyboard())
        except Exception as e:
            await query.edit_message_text(f"{E['error']} Error: {e}")

    elif data == "admin:export":
        if not is_admin(user.id):
            return
        await query.edit_message_text(
            f"{E['export']} *Export Data:*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_export_keyboard()
        )

    elif data == "export:users":
        if not is_admin(user.id):
            return
        csv_file = analytics.export_users_csv()
        await query.message.reply_document(document=csv_file, filename=f"users_{get_timestamp()}.csv")
        await query.edit_message_text(f"{E['success']} Export sent!", parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_back_keyboard())

    elif data == "export:downloads":
        if not is_admin(user.id):
            return
        csv_file = analytics.export_downloads_csv(30)
        await query.message.reply_document(document=csv_file, filename=f"downloads_{get_timestamp()}.csv")
        await query.edit_message_text(f"{E['success']} Export sent!", parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_back_keyboard())

    elif data == "export:report":
        if not is_admin(user.id):
            return
        report = analytics.generate_report()
        await query.edit_message_text(report, parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_back_keyboard())

# ==================== HELPER HANDLERS ====================

async def show_history(query, user_id: int, page: int):
    """Show history page"""
    per_page = 5
    offset = (page - 1) * per_page

    items = db.get_user_history(user_id, per_page, offset)
    total = db.get_user_history_count(user_id)
    total_pages = max(1, (total + per_page - 1) // per_page)

    if not items:
        text = f"{E['history']} *HISTORY*\n\nBelum ada history."
    else:
        text = f"{E['history']} *HISTORY* ({total})\n\n"
        for i, item in enumerate(items, 1):
            p_emoji = E.get(item['platform'], '📥')
            text += f"{i}. {p_emoji} {item['platform'].title()}\n"
            text += f"   └ {truncate(item['title'], 25)}\n"

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_history_keyboard(page, total_pages, bool(items))
    )


async def show_admin_users(query, page: int):
    """Show admin users list"""
    users, total = db.get_users_paginated(page, 10)
    total_pages = max(1, (total + 9) // 10)

    text = f"{E['users']} *USERS* ({total})\n\n"
    for u in users:
        status = f"{E['ban']}" if u.is_banned else f"{E['premium']}" if u.is_premium else ""
        text += f"• `{u.user_id}` - {u.first_name or 'N/A'} {status}\n"

    text += f"\nPage {page}/{total_pages}"

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_admin_users_keyboard(page, total_pages)
    )


async def show_platform_help(query, platform: str, user_id: int):
    """Show platform help"""
    helps = {
        "tiktok": f"{E['tiktok']} *TikTok*\n\nDownload video HD, SD, dan audio MP3.\nTanpa watermark!",
        "instagram": f"{E['instagram']} *Instagram*\n\nDownload Reels, Post, Stories.\nAkun harus public.",
        "twitter": f"{E['twitter']} *Twitter/X*\n\nDownload video dengan berbagai kualitas.",
    }

    await query.edit_message_text(
        helps.get(platform, "Unknown"),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_home_keyboard()
    )


async def do_broadcast(query, ctx):
    """Execute broadcast"""
    message = ctx.user_data.get('broadcast_message', '')
    if not message:
        await query.edit_message_text(f"{E['error']} No message!")
        return

    user_ids = db.get_all_user_ids()
    sent, failed = 0, 0

    await query.edit_message_text(f"{E['loading']} Broadcasting to {len(user_ids)} users...")

    for uid in user_ids:
        try:
            await ctx.bot.send_message(uid, message, parse_mode=ParseMode.MARKDOWN)
            sent += 1
        except:
            failed += 1
        if sent % 30 == 0:
            await asyncio.sleep(1)

    db.add_broadcast(query.from_user.id, message, sent, failed)
    ctx.user_data.pop('broadcast_message', None)

    await query.edit_message_text(
        f"{E['success']} Broadcast selesai!\n\n✅ Sent: {sent}\n❌ Failed: {failed}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_admin_back_keyboard()
    )


async def handle_download(query, ctx, media_type: str, quality: str):
    """Handle download"""
    pending = ctx.user_data.get('pending', {})
    url = pending.get('url')
    platform = pending.get('platform')
    user_id = query.from_user.id

    if not url or not platform:
        await query.edit_message_text(
            build_error(user_id, "Session expired"),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_home_keyboard()
        )
        return

    await query.edit_message_text(build_processing(platform), parse_mode=ParseMode.MARKDOWN)
    await process_download(query.message, ctx, user_id, platform, url, media_type, quality)
    ctx.user_data.pop('pending', None)


# ==================== MESSAGE HANDLER ====================

async def message_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle all text messages"""
    user = update.effective_user
    text = update.message.text
    lang = get_lang(user.id)

    # Check maintenance & banned
    if Config.MAINTENANCE_MODE and not is_admin(user.id):
        await update.message.reply_text(build_maintenance(), parse_mode=ParseMode.MARKDOWN)
        return

    if db.is_banned(user.id):
        await update.message.reply_text(build_banned(), parse_mode=ParseMode.MARKDOWN)
        return

    # Add user
    db.add_user(user.id, user.username or "", user.first_name or "")

    # ===== ADMIN INPUTS =====
    if ctx.user_data.get('awaiting_broadcast') and is_admin(user.id):
        ctx.user_data['broadcast_message'] = text
        ctx.user_data['awaiting_broadcast'] = False
        user_count = len(db.get_all_user_ids())
        await update.message.reply_text(
            f"{E['broadcast']} *Preview:*\n\n{text}\n\nKirim ke {user_count} users?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_broadcast_confirm_keyboard()
        )
        return

    if ctx.user_data.get('awaiting_ban') and is_admin(user.id):
        ctx.user_data['awaiting_ban'] = False
        try:
            target_id = int(text.strip())
            if db.is_banned(target_id):
                db.unban_user(target_id)
                await update.message.reply_text(f"{E['success']} User `{target_id}` unbanned!", parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_back_keyboard())
            else:
                db.ban_user(target_id)
                await update.message.reply_text(f"{E['success']} User `{target_id}` banned!", parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_back_keyboard())
        except:
            await update.message.reply_text(f"{E['error']} Invalid ID!")
        return

    if ctx.user_data.get('give_coins_to') and is_admin(user.id):
        target_id = ctx.user_data.pop('give_coins_to')
        try:
            coins = int(text.strip())
            gamification.add_coins(target_id, coins)
            await update.message.reply_text(f"{E['success']} Gave {coins} coins to `{target_id}`!", parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_back_keyboard())
        except:
            await update.message.reply_text(f"{E['error']} Invalid amount!")
        return

    # ===== USER INPUTS =====
    if ctx.user_data.get('awaiting_feedback'):
        ctx.user_data['awaiting_feedback'] = False
        db.add_feedback(user.id, text)

        # Notify admins
        for admin_id in Config.ADMIN_IDS:
            try:
                await ctx.bot.send_message(admin_id, f"{E['feedback']} *Feedback dari* {user.first_name} (`{user.id}`):\n\n{text}", parse_mode=ParseMode.MARKDOWN)
            except:
                pass

        # Give achievement
        gamification.check_achievements(user.id)

        await update.message.reply_text(f"{E['success']} Terima kasih atas feedbacknya!", reply_markup=get_home_keyboard())
        return

    if ctx.user_data.get('awaiting_referral'):
        ctx.user_data['awaiting_referral'] = False
        success, msg = gamification.apply_referral(user.id, text.strip())
        emoji = E['success'] if success else E['error']
        await update.message.reply_text(f"{emoji} {msg}", reply_markup=get_home_keyboard())
        return

    # ===== AI INPUTS =====
    ai_mode = ctx.user_data.get('ai_mode')
    if ai_mode:
        ctx.user_data.pop('ai_mode', None)

        await update.message.reply_text(f"{E['loading']} AI sedang memproses...", parse_mode=ParseMode.MARKDOWN)

        if ai_mode == 'chat':
            result = await ai_features.chat(text)
        elif ai_mode == 'translate':
            target = ctx.user_data.pop('translate_target', 'en')
            result = await free_ai.translate_free(text, target)
        elif ai_mode == 'caption':
            result = await ai_features.generate_caption(text, "", "social media")
        elif ai_mode == 'hashtags':
            result = await ai_features.generate_hashtags(text, "social media")
        elif ai_mode == 'ask':
            result = await ai_features.ask_question(text)
        elif ai_mode == 'summarize':
            result = await ai_features.summarize(text)
        else:
            result = type('obj', (object,), {'success': False, 'error': 'Unknown mode'})()

        if result.success:
            await update.message.reply_text(
                f"{E['ai']} *AI Response:*\n\n{result.content}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_ai_menu_keyboard()
            )
        else:
            await update.message.reply_text(
                f"{E['error']} {result.error or 'AI tidak tersedia'}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_ai_menu_keyboard()
            )
        return

    # ===== RATE LIMIT =====
    allowed, wait = rate_limiter.check_rate_limit(user.id)
    if not allowed:
        await update.message.reply_text(f"{E['warning']} Terlalu cepat! Tunggu {wait} detik.", parse_mode=ParseMode.MARKDOWN)
        return

    # ===== EXTRACT URL =====
    url = extract_url(text)
    if not url:
        await update.message.reply_text(f"{E['warning']} Kirim link TikTok/Instagram/Twitter!", parse_mode=ParseMode.MARKDOWN)
        return

    platform = detect_platform(url)
    if not platform:
        await update.message.reply_text(build_error(user.id, "Platform tidak didukung"), parse_mode=ParseMode.MARKDOWN)
        return

    # ===== DAILY LIMIT =====
    is_prem = db.is_premium(user.id)
    allowed, current, limit = daily_limiter.check_daily_limit(user.id, is_prem)
    if not allowed:
        await update.message.reply_text(
            f"{E['limit']} Limit harian tercapai ({limit})!\n\nUpgrade ke Premium untuk lebih banyak.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_premium_keyboard(is_prem)
        )
        return

    # ===== SAVE PENDING =====
    ctx.user_data['pending'] = {'url': url, 'platform': platform}

    # ===== CHECK QUALITY MODE =====
    quality_mode = db.get_quality_mode(user.id)

    if quality_mode == 'auto':
        processing = await update.message.reply_text(build_processing(platform), parse_mode=ParseMode.MARKDOWN)
        await process_download(processing, ctx, user.id, platform, url, "video", "best")
    else:
        await update.message.reply_text(
            f"{E['quality']} *{platform.title()}*\n\n{E['link']} `{truncate(url, 35)}`",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_quick_or_quality_keyboard()
        )


# ==================== DOWNLOAD PROCESSOR ====================

async def process_download(message, ctx, user_id: int, platform: str, url: str, media_type: str, quality: str):
    """Process download"""
    is_prem = db.is_premium(user_id)
    from config import Config as C
    max_size = C.PREMIUM_MAX_FILE_SIZE if is_prem else C.MAX_FILE_SIZE

    try:
        if platform == "tiktok":
            audio_only = media_type == "audio"
            result = await tiktok_dl.download(url, audio_only=audio_only)

            if result.success:
                file_path = result.audio_path if audio_only else result.video_path
                file_size = os.path.getsize(file_path) if file_path and os.path.exists(file_path) else 0

                if file_size > max_size * 1024 * 1024:
                    cleanup_file(file_path)
                    await message.edit_text(build_error(user_id, f"File terlalu besar ({format_size(file_size)})"), parse_mode=ParseMode.MARKDOWN)
                    return

                # Add XP & record
                xp_gained, leveled_up = gamification.add_xp(user_id, C.XP_PER_DOWNLOAD, "download")
                daily_limiter.increment(user_id)
                db.add_download(user_id, platform, url, media_type, quality, result.title or "", result.author or "", file_size)

                caption = build_success(platform, result.title or "TikTok", result.author or "Unknown",
                                        quality=quality, file_size=file_size, duration=result.duration,
                                        views=result.views, likes=result.likes, xp_gained=C.XP_PER_DOWNLOAD)

                if audio_only:
                    with open(file_path, 'rb') as f:
                        await message.reply_audio(audio=f, title=result.title, performer=result.author,
                                                  caption=caption, parse_mode=ParseMode.MARKDOWN)
                else:
                    with open(file_path, 'rb') as f:
                        await message.reply_video(video=f, caption=caption, parse_mode=ParseMode.MARKDOWN, supports_streaming=True)

                cleanup_file(file_path)
                await message.edit_text(f"{E['success']} Download selesai!")

                # Check achievements
                new_ach = gamification.check_achievements(user_id)
                for ach in new_ach:
                    await message.reply_text(f"{E['achievement']} *{ach.name}* unlocked! +{ach.xp} XP", parse_mode=ParseMode.MARKDOWN)

                if leveled_up:
                    level_info = gamification.get_level_info(user_id)
                    await message.reply_text(f"🎉 *LEVEL UP!* Level {level_info.level} - {level_info.name}", parse_mode=ParseMode.MARKDOWN)
            else:
                await message.edit_text(build_error(user_id, result.error or "Gagal"), parse_mode=ParseMode.MARKDOWN)

        elif platform == "instagram":
            result = await instagram_dl.download(url)

            if result.success:
                gamification.add_xp(user_id, Config.XP_PER_DOWNLOAD, "download")
                daily_limiter.increment(user_id)
                db.add_download(user_id, platform, url, result.media_type, quality, result.title or "", result.author or "", 0)

                if result.video_paths:
                    for vp in result.video_paths:
                        with open(vp, 'rb') as f:
                            await message.reply_video(video=f, caption=f"{E['success']} Instagram Video", supports_streaming=True)
                        cleanup_file(vp)

                if result.image_paths:
                    for ip in result.image_paths:
                        with open(ip, 'rb') as f:
                            await message.reply_photo(photo=f)
                        cleanup_file(ip)

                await message.edit_text(f"{E['success']} Download selesai! +{Config.XP_PER_DOWNLOAD} XP")
                gamification.check_achievements(user_id)
            else:
                await message.edit_text(build_error(user_id, result.error or "Gagal"), parse_mode=ParseMode.MARKDOWN)

        elif platform == "twitter":
            result = await twitter_dl.download(url)

            if result.success:
                gamification.add_xp(user_id, Config.XP_PER_DOWNLOAD, "download")
                daily_limiter.increment(user_id)
                db.add_download(user_id, platform, url, result.media_type, quality, result.title or "", result.author or "", 0)

                if result.video_path:
                    with open(result.video_path, 'rb') as f:
                        await message.reply_video(video=f, caption=f"{E['success']} Twitter Video", supports_streaming=True)
                    cleanup_file(result.video_path)

                if result.image_paths:
                    for ip in result.image_paths:
                        with open(ip, 'rb') as f:
                            await message.reply_photo(photo=f)
                        cleanup_file(ip)

                await message.edit_text(f"{E['success']} Download selesai! +{Config.XP_PER_DOWNLOAD} XP")
                gamification.check_achievements(user_id)
            else:
                await message.edit_text(build_error(user_id, result.error or "Gagal"), parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(f"Download error: {e}")
        await message.edit_text(build_error(user_id, str(e)), parse_mode=ParseMode.MARKDOWN)


# ==================== ERROR HANDLER ====================

async def error_handler(update: object, ctx: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {ctx.error}")


# ==================== MAIN ====================

def main():
    if not Config.BOT_TOKEN:
        logger.error("BOT_TOKEN not found!")
        return

    app = Application.builder().token(Config.BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("daily", cmd_daily))
    app.add_handler(CommandHandler("spin", cmd_spin))
    app.add_handler(CommandHandler("referral", cmd_referral))
    app.add_handler(CommandHandler("shop", cmd_shop))
    app.add_handler(CommandHandler("premium", cmd_premium))
    app.add_handler(CommandHandler("ai", cmd_ai))
    app.add_handler(CommandHandler("leaderboard", cmd_leaderboard))
    app.add_handler(CommandHandler("admin", cmd_admin))

    # Callbacks & Messages
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.add_error_handler(error_handler)

    logger.info("Bot started!")

    print(f"""
╔═══════════════════════════════════════════════════════════╗
║         🚀 MEDIA DOWNLOADER BOT v2.0 STARTED 🚀           ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  ✅ Download: TikTok, Instagram, Twitter                  ║
║  ✅ AI Features: Chat, Translate, Caption, Hashtags       ║
║  ✅ Gamification: XP, Levels, Achievements, Leaderboard   ║
║  ✅ Monetization: Premium, Coins, Shop                    ║
║  ✅ Admin: Stats, Users, Broadcast, Revenue               ║
║                                                           ║
║  📱 Press Ctrl+C to stop                                  ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()