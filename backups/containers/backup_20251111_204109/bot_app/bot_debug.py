import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [BOT_DEBUG] %(message)s")
log = logging.getLogger("bot")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

async def debug_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Простой debug handler для ВСЕХ сообщений"""
    log.info(f"📨 RECEIVED MESSAGE: {update.message.text}")
    await update.message.reply_text(f"🔍 Бот получил: '{update.message.text}'")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Debug bot started! Send any message.")

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Только два простых handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ALL, debug_message))
    
    log.info("🚀 DEBUG BOT STARTED")
    application.run_polling()

if __name__ == "__main__":
    main()
