import logging
import yfinance as yf
import feedparser
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Replace this with your bot token
TOKEN = "8601899020:AAF6xdQ9Uc2vUqE2J3g_B_iynLoVa83bfGQ"

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== Helper functions =====

async def fetch_stock_price(symbol: str) -> str:
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period="1d")
        if not data.empty:
            price = data["Close"].iloc[-1]
            return f"{symbol.upper()} current price: ₹{price:.2f}"
        else:
            return f"No data available for {symbol.upper()}"
    except Exception as e:
        logger.error(f"Error fetching stock price: {e}")
        return "Failed to fetch stock price."

async def fetch_stock_news(symbol: str) -> str:
    try:
        url = f"https://finance.yahoo.com/rss/headline?s={symbol}"
        feed = feedparser.parse(url)
        if feed.entries:
            news_list = [f"- {entry.title}" for entry in feed.entries[:5]]
            return f"Latest news for {symbol.upper()}:\n" + "\n".join(news_list)
        else:
            return f"No news found for {symbol.upper()}"
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        return "Failed to fetch news."

# ===== Command Handlers =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Get Stock Price", callback_data="price")],
        [InlineKeyboardButton("Get Stock News", callback_data="news")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome to StockBot! Choose an option and then enter the stock symbol (like RELIANCE.BO):",
        reply_markup=reply_markup,
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # Store user selection (price or news) in context.user_data
    context.user_data["action"] = query.data
    await query.edit_message_text(
        text=f"You selected *{query.data.upper()}*. Now send the stock symbol:",
        parse_mode="Markdown",
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle stock symbol sent by user"""
    symbol = update.message.text.strip().upper()
    action = context.user_data.get("action")

    if not action:
        await update.message.reply_text(
            "Please select an option first using /start or the menu buttons."
        )
        return

    if action == "price":
        result = await fetch_stock_price(symbol)
    elif action == "news":
        result = await fetch_stock_news(symbol)
    else:
        result = "Unknown action."

    await update.message.reply_text(result)
    # Clear action after processing
    context.user_data["action"] = None

# ===== Main =====

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
# --------------------------
# Dummy Web Server for Render
# --------------------------
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write("Bot is running 🚀".encode("utf-8"))
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))  # Render assigns PORT automatically
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    print(f"Dummy web server running on port {port}")
    server.serve_forever()

# --------------------------
# Run Both Bot and Server
# --------------------------
if __name__ == "__main__":
    # Start web server in background thread
    threading.Thread(target=run_dummy_server, daemon=True).start()

    # Start Telegram bot
    run_telegram_bot()
