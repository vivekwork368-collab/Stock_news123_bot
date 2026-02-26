import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN is not set!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Bot is working ✅")

def main():
    app = Application.builder().token(TOKEN).build()  # new API
    app.add_handler(CommandHandler("start", start))
    print("Bot running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    (main())
