import logging
import requests
import xml.etree.ElementTree as ET
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8601899020:AAF6xdQ9Uc2vUqE2J3g_B_iynLoVa83bfGQ"

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Stock News Bot is running on cloud!")

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rss_url = "https://news.google.com/rss/search?q=Indian+stock+market+OR+NIFTY+OR+SENSEX&hl=en-IN&gl=IN&ceid=IN:en"

    try:
        response = requests.get(rss_url)
        root = ET.fromstring(response.content)

        items = root.findall(".//item")[:5]

        if not items:
            await update.message.reply_text("No news found.")
            return

        message = "📰 Latest Indian Stock Market News:\n\n"

        for item in items:
            title = item.find("title").text
            link = item.find("link").text
            message += f"🔹 {title}\n{link}\n\n"

        await update.message.reply_text(message)

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("news", news))

    print("Bot Running on Cloud...")
    app.run_polling()

if __name__ == "__main__":
    main()
