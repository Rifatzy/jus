import os
import asyncio
import yt_dlp
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

# Import dari file lokal
from config import Config
from database import db

# ═══════════════════════════════════════════════════════════════
# 🎨 TEMPLATES & KEYBOARDS
# ═══════════════════════════════════════════════════════════════

WELCOME_MESSAGE = """
╔══════════════════════════════════╗
║    🦁 <b>MEDIAMUNCHER BOT</b> 🦁    ║
╚══════════════════════════════════╝

🎬 <b>Bot Download Media Terlengkap!</b>

┌─────────────────────────────────┐
│  🎵 TikTok (Tanpa Watermark)    │
│  📸 Instagram Reels/Post/Story  │
│  🐦 Twitter / X                 │
│  ▶️ YouTube (Video & Shorts)    │
│  📘 Facebook Video              │
│  🎮 Dan 1500+ situs lainnya!    │
└─────────────────────────────────┘

💡 <b>Cara Pakai:</b> Kirim link saja! ✨

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ <i>Fast • Free • No Watermark</i> ⚡
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

def get_main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📖 Bantuan", callback_data="help"),
            InlineKeyboardButton("📊 Statistik Saya", callback_data="stats")
        ],
        [
            InlineKeyboardButton("ℹ️ Tentang", callback_data="about"),
            InlineKeyboardButton("❓ FAQ", callback_data="faq")
        ]
    ])

def get_back_keyboard(menu="start"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Kembali", callback_data=menu)]
    ])

# ═══════════════════════════════════════════════════════════════
# 🛠️ HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def format_duration(seconds):
    if not seconds: return "N/A"
    mins, secs = divmod(int(seconds), 60)
    hours, mins = divmod(mins, 60)
    return f"{hours}:{mins:02d}:{secs:02d}" if hours else f"{mins}:{secs:02d}"

def format_filesize(size_bytes):
    return f"{size_bytes / (1024*1024):.1f} MB" if size_bytes > 1024*1024 else f"{size_bytes / 1024:.1f} KB"

def get_platform_icon(extractor):
    icons = {'tiktok': '🎵', 'instagram': '📸', 'twitter': '🐦', 'youtube': '▶️', 'facebook': '📘'}
    return next((icon for key, icon in icons.items() if key in extractor.lower()), '🌐')

# ═══════════════════════════════════════════════════════════════
# 📦 USER COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.add_user(user.id, user.username, user.first_name, user.last_name)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            WELCOME_MESSAGE, parse_mode='HTML', reply_markup=get_main_keyboard()
        )
    else:
        await update.message.reply_text(
            WELCOME_MESSAGE, parse_mode='HTML', reply_markup=get_main_keyboard()
        )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
╔══════════════════════════════════╗
║      📖 <b>PANDUAN PENGGUNAAN</b>      ║
╚══════════════════════════════════╝

<b>🔗 Link yang Didukung:</b>
• TikTok, Instagram, Twitter/X
• YouTube, Facebook, Reddit
• Dan 1500+ situs lainnya!

<b>📌 Cara Pakai:</b>
Cukup kirim link, bot akan proses!

<b>⚠️ Batasan:</b>
• Ukuran file maks: {max_size}MB
• Limit harian: {limit} unduhan
• Konten private/berbayar tidak bisa diunduh.
""".format(max_size=Config.MAX_FILE_SIZE_MB, limit=db.get_setting("daily_limit", Config.DAILY_LIMIT))

    await update.callback_query.edit_message_text(
        text, parse_mode='HTML', reply_markup=get_back_keyboard()
    )

async def about_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
╔══════════════════════════════════╗
║      🦁 <b>TENTANG BOT</b>              ║
╚══════════════════════════════════╝

<b>📛 Nama:</b> MediaMuncher Bot
<b>🔧 Versi:</b> 3.1
<b>⚙️ Engine:</b> yt-dlp

Bot ini dibuat untuk memudahkan download media dari berbagai platform secara gratis dan tanpa watermark.
"""
    await update.callback_query.edit_message_text(
        text, parse_mode='HTML', reply_markup=get_back_keyboard()
    )

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    limit_ok, remaining = db.check_daily_limit(user_id)

    text = f"""
