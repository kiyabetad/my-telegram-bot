import logging
import os
import re
import tempfile
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from yt_dlp import YoutubeDL

BOT_TOKEN = "8079991527:AAFRSFLgTkXfzCmMAkEz1rC013sH8BY648Y"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WELCOME_TEXT = "سلام! لینک یوتیوب، تیک‌تاک، توییتر، ساندکلاد، اسپاتیفای یا اینستاگرام رو بفرست تا دانلود کنم."

# regex تشخیص لینک‌ها
PATTERNS = {
    'youtube': r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/',
    'tiktok': r'(https?://)?(www\.)?tiktok\.com/',
    'twitter': r'(https?://)?(www\.)?twitter\.com/',
    'soundcloud': r'(https?://)?(www\.)?soundcloud\.com/',
    'spotify': r'(https?://)?(open\.)?spotify\.com/',
    'instagram': r'(https?://)?(www\.)?instagram\.com/'
}

# استارت
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(WELCOME_TEXT)

# دانلود همه پلتفرم‌ها با yt-dlp
async def download_media(url, chat_id, context):
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            ydl_opts = {
                'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
                'quiet': True,
                'noplaylist': True
            }
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filepath = ydl.prepare_filename(info)
            
            # ارسال فایل
            if filepath.endswith(".mp4"):
                await context.bot.send_video(chat_id=chat_id, video=open(filepath, 'rb'))
            elif filepath.endswith((".mp3", ".m4a")):
                await context.bot.send_audio(chat_id=chat_id, audio=open(filepath, 'rb'))
            else:
                await context.bot.send_document(chat_id=chat_id, document=open(filepath, 'rb'))
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            await context.bot.send_message(chat_id=chat_id, text="❌ خطا در دانلود یا پشتیبانی نشدن این لینک.")

# نرخ ارز
async def currency(update: Update, context: CallbackContext):
    text = update.message.text
    chat_id = update.message.chat_id
    match = re.search(r'(\d+)', text)
    if match:
        amount = float(match.group(1))
        try:
            r = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
            rate = r.json()['rates']['IRR']
            await update.message.reply_text(f"💵 {amount} دلار = {int(rate * amount):,} ریال")
        except:
            await update.message.reply_text("❌ خطا در دریافت نرخ ارز")

# پیام‌های دریافتی
async def handle_message(update: Update, context: CallbackContext):
    text = update.message.text
    chat_id = update.message.chat_id

    # نرخ ارز
    if "دلار" in text or "$" in text:
        await currency(update, context)
        return

    # بررسی لینک‌ها
    for name, pattern in PATTERNS.items():
        if re.search(pattern, text):
            await update.message.reply_text("در حال دانلود... لطفاً صبر کن.")
            await download_media(text, chat_id, context)
            return

    await update.message.reply_text("❌ لینک پشتیبانی نمی‌شود یا نادرست است.")

# اجرای ربات
if __name__ == '__main__':
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ ربات آماده‌ست...")
    app.run_polling()
