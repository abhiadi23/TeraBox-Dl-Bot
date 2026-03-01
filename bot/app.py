"""
bot/app.py — Build and return the configured Telegram Application.

Kept separate from main.py so the app can be imported for testing
without immediately starting polling.
"""

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from config import BOT_TOKEN
from bot.handlers import cmd_start, cmd_help, handle_link


def build_app():
    """Construct the PTB Application with all handlers registered."""
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    return app
