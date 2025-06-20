import os
import time
import random
import threading
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler
from datetime import datetime
from pytz import timezone

# --- Configurations ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
DEFAULT_INTERVAL = int(os.getenv("DEFAULT_INTERVAL", 300))  # default 5 mins
TIMEZONE = timezone('Asia/Dhaka')

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dispatcher = Dispatcher(bot=bot, update_queue=None, workers=4, use_context=True)

# --- Signal Message Generator ---
assets = ['EUR/USD', 'CHF/USD', 'NZD/USD', 'CAD/USD', 'AUD/USD', 'GBP/USD', 'USD/JPY']
directions = ['UP', 'DOWN']
interval_seconds = DEFAULT_INTERVAL
interval_lock = threading.Lock()
interval_updated = threading.Event()
interval_updated.set()

def send_signal_loop():
    while True:
        try:
            asset = random.choice(assets)
            direction = random.choice(directions)
            now = datetime.now(TIMEZONE).strftime('%I:%M %p')

            message = (
                "🚨 *Trade Signal Alert*\n\n"
                f"💹 Pair: `{asset}`\n"
                f"📊 Direction: {'📈' if direction == 'UP' else '📉'} *{direction}*\n"
                f"🕒 Time: {now}\n"
                f"⏱ Duration: 1 Minute\n\n"
                "⚠️ Place this trade manually on *Quotex!*"
            )

            bot.send_message(chat_id=GROUP_ID, text=message, parse_mode='Markdown')
            logger.info(f"Signal sent: {message}")

        except Exception as e:
            logger.error(f"Error sending signal: {e}")

        with interval_lock:
            wait = interval_seconds
        interval_updated.wait(timeout=wait)
        interval_updated.clear()

# --- Commands ---
def start(update: Update, context):
    msg = (
        "🌟 *Welcome to Elite Quotex Signal Bot!*\n\n"
        "This bot sends 1-minute trading signals every 5 minutes by default.\n"
        "You can change the interval using `/timeset <seconds>`.\n\n"
        "Example: `/timeset 120`\n\n"
        "✅ All signals are posted automatically in the group."
    )
    update.message.reply_text(msg, parse_mode='Markdown')

def timeset(update: Update, context):
    global interval_seconds
    try:
        parts = update.message.text.strip().split()
        if len(parts) >= 2:
            new_time = int(parts[1])
            with interval_lock:
                interval_seconds = new_time
            interval_updated.set()
            update.message.reply_text(f"✅ Signal interval updated to {new_time} seconds.")
            logger.info(f"Interval changed to {new_time} seconds")
        else:
            raise ValueError
    except Exception:
        update.message.reply_text("❌ Invalid format. Use: /timeset 120")

# --- Webhook Setup ---
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("timeset", timeset))

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK", 200

@app.route("/", methods=["GET"])
def home():
    return "Elite Quotex Signal Bot is running.", 200

# --- Start signal thread ---
threading.Thread(target=send_signal_loop, daemon=True).start()

# --- Start Flask App ---
if __name__ == '__main__':
    PORT = int(os.getenv("PORT", 8080))
    logger.info("Starting Elite Quotex Bot server...")
    app.run(host="0.0.0.0", port=PORT)
