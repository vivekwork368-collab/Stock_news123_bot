import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import yfinance as yf
import feedparser

# ---------------------------
# Configure logging
# ---------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------------------------
# Telegram Bot Token
# ---------------------------
TOKEN = "8601899020:AAF6xdQ9Uc2vUqE2J3g_B_iynLoVa83bfGQ"  # Replace with your actual token

# ---------------------------
# /start command
# ---------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! 🤖\n\n"
        "I can give you stock prices and news.\n"
        "Use /stock <TICKER> to get stock price.\n"
        "Use /news <TICKER> to get latest news."
    )

# ---------------------------
# /stock command
# ---------------------------
async def stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /stock <TICKER>")
        return
    ticker = context.args[0].upper()
    try:
        stock_info = yf.Ticker(ticker)
        data = stock_info.history(period="1d")
        if data.empty:
            await update.message.reply_text(f"No data found for {ticker}")
            return
        price = data['Close'].iloc[-1]
        await update.message.reply_text(f"{ticker} price: ${price:.2f}")
    except Exception as e:
        logger.error(f"Error fetching stock {ticker}: {e}")
        await update.message.reply_text(f"Error fetching stock {ticker}: {e}")

# ---------------------------
# /news command
# ---------------------------
async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /news <TICKER>")
        return
    ticker = context.args[0].upper()
    try:
        # Use Yahoo Finance RSS feed
        rss_url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
        feed = feedparser.parse(rss_url)
        if not feed.entries:
            await update.message.reply_text(f"No news found for {ticker}")
            return
        message = f"Latest news for {ticker}:\n"
        for entry in feed.entries[:5]:  # Top 5 news
            message += f"\n- {entry.title}\n  {entry.link}\n"
        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Error fetching news {ticker}: {e}")
        await update.message.reply_text(f"Error fetching news {ticker}: {e}")

# ---------------------------
# Main function
# ---------------------------
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stock", stock))
    app.add_handler(CommandHandler("news", news))

    # Start the bot
    logger.info("Bot started 🚀")
    await app.run_polling()

# ---------------------------
# Entry point
# ---------------------------
if __name__ == "__main__":
    asyncio.run(main())
