import logging
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN, SESSION_STRING

logger = logging.getLogger(__name__)


def build_app() -> Client:
    """Build and configure the Pyrogram Client."""
    
    plugins = dict(root="bot")  # This will load handlers from cmds.py
    
    app = Client(
        name="terabox_bot",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        plugins=plugins,
        workdir=".",
    )
    
    logger.info("Bot client configured successfully")
    return app
