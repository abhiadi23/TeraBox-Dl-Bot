import logging
from pathlib import Path
import httpx
from pyrogram import Client, enums

from config import (
    BOT_TOKEN, API_ID, API_HASH, SESSION_STRING,
    MAX_UPLOAD_SIZE, BOT_API_LIMIT,
)

logger = logging.getLogger(__name__)
CHUNK = 10 * 1024 * 1024

async def _download_file(url: str, dest: Path, progress_cb=None) -> None:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
        )
    }
    async with httpx.AsyncClient(follow_redirects=True, timeout=None) as client:
        async with client.stream("GET", url, headers=headers) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0))
            downloaded = 0
            with open(dest, "wb") as f:
                async for chunk in resp.aiter_bytes(CHUNK):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_cb and total:
                        await progress_cb(downloaded, total)

def _make_pyro_client() -> Client:
    # Helper to create a temporary client for large file uploads
    if SESSION_STRING:
        return Client(
            name="owner_session",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=SESSION_STRING,
            no_updates=True,
            in_memory=True
        )
    return Client(
        name="bot_session_tmp",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        no_updates=True,
        in_memory=True
    )

def _fmt(size: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

async def send_file(
    client: Client,
    chat_id: int,
    dlink: str,
    filename: str,
    file_size: int,
    status_msg,
) -> None:
    if file_size > MAX_UPLOAD_SIZE:
        limit_gb = MAX_UPLOAD_SIZE // 1024 ** 3
        await status_msg.edit(
            f"⚠️ **{filename}**\n\n"
            f"File is `{_fmt(file_size)}` — exceeds the `{limit_gb} GB` upload limit.\n\n"
            f"[⬇️ Download directly from TeraBox]({dlink})",
            parse_mode=enums.ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
        return

    # Pyrogram can handle small files directly from URL, but usually safer to use Bot API logic
    if file_size <= BOT_API_LIMIT:
        await _send_via_bot_api(client, chat_id, dlink, filename, file_size, status_msg)
    else:
        if not API_ID or not API_HASH:
            await status_msg.edit(
                f"⚠️ File is `{_fmt(file_size)}` — `API_ID`/`API_HASH` not configured.\n\n"
                f"[⬇️ Download directly]({dlink})",
                parse_mode=enums.ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )
            return
        await _send_via_pyrogram(chat_id, dlink, filename, file_size, status_msg)

async def _send_via_bot_api(client: Client, chat_id, dlink, filename, file_size, status_msg):
    await status_msg.edit(
        f"📤 Uploading `{filename}` (`{_fmt(file_size)}`)…",
        parse_mode=enums.ParseMode.MARKDOWN,
    )
    try:
        # Pyrogram can send remote URLs as documents
        await client.send_document(
            chat_id=chat_id,
            document=dlink,
            file_name=filename,
            caption=f"📁 **{filename}**\n`{_fmt(file_size)}`",
            parse_mode=enums.ParseMode.MARKDOWN,
        )
        await status_msg.delete()
    except Exception as exc:
        logger.error("Bot API upload failed: %s", exc)
        await status_msg.edit(
            f"❌ Upload failed.\n\n[⬇️ Download directly]({dlink})",
            parse_mode=enums.ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )

async def _send_via_pyrogram(chat_id, dlink, filename, file_size, status_msg):
    tmp_path = Path(f"downloads/{filename}")
    tmp_path.parent.mkdir(exist_ok=True)
    last_pct = [-1]

    async def on_progress(done, total):
        pct = int(done / total * 100)
        step = pct - (pct % 10)
        if step != last_pct[0]:
            last_pct[0] = step
            try:
                await status_msg.edit(
                    f"⬇️ Downloading `{filename}`… {step}%  "
                    f"(`{_fmt(done)}` / `{_fmt(total)}`)",
                    parse_mode=enums.ParseMode.MARKDOWN,
                )
            except: pass

    try:
        await status_msg.edit(f"⬇️ Downloading `{filename}`…", parse_mode=enums.ParseMode.MARKDOWN)
        await _download_file(dlink, tmp_path, progress_cb=on_progress)

        await status_msg.edit(f"📤 Uploading `{filename}`…", parse_mode=enums.ParseMode.MARKDOWN)

        async with _make_pyro_client() as pyro:
            await pyro.send_document(
                chat_id=chat_id,
                document=str(tmp_path),
                file_name=filename,
                caption=f"📁 **{filename}**\n`{_fmt(file_size)}`",
                parse_mode=enums.ParseMode.MARKDOWN,
            )

        await status_msg.delete()
    except Exception as exc:
        logger.error("Pyrogram upload failed: %s", exc)
        await status_msg.edit(f"❌ Upload failed: `{exc}`", disable_web_page_preview=True)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
