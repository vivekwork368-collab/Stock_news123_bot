import logging
import requests
import xml.etree.ElementTree as ET
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# 🔹 Replace with your real bot token
TOKEN = "8601899020:AAF6xdQ9Uc2vUqE2J3g_B_iynLoVa83bfGQ"

logging.basicConfig(level=logging.INFO)

# ✅ Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📈 Indian Stock Market News Bot is Live!\n\n"
        "Use /news to get latest market headlines."
    )

# ✅ News command
async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rss_url = "https://news.google.com/rss/search?q=Indian+stock+market+OR+NIFTY+OR+SENSEX&hl=en-IN&gl=IN&ceid=IN:en"

    try:
        response = requests.get(rss_url, timeout=10)
        root = ET.fromstring(response.content)

        items = root.findall(".//item")[:5]

        if not items:
            await update.message.reply_text("❌ No news found.")
            return

        message = "📰 Latest Indian Stock Market News:\n\n"

        for item in items:
            title = item.find("title").text
            link = item.find("link").text
            message += f"🔹 {title}\n{link}\n\n"

        # ✅ Telegram limit fix (4096 chars)
        for i in range(0, len(message), 4000):
            await update.message.reply_text(message[i:i+4000])

    except Exception as e:
        await update.message.reply_text(f"⚠ Error: {str(e)}")

# ✅ Main function
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("news", news))

    print("🚀 Bot Running on Cloud...")
    app.run_polling()

if __name__ == "__main__":
    main()
