import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str        = os.environ["BOT_TOKEN"]
NDUS_COOKIE: str      = os.environ["NDUS_COOKIE"]

API_ID: int | None    = int(os.environ["API_ID"]) if os.getenv("API_ID") else None
API_HASH: str | None  = os.getenv("API_HASH")
SESSION_STRING: str | None = os.getenv("SESSION_STRING")

_4GB = 4 * 1024 ** 3
_2GB = 2 * 1024 ** 3
MAX_UPLOAD_SIZE: int  = _4GB if SESSION_STRING else _2GB
BOT_API_LIMIT: int    = 50 * 1024 ** 2

CACHE_TTL: int        = int(os.getenv("CACHE_TTL", 7200))
LOG_LEVEL: str        = os.getenv("LOG_LEVEL", "INFO").upper()
