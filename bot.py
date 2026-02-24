import logging
import os
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = "8601899020:AAF6xdQ9Uc2vUqE2J3g_B_iynLoVa83bfGQ"

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is running on cloud!")

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api_key = os.getenv("c5fb0e2299814a2aa8b79cbf26cbab74")

    url = "https://newsapi.org/v2/top-headlines"

    params = {
        "country": "in",
        "category": "business",
        "apiKey": api_key
    }

    response = requests.get(url, params=params)
    data = response.json()

    articles = data.get("articles", [])[:5]

    if not articles:
        await update.message.reply_text("No news found.")
        return

    message = "📰 Latest Stock Market News:\n\n"

    for article in articles:
        message += f"🔹 {article['title']}\n{article['url']}\n\n"

    await update.message.reply_text(message)

async def reply_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.reply_text(f"You said: {user_text}")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_message))

    print("Bot Running on Cloud...")
    app.run_polling()

if __name__ == "__main__":
    main()
