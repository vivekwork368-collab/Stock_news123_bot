import asyncio
import logging
import os
import signal
import sys
from telegram.ext import Application, CommandHandler

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_TOKEN')
if not TOKEN:
    logger.error("TELEGRAM_TOKEN not set!")
    sys.exit(1)

async def start(update, context):
    await update.message.reply_text('✅ Bot running perfectly on Render!')

async def stop(update, context):
    await update.message.reply_text('🛑 Bot stopping...')

def signal_handler(signum, frame):
    logger.info("Received signal, shutting down gracefully...")
    sys.exit(0)

async def main():
    """Async main with proper event loop management"""
    app = Application.builder().token(TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    
    # Graceful shutdown handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("🚀 Bot starting polling...")
    
    # Use low-level polling API - NO run_polling()
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    
    logger.info("✅ Bot is running! Press Ctrl+C to stop.")
    
    # Keep running until interrupted
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("🛑 Shutting down...")
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot interrupted.")
