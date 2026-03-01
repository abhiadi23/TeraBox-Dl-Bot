import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str        = os.environ("BOT_TOKEN", "8598064539:AAFFDzeNlqPAOdhTvGIizQ9eL2Wp9Tf9jqQ")
NDUS_COOKIE: str      = os.environ("NDUS_COOKIE")

API_ID: int | None    = int(os.environ["API_ID", "27322718"]) if os.getenv("API_ID") else None
API_HASH: str | None  = os.getenv("API_HASH", "4f6d1b67cf101aea5cf0536885aa1b82")
SESSION_STRING: str | None = os.getenv("SESSION_STRING")

_4GB = 4 * 1024 ** 3
_2GB = 2 * 1024 ** 3
MAX_UPLOAD_SIZE: int  = _4GB if SESSION_STRING else _2GB
BOT_API_LIMIT: int    = 50 * 1024 ** 2

CACHE_TTL: int        = int(os.getenv("CACHE_TTL", 7200))
LOG_LEVEL: str        = os.getenv("LOG_LEVEL", "INFO").upper()
