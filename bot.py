import os
import json
import feedparser
from apscheduler.schedulers.background import BackgroundScheduler
import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ---------- CONFIG ----------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # Set this in Render Environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Set this in Render Environment
PORTFOLIO_FILE = "portfolio.json"
CHAT_ID = os.getenv("CHAT_ID")  # Your Telegram user ID or group

openai.api_key = OPENAI_API_KEY

# ---------- UTILS ----------
def load_portfolio():
    if not os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, "w") as f:
            json.dump([], f)
        return []
    with open(PORTFOLIO_FILE, "r") as f:
        return json.load(f)

def save_portfolio(portfolio):
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f)

def fetch_news(query, count=5):
    news = []
    rss_urls = [
        f"https://news.google.com/rss/search?q={query}",
        f"https://finance.yahoo.com/rss/headline?s={query}"
    ]
    for url in rss_urls:
        feed = feedparser.parse(url)
        for entry in feed.entries[:count]:
            news.append(f"{entry.title}\n{entry.link}")
    return news

async def summarize_and_analyze(text, stock):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "user",
                "content": (
                    f"Summarize this news in 2-3 bullet points:\n{text}\n\n"
                    f"Then provide market sentiment for the stock {stock} for the monthly timeframe "
                    f"(Bullish / Bearish / Neutral). Format your response as:\n"
                    f"Summary:\n- ...\nSentiment: ..."
                )
            }],
            max_tokens=200
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Error summarizing/analyzing: {e}"

def aggregate_sentiment(sentiments):
    counts = {"Bullish":0, "Bearish":0, "Neutral":0}
    for s in sentiments:
        if "Bullish" in s: counts["Bullish"] += 1
        elif "Bearish" in s: counts["Bearish"] += 1
        else: counts["Neutral"] += 1
    total = sum(counts.values())
    if total == 0: return "No sentiment data"
    return {k: f"{v/total*100:.0f}%" for k,v in counts.items()}

# ---------- TELEGRAM COMMANDS ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome! Use /add, /remove, /portfolio to manage stocks.\n"
        "Get news with /news. Daily sentiment report will be sent automatically."
    )

async def add_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    portfolio = load_portfolio()
    if not context.args:
        await update.message.reply_text("Provide stock/sector to add, e.g. /add RELIANCE")
        return
    stock = " ".join(context.args).upper()
    if stock not in portfolio:
        portfolio.append(stock)
        save_portfolio(portfolio)
        await update.message.reply_text(f"Added {stock} to your portfolio.")
    else:
        await update.message.reply_text(f"{stock} is already in your portfolio.")

async def remove_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    portfolio = load_portfolio()
    if not context.args:
        await update.message.reply_text("Provide stock/sector to remove, e.g. /remove TECH")
        return
    stock = " ".join(context.args).upper()
    if stock in portfolio:
        portfolio.remove(stock)
        save_portfolio(portfolio)
        await update.message.reply_text(f"Removed {stock} from your portfolio.")
    else:
        await update.message.reply_text(f"{stock} is not in your portfolio.")

async def show_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    portfolio = load_portfolio()
    if portfolio:
        await update.message.reply_text("Your portfolio:\n" + "\n".join(portfolio))
    else:
        await update.message.reply_text("Your portfolio is empty. Add stocks using /add command.")

async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    portfolio = load_portfolio()
    if not portfolio:
        await update.message.reply_text("Portfolio is empty. Add stocks using /add")
        return
    for stock in portfolio:
        news_list = fetch_news(stock)
        if not news_list:
            await update.message.reply_text(f"No news found for {stock}")
            continue
        sentiments = []
        for news_item in news_list:
            result = await summarize_and_analyze(news_item, stock)
            await update.message.reply_text(f"*{stock}*\n{result}", parse_mode="Markdown")
            if "Sentiment:" in result:
                sentiments.append(result.split("Sentiment:")[1].strip())
        agg = aggregate_sentiment(sentiments)
        await update.message.reply_text(f"*{stock} Monthly Sentiment:*\n{agg}", parse_mode="Markdown")

# ---------- DAILY SENTIMENT REPORT ----------
async def daily_report():
    portfolio = load_portfolio()
    if not portfolio: return
    for stock in portfolio:
        news_list = fetch_news(stock, count=7)
        sentiments = []
        report_msg = f"*{stock} News Summary & Sentiment:*\n"
        for news_item in news_list:
            result = await summarize_and_analyze(news_item, stock)
            report_msg += result + "\n\n"
            if "Sentiment:" in result:
                sentiments.append(result.split("Sentiment:")[1].strip())
        agg = aggregate_sentiment(sentiments)
        report_msg += f"*Aggregated Monthly Sentiment:*\n{agg}"
        # Send via bot
        app = context.bot_data.get("app")
        if app:
            await app.bot.send_message(chat_id=CHAT_ID, text=report_msg, parse_mode="Markdown")

# ---------- MAIN ----------
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Store app reference for daily report
    app.bot_data["app"] = app

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_stock))
    app.add_handler(CommandHandler("remove", remove_stock))
    app.add_handler(CommandHandler("portfolio", show_portfolio))
    app.add_handler(CommandHandler("news", get_news))

    # Schedule daily report at 9:00 AM
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: app.create_task(daily_report()), 'cron', hour=9, minute=0)
    scheduler.start()

    app.run_polling()
