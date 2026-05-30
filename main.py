from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

import json
import os
import re

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise Exception("BOT_TOKEN is not set in environment variables!")

BOT_USERNAME = "TTjon_123_bot"
CHANNEL_USERNAME = "@iiiiiiiitbdux"
CHANNEL_LINK = "https://t.me/iiiiiiiitbdux"

WARN_FILE = "warnings.json"

warnings = {}

# =========================
# LOAD / SAVE WARNINGS
# =========================

if os.path.exists(WARN_FILE):
    try:
        with open(WARN_FILE, "r") as f:
            warnings = json.load(f)
    except:
        warnings = {}

def save_warnings():
    try:
        with open(WARN_FILE, "w") as f:
            json.dump(warnings, f)
    except Exception as e:
        print("SAVE ERROR:", e)

# =========================
# CHECK MEMBERSHIP
# =========================

async def is_member(user_id, context):
    try:
        m = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return m.status in ["member", "administrator", "creator"]
    except:
        return False

# =========================
# CHECK ADMIN
# =========================

async def is_admin(chat_id, user_id, context):
    try:
        m = await context.bot.get_chat_member(chat_id, user_id)
        return m.status in ["administrator", "creator"]
    except:
        return False

# =========================
# START COMMAND
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    keyboard = [
        [InlineKeyboardButton("📢 عضویت کانال", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ عضو شدم", callback_data="check_join")],
        [InlineKeyboardButton("➕ افزودن به گروه", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")]
    ]

    await update.message.reply_text(
        f"👋 سلام {user.first_name}\n\nبرای استفاده اول عضو کانال شو 😎",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =========================
# BUTTON HANDLER
# =========================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    user_id = q.from_user.id

    if q.data == "check_join":
        ok = await is_member(user_id, context)

        if ok:
            await q.message.reply_text("✅ تایید شد 😎🔥")
        else:
            await q.answer("❌ هنوز عضو نشدی", show_alert=True)

# =========================
# WELCOME MESSAGE
# =========================

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for u in update.message.new_chat_members:
        await update.message.reply_text(
            f"👋 خوش اومدی {u.first_name} 😎\nقوانین رو رعایت کن ⚡"
        )

# =========================
# MAIN HANDLER (ANTI-LINK + WARN)
# =========================

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
        return

    if update.effective_chat.type == "private":
        return

    user = update.effective_user
    uid = str(user.id)
    chat_id = update.effective_chat.id
    text = update.message.text.lower()

    # ignore admins
    if await is_admin(chat_id, user.id, context):
        return

    # anti-link
    link_pattern = r"(https?://|t\.me/|telegram\.me/|www\.|@\w+)"

    if re.search(link_pattern, text):

        warnings[uid] = warnings.get(uid, 0) + 1
        save_warnings()

        try:
            await update.message.delete()
        except:
            pass

        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ لینک ممنوع\n⚠️ هشدار: {warnings[uid]}/3"
        )

        if warnings[uid] >= 3:
            try:
                await context.bot.ban_chat_member(chat_id, user.id)
            except:
                pass

            warnings.pop(uid, None)
            save_warnings()

        return

# =========================
# RUN BOT
# =========================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler))

print("BOT RUNNING 😎")

app.run_polling()