╔══════════════════════════════════╗
║       📊 <b>STATISTIK ANDA</b>          ║
╚══════════════════════════════════╝

👤 <b>User:</b> <code>{user_id}</code>
📥 <b>Total Unduhan:</b> {user_data.get('total_downloads', 0)}
🗓️ <b>Sisa Limit Hari Ini:</b> {remaining}/{db.get_setting("daily_limit", Config.DAILY_LIMIT)}
"""
    await update.callback_query.edit_message_text(
        text, parse_mode='HTML', reply_markup=get_back_keyboard()
    )

async def faq_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan pesan FAQ."""
    faq_text = """
    ❓ <b>Pertanyaan Umum (FAQ)</b>

    <b>T: Bot ini gratis?</b>
    J: Ya, bot ini 100% gratis dengan batas unduhan harian.

    <b>T: Kenapa unduhan saya gagal?</b>
    J: Kemungkinan besar karena kontennya bersifat pribadi (private), sudah dihapus, atau link yang Anda kirim salah.

    <b>T: Bisakah saya mengunduh video pribadi?</b>
    J: Tidak. Bot tidak dapat mengunduh konten yang memerlukan login atau akses khusus.

    <b>T: Apakah data saya aman?</b>
    J: Bot hanya menyimpan User ID Anda untuk statistik dan fitur ban. Kami tidak menyimpan riwayat unduhan atau informasi pribadi lainnya.
    """
    if update.callback_query:
        await update.callback_query.edit_message_text(faq_text, parse_mode='HTML', reply_markup=get_back_keyboard())
    else:
        await update.message.reply_text(faq_text, parse_mode='HTML', reply_markup=get_back_keyboard())

