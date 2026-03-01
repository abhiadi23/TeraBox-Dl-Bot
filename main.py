import logging
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN

logger = logging.getLogger(__name__)


def main() -> None:
    """Build and configure the Pyrogram Client."""
    
    plugins = dict(root="bot")  # Load handlers from bot/ directory
    
    app = Client(
        name="terabox_bot",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        plugins=plugins,
        workdir=".",
    )
    
    logger.info("Bot client configured successfully")
    
    try:
        logger.info("Starting bot...")
        app.run()  # This actually starts the bot
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    finally:
        logger.info("Bot shutdown complete")


if __name__ == "__main__":
    main()
