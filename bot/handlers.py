import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import MAX_UPLOAD_SIZE, SESSION_STRING
from core import fetch_file_list, cache_get, cache_set, send_file
from utils import is_valid_terabox_url, extract_surl, find_url_in_text, format_bytes

logger = logging.getLogger(__name__)

_LIMIT_NOTE = (
    "4 GB (owner session active)"
    if SESSION_STRING
    else "2 GB (set `SESSION_STRING` in `.env` to raise to 4 GB)"
)


async def cmd_start(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "☁️ *TeraBox Downloader Bot*\n\n"
        "Send me any TeraBox share link and I'll:\n"
        "• Upload the file directly to Telegram\n"
        "• Send you the direct download link\n\n"
        f"Upload limit: `{_LIMIT_NOTE}`\n\n"
        "Use /help for more info.",
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_help(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "*How to use:*\n"
        "Just paste any TeraBox share link — the bot handles the rest.\n\n"
        "*Supported domains:*\n"
        "`terabox.com` · `terabox.app` · `1024terabox.com`\n"
        "`teraboxshare.com` · `teraboxlink.com`\n\n"
        "*File delivery:*\n"
        "≤ 50 MB → uploaded instantly via Bot API\n"
        "> 50 MB → downloaded on server, then uploaded via MTProto\n"
        f"> limit → download link only  _(limit: {_LIMIT_NOTE})_\n\n"
        "*Example link:*\n"
        "`https://terabox.app/s/1HSEb8PZRUE7Z1Tvd3ZtT0g`",
        parse_mode=ParseMode.MARKDOWN,
    )


async def handle_link(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.message.text or "").strip()

    url = find_url_in_text(text)
    if not url:
        await update.message.reply_text("❌ Please send a valid TeraBox share link.")
        return

    if not is_valid_terabox_url(url):
        await update.message.reply_text(
            "❌ Not a supported TeraBox link. Use /help to see supported domains."
        )
        return

    surl = extract_surl(url)
    if not surl:
        await update.message.reply_text("❌ Could not extract the share token from the URL.")
        return

    status_msg = await update.message.reply_text("⏳ Resolving link…")

    data = cache_get(surl)
    if data is None:
        data = fetch_file_list(surl)
        if not data.get("error"):
            cache_set(surl, data)

    if data.get("error"):
        await status_msg.edit_text(f"❌ {data['error']}")
        return

    file_list = data.get("list", [])
    if not file_list:
        await status_msg.edit_text("❌ No files found. The link may be expired or private.")
        return

    for item in file_list[:5]:
        filename  = item.get("server_filename", "Unknown")
        file_size = int(item.get("size", 0))
        dlink     = item.get("dlink", "")
        thumbs    = item.get("thumbs", {})
        thumb_url = thumbs.get("url3") or thumbs.get("url2") or thumbs.get("url1", "")

        if not dlink:
            await status_msg.edit_text(
                f"⚠️ *{filename}*\nNo download link available for this file.",
                parse_mode=ParseMode.MARKDOWN,
            )
            continue

        dl_keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("⬇️ Direct Download Link", url=dlink)]]
        )

        if thumb_url:
            try:
                await update.message.reply_photo(
                    photo=thumb_url,
                    caption=f"📁 *{filename}*\n📦 `{format_bytes(file_size)}`",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=dl_keyboard,
                )
            except Exception as exc:
                logger.warning("Thumbnail send failed: %s", exc)
                await update.message.reply_text(
                    f"📁 *{filename}*\n📦 `{format_bytes(file_size)}`",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=dl_keyboard,
                    disable_web_page_preview=True,
                )
        else:
            await status_msg.edit_text(
                f"📁 *{filename}*\n📦 `{format_bytes(file_size)}`",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=dl_keyboard,
                disable_web_page_preview=True,
            )

        upload_status = await update.message.reply_text(
            f"📤 Preparing to upload `{filename}`…",
            parse_mode=ParseMode.MARKDOWN,
        )

        await send_file(
            bot=ctx.bot,
            chat_id=update.effective_chat.id,
            dlink=dlink,
            filename=filename,
            file_size=file_size,
            status_msg=upload_status,
        )
