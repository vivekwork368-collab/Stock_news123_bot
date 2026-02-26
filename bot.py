import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# --------------------------
# Your Bot Token
# --------------------------
TOKEN = "8601899020:AAF6xdQ9Uc2vUqE2J3g_B_iynLoVa83bfGQ"  # Replace with your actual token

# --------------------------
# Your Bot Handlers
# --------------------------
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Hello! Bot is running on Render ✅")

# You can add more command handlers here
def hello(update: Update, context: CallbackContext):
    update.message.reply_text("Hi there! 👋")

# --------------------------
# Telegram Bot Function
# --------------------------
def run_telegram_bot():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Add your handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("hello", hello))

    # Start polling
    updater.start_polling()
    updater.idle()  # Keeps bot alive

# --------------------------
# Dummy Web Server for Render
# --------------------------
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running 🚀")

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
