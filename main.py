import os
import random
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from pytz import timezone

# --- Configurations ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
DEFAULT_INTERVAL = int(os.getenv("DEFAULT_INTERVAL", 300))
TIMEZONE = timezone('Asia/Dhaka')

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# --- Scheduler Setup ---
scheduler = BackgroundScheduler(timezone=TIMEZONE)
interval_seconds = DEFAULT_INTERVAL

# --- Signal Generator ---
assets = ['EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD']
directions = ['UP', 'DOWN']

def send_signal():
    asset = random.choice(assets)
    direction = random.choice(directions)
    now = datetime.now(TIMEZONE).strftime('%I:%M %p')

    message = (
        "🚨 *Trade Signal Alert*\n\n"
        f"Pair: `{asset}`\n"
        f"Direction: {'📈' if direction == 'UP' else '📉'} {direction}\n"
        f"Time: {now}\n"
        "Duration: 1 Minute\n\n"
        "⚠️ Place this trade manually on Quotex!"
    )
    bot.send_message(chat_id=GROUP_ID, text=message, parse_mode="Markdown")

job = scheduler.add_job(send_signal, 'interval', seconds=interval_seconds, id='send_signal')
scheduler.start()

# --- Handlers ---
def start(update: Update, context):
    welcome = (
        "🌟 *Welcome to Elite Quotex Signal Bot!*\n\n"
        "This bot sends 1-minute trading signals every 5 minutes by default.\n"
        "You can change the interval using `/timeset <seconds>`.\n\n"
        "Example: `/timeset 120` to receive signals every 2 minutes.\n\n"
        "✅ All signals are posted automatically in the group."
    )
    update.message.reply_text(welcome, parse_mode='Markdown')


def help_command(update: Update, context):
    help_text = (
        "ℹ️ *Available Commands:*\n\n"
        "/start - Welcome message\n"
        "/help - Show this help menu\n"
        "/about - About this bot\n"
        "/timeset <seconds> - Change signal interval (admins only)"
    )
    update.message.reply_text(help_text, parse_mode='Markdown')


def about(update: Update, context):
    about_text = (
        "ℹ️ *About Elite Quotex Signal Bot*\n\n"
        "🔹 Developer: @thenoman_dev\n"
        "🔹 Purpose: Provides automated Quotex trading signals\n"
        "🔹 Default Interval: 5 minutes (customizable with /timeset)\n\n"
        "⚠️ Disclaimer: Signals are for educational purposes only. "
        "Trade at your own risk."
    )
    update.message.reply_text(about_text, parse_mode='Markdown')


def timeset(update: Update, context):
    global interval_seconds
    try:
        user_id = update.effective_user.id
        chat_member = bot.get_chat_member(GROUP_ID, user_id)

        if chat_member.status not in ["administrator", "creator"]:
            update.message.reply_text("❌ Only group admins can change the signal interval.")
            return

        new_time = int(context.args[0])
        interval_seconds = new_time
        scheduler.reschedule_job('send_signal', trigger='interval', seconds=interval_seconds)
        update.message.reply_text(f"✅ Signal interval updated to {interval_seconds} seconds.")
    except (IndexError, ValueError):
        update.message.reply_text("❌ Invalid format. Use: /timeset 120")


# --- Dispatcher Setup ---
dispatcher = Dispatcher(bot=bot, update_queue=None, workers=4, use_context=True)
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("help", help_command))
dispatcher.add_handler(CommandHandler("about", about))
dispatcher.add_handler(CommandHandler("timeset", timeset))

# --- Webhook route ---
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK", 200

# --- Root for GET requests (optional health check) ---
@app.route("/", methods=["GET"])
def index():
    return "✅ Elite Quotex Signal Bot is running."

# --- Local testing (if needed) ---
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