async def feedback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangani /feedback dan /bugreport."""
    user = update.effective_user
    command = update.message.text.split()[0].lower()
    report_type = "Feedback" if command == "/feedback" else "Laporan Bug"

    if not context.args:
        await update.message.reply_text(f"⚠️ Format salah. Gunakan: `{command} [pesan Anda]`", parse_mode='MarkdownV2')
        return

    message = " ".join(context.args)
    log_message = (
        f"📝 <b>{report_type} Baru</b>\n\n"
        f"<b>Dari:</b> {user.first_name} (@{user.username})\n"
        f"<b>User ID:</b> <code>{user.id}</code>\n"
        f"<b>Pesan:</b>\n{message}"
    )

    try:
        await context.bot.send_message(
            chat_id=Config.LOG_CHANNEL_ID,
            text=log_message,
            parse_mode='HTML'
        )
        await update.message.reply_text("✅ Terima kasih! Pesan Anda telah berhasil dikirim ke admin.")
    except Exception as e:
        print(f"Gagal mengirim ke log channel: {e}")
        await update.message.reply_text("❌ Maaf, terjadi kesalahan saat mengirim pesan Anda.")

# ═══════════════════════════════════════════════════════════════
# 📥 DOWNLOAD HANDLER
# ═══════════════════════════════════════════════════════════════

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    url = update.message.text.strip()

    # Update data user di DB
    db.add_user(user.id, user.username, user.first_name, user.last_name)

    # Cek maintenance mode
    if db.get_setting("maintenance_mode", False) and not Config.is_admin(user.id):
        await update.message.reply_text("🔧 Bot sedang dalam perbaikan. Coba lagi nanti.")
        return

    # Cek banned
    if db.is_banned(user.id):
        user_data = db.get_user(user.id)
        await update.message.reply_text(
            f"⛔ <b>Anda dibanned!</b>\n\nAlasan: {user_data.get('ban_reason', 'N/A')}",
            parse_mode='HTML'
        )
        return

    # Validasi URL
    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text("❌ URL tidak valid. Kirim link yang benar.")
        return

    # Cek limit harian
    limit_ok, remaining = db.check_daily_limit(user.id)
    if not limit_ok and not Config.is_admin(user.id):
        await update.message.reply_text(
            f"⚠️ <b>Limit harian tercapai!</b>\nSisa unduhan: 0/{db.get_setting('daily_limit', Config.DAILY_LIMIT)}",
            parse_mode='HTML'
        )
        return

    status_msg = await update.message.reply_text("⏳ Memproses link...", parse_mode='HTML')

    ydl_opts = {
        'outtmpl': os.path.join(Config.DOWNLOAD_PATH, '%(title)s.%(ext)s'),
        'format': 'best[ext=mp4]/bv*+ba/b', 'noplaylist': True, 'merge_output_format': 'mp4',
        'quiet': True, 'no_warnings': True,
    }

    download_id = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            title = info.get('title', 'Video')[:50]
            extractor = info.get('extractor_key', 'Unknown')
            icon = get_platform_icon(extractor)

            await status_msg.edit_text(f"📥 {icon} Mengunduh <b>{title}</b>...", parse_mode='HTML')

            ydl.download([url])
            filename = ydl.prepare_filename(info)
            file_size = os.path.getsize(filename)

            if file_size > Config.MAX_FILE_SIZE_MB * 1024 * 1024:
                await status_msg.edit_text(f"❌ File terlalu besar (> {Config.MAX_FILE_SIZE_MB}MB).")
                db.add_download(user.id, url, extractor, title, file_size, "failed", "File too large")
                return

            caption = f"{icon} <b>{title}</b>"

            # Kirim file
            with open(filename, 'rb') as file:
                if info.get('ext') in ['mp4', 'webm']:
                    await update.message.reply_video(video=file, caption=caption, parse_mode='HTML')
                elif info.get('ext') in ['mp3', 'm4a', 'ogg']:
                    await update.message.reply_audio(audio=file, caption=caption, parse_mode='HTML')
                else:
                    await update.message.reply_document(document=file, caption=caption, parse_mode='HTML')

            # Update statistik dan simpan history
            db.update_download_count(user.id)
            download_id = db.add_download(user.id, url, extractor, title, file_size, "success")

            await status_msg.delete()

    except Exception as e:
        error_msg = str(e)[:200]
        await status_msg.edit_text(f"❌ Gagal memproses link.\n\n<code>{error_msg}</code>", parse_mode='HTML')
        db.add_download(user.id, url, "Unknown", "Unknown", 0, "failed", error_msg)

    finally:
        if 'filename' in locals() and os.path.exists(filename):
            os.remove(filename)

    # Kirim permintaan rating jika download berhasil
    if download_id:
        rating_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"⭐ {i}", callback_data=f"rate_{download_id}_{i}") for i in range(1, 6)]
        ])
        await update.message.reply_text("👇 Beri nilai untuk unduhan ini:", reply_markup=rating_keyboard)

# ═══════════════════════════════════════════════════════════════
# 📞 CALLBACK HANDLERS
# ═══════════════════════════════════════════════════════════════

async def main_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "start": await start(update, context)
    elif query.data == "help": await help_cmd(update, context)
    elif query.data == "about": await about_cmd(update, context)
    elif query.data == "stats": await stats_cmd(update, context)

async def rating_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("✅ Terima kasih atas penilaian Anda!")

    _, download_id, rating = query.data.split("_")
    db.update_download_rating(int(download_id), int(rating))

    await query.edit_message_text(f"🙏 Anda memberikan <b>{'⭐'*int(rating)}</b>. Terima kasih!", parse_mode='HTML')


# ═══════════════════════════════════════════════════════════════
# 🚀 MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    try:
        Config.validate()
    except ValueError as e:
        print(e)
        return

    app = Application.builder().token(Config.BOT_TOKEN).build()

    # Handler
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("faq", faq_command))
    app.add_handler(CommandHandler("feedback", feedback_handler))
    app.add_handler(CommandHandler("bugreport", feedback_handler))
    app.add_handler(CallbackQueryHandler(main_callback_handler, pattern="^(start|help|about|stats|faq)$"))
    app.add_handler(CallbackQueryHandler(rating_callback_handler, pattern=r"^rate_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download))

    # Import dan daftarkan admin handler
    from admin import add_admin_handlers
    add_admin_handlers(app)

    print("✅ Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()