import feedparser
import asyncio
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")

stocks = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Stock Bot is running ✅")

async def add_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stock = " ".join(context.args)
    if stock and stock not in stocks:
        stocks.append(stock)
        await update.message.reply_text(f"Added: {stock}")
    else:
        await update.message.reply_text("Stock exists or invalid.")

async def list_stocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if stocks:
        await update.message.reply_text("Your Stocks:\n" + "\n".join(stocks))
    else:
        await update.message.reply_text("No stocks added.")

def get_news(query):
    url = f"https://news.google.com/rss/search?q={query}+stock+india"
    feed = feedparser.parse(url)
    return feed.entries[:3]

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not stocks:
        await update.message.reply_text("No stocks added.")
        return

    report = "📊 Daily Stock Headlines\n\n"

    for stock in stocks:
        news_list = get_news(stock)
        if news_list:
            report += f"{stock}\n"
            for news in news_list:
                report += f"- {news.title}\n"
            report += "\n"

    await update.message.reply_text(report)

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_stock))
    app.add_handler(CommandHandler("list", list_stocks))
    app.add_handler(CommandHandler("summary", summary))

    print("Bot Running on Cloud...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
