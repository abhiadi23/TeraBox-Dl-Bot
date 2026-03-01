import logging
from config import LOG_LEVEL
from bot import build_app

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    level=getattr(logging, LOG_LEVEL, logging.INFO),
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Starting TeraBox Downloader Bot…")
    app = build_app()
    app.run_polling()


if __name__ == "__main__":
    main()
