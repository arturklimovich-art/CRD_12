import os
import aiohttp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

app = Application.builder().token(TELEGRAM_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Engineer A v2 - Connected to AI Agent!")

async def health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://engineer_b_api:8000/system/health") as response:
                data = await response.json()
                await update.message.reply_text(f"🏥 System: {data['status']}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://engineer_b_api:8000/agent/memory") as response:
                data = await response.json()
                await update.message.reply_text(f"🧠 Memory: {data['status']}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task = update.message.text
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post("http://engineer_b_api:8000/agent/analyze", json={"task": task}) as response:
                data = await response.json()
                await update.message.reply_text(f"🎯 {data['analysis']}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("health", health))
app.add_handler(CommandHandler("memory", memory))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("🤖 Engineer A Bot v2 starting...")
app.run_polling()
