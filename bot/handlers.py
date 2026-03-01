import logging

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from config import MAX_UPLOAD_SIZE, SESSION_STRING
from core import fetch_file_list, cache_get, cache_set, send_file
from utils import is_valid_terabox_url, extract_surl, find_url_in_text, format_bytes

logger = logging.getLogger(__name__)

_LIMIT_NOTE = (
    "4 GB (owner session active)"
    if SESSION_STRING
    else "2 GB (set `SESSION_STRING` in `.env` to raise to 4 GB)"
)


@Client.on_message(filters.command("start") & filters.private)
async def cmd_start(client: Client, message: Message) -> None:
    await message.reply_text(
        "☁️ **TeraBox Downloader Bot**\n\n"
        "Send me any TeraBox share link and I'll:\n"
        "• Upload the file directly to Telegram\n"
        "• Send you the direct download link\n\n"
        f"Upload limit: `{_LIMIT_NOTE}`\n\n"
        "Use /help for more info."
    )


@Client.on_message(filters.command("help") & filters.private)
async def cmd_help(client: Client, message: Message) -> None:
    await message.reply_text(
        "**How to use:**\n"
        "Just paste any TeraBox share link — the bot handles the rest.\n\n"
        "**Supported domains:**\n"
        "`terabox.com` · `terabox.app` · `1024terabox.com`\n"
        "`teraboxshare.com` · `teraboxlink.com`\n\n"
        "**File delivery:**\n"
        "≤ 50 MB → uploaded instantly via Bot API\n"
        "> 50 MB → downloaded on server, then uploaded via MTProto\n"
        f"> limit → download link only  _(limit: {_LIMIT_NOTE})_\n\n"
        "**Example link:**\n"
        "`https://terabox.app/s/1HSEb8PZRUE7Z1Tvd3ZtT0g`"
    )


@Client.on_message(filters.text & filters.private & ~filters.command(["start", "help"]))
async def handle_link(client: Client, message: Message) -> None:
    text = (message.text or "").strip()

    url = find_url_in_text(text)
    if not url:
        await message.reply_text("❌ Please send a valid TeraBox share link.")
        return

    if not is_valid_terabox_url(url):
        await message.reply_text(
            "❌ Not a supported TeraBox link. Use /help to see supported domains."
        )
        return

    surl = extract_surl(url)
    if not surl:
        await message.reply_text("❌ Could not extract the share token from the URL.")
        return

    status_msg = await message.reply_text("⏳ Resolving link…")

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
        filename = item.get("server_filename", "Unknown")
        file_size = int(item.get("size", 0))
        dlink = item.get("dlink", "")
        thumbs = item.get("thumbs", {})
        thumb_url = thumbs.get("url3") or thumbs.get("url2") or thumbs.get("url1", "")

        if not dlink:
            await status_msg.edit_text(
                f"⚠️ **{filename}**\nNo download link available for this file."
            )
            continue

        dl_keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("⬇️ Direct Download Link", url=dlink)]]
        )

        if thumb_url:
            try:
                await message.reply_photo(
                    photo=thumb_url,
                    caption=f"📁 **{filename}**\n📦 `{format_bytes(file_size)}`",
                    reply_markup=dl_keyboard,
                )
            except Exception as exc:
                logger.warning("Thumbnail send failed: %s", exc)
                await message.reply_text(
                    f"📁 **{filename}**\n📦 `{format_bytes(file_size)}`",
                    reply_markup=dl_keyboard,
                    disable_web_page_preview=True,
                )
        else:
            await status_msg.edit_text(
                f"📁 **{filename}**\n📦 `{format_bytes(file_size)}`",
                reply_markup=dl_keyboard,
                disable_web_page_preview=True,
            )

        upload_status = await message.reply_text(
            f"📤 Preparing to upload `{filename}`…"
        )

        await send_file(
            bot=client,
            chat_id=message.chat.id,
            dlink=dlink,
            filename=filename,
            file_size=file_size,
            status_msg=upload_status,
    )
