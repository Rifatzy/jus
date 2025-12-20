import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, Application

from config import Config
from database import db
from functools import wraps

# ═══════════════════════════════════════════════════════════════
# 🔒 DECORATORS
# ═══════════════════════════════════════════════════════════════

def admin_only(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if not Config.is_admin(user_id) and not db.is_admin_in_db(user_id):
            await update.message.reply_text("⛔ Akses ditolak!")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

def owner_only(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not Config.is_owner(update.effective_user.id):
            await update.message.reply_text("⛔ Hanya owner yang bisa pakai perintah ini!")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

# ═══════════════════════════════════════════════════════════════
# 🎨 TEMPLATES & KEYBOARDS
# ═══════════════════════════════════════════════════════════════

ADMIN_PANEL_TEXT = """
╔══════════════════════════════════╗
║     🛡️ <b>ADMIN CONTROL PANEL</b>      ║
╚══════════════════════════════════╝

👋 Selamat datang, <b>{admin_name}</b>!

Pilih menu di bawah untuk mengelola bot.
"""

def get_admin_panel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Statistik Detail", callback_data="admin_stats")],
        [
            InlineKeyboardButton("👥 User Management", callback_data="admin_users"),
            InlineKeyboardButton(" broadcast", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton("🚫 Daftar Ban", callback_data="admin_banlist"),
            InlineKeyboardButton("⚙️ Pengaturan", callback_data="admin_settings")
        ],
        [InlineKeyboardButton("🔄 Refresh", callback_data="admin_refresh")]
    ])

# ═══════════════════════════════════════════════════════════════
# 🛡️ ADMIN COMMANDS
# ═══════════════════════════════════════════════════════════════

@admin_only
async def admin_panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.edit_message_text(
            ADMIN_PANEL_TEXT.format(admin_name=update.effective_user.first_name),
            parse_mode='HTML', reply_markup=get_admin_panel_keyboard()
        )
    else:
        await update.message.reply_text(
            ADMIN_PANEL_TEXT.format(admin_name=update.effective_user.first_name),
            parse_mode='HTML', reply_markup=get_admin_panel_keyboard()
        )

@admin_only
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ <b>Format:</b> /broadcast [pesan]")
        return

    msg = " ".join(context.args)
    user_ids = db.get_all_user_ids()

    progress_msg = await update.message.reply_text(f"📢 Memulai broadcast ke {len(user_ids)} pengguna...")

    success, failed = 0, 0
    for uid in user_ids:
        try:
            await context.bot.send_message(uid, f"📢 <b>Pesan dari Admin:</b>\n\n{msg}", parse_mode='HTML')
            success += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

    await progress_msg.edit_text(f"✅ Broadcast Selesai!\n\nBerhasil: {success}\nGagal: {failed}")

@admin_only
async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("⚠️ <b>Format:</b> /ban [user_id] [alasan]")
        return

    try:
        target_id = int(context.args[0])
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "Tanpa alasan"

        if Config.is_admin(target_id):
            await update.message.reply_text("⛔ Tidak bisa ban admin!")
            return

        db.ban_user(target_id, update.effective_user.id, reason)
        await update.message.reply_text(f"✅ Pengguna <code>{target_id}</code> berhasil diban.", parse_mode='HTML')
    except ValueError:
        await update.message.reply_text("❌ User ID harus angka.")

@admin_only
async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("⚠️ <b>Format:</b> /unban [user_id]")
        return

    try:
        target_id = int(context.args[0])
        db.unban_user(target_id)
        await update.message.reply_text(f"✅ Ban untuk pengguna <code>{target_id}</code> telah dicabut.", parse_mode='HTML')
    except ValueError:
        await update.message.reply_text("❌ User ID harus angka.")

# ═══════════════════════════════════════════════════════════════
# 📞 ADMIN CALLBACK HANDLER
# ═══════════════════════════════════════════════════════════════

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not Config.is_admin(query.from_user.id): return

    action = query.data.split('_')[-1]

    if action == "refresh":
        await admin_panel_command(update, context)
    elif action == "stats":
        stats = db.get_download_stats()
        text = f"""
📊 <b>Statistik Detail Bot</b>

- Total Pengguna: {db.get_user_count()}
- Pengguna Aktif Hari Ini: {db.get_active_users_today()}
- Total Unduhan: {stats['total']}
- Unduhan Hari Ini: {stats['today']}
"""
        await query.edit_message_text(text, parse_mode='HTML', reply_markup=get_back_keyboard("admin_panel"))

# Dan seterusnya untuk handler callback lainnya...

def get_back_keyboard(menu="admin_panel"):
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data=menu)]])


# ═══════════════════════════════════════════════════════════════
# 🚀 ADD HANDLERS TO APP
# ═══════════════════════════════════════════════════════════════

def add_admin_handlers(app: Application):
    app.add_handler(CommandHandler("admin", admin_panel_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CommandHandler("ban", ban_command))
    app.add_handler(CommandHandler("unban", unban_command))

    # Callback handler untuk semua aksi admin
    app.add_handler(CallbackQueryHandler(admin_callback_handler, pattern=r"^admin_"))
    app.add_handler(CallbackQueryHandler(admin_panel_command, pattern=r"^admin_panel$"))
