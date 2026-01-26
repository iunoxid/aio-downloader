from __future__ import annotations

import io
from typing import List

import aiohttp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto

from bot.context import BotContext
from bot.downloader_client import DownloaderClient, TooLargeError
from bot.media_utils import is_image, is_video, iter_medias, pick_caption, summarize_result
from bot.ui import build_summary_keyboard


async def send_result_flow(ctx: BotContext, *, platform: str, message, result: dict, req_id: str, user_id: int, api: DownloaderClient, original_url: str) -> None:
    import logging

    logger = logging.getLogger("bot")

    author = result.get("author")
    title = result.get("title")
    videos, images, audios = summarize_result(result)

    if videos + images + audios == 0:
        await message.reply_text("Tidak ditemukan media.")
        return

    caption_text = pick_caption(author, title)

    logger.info(
        "request_success id=%s user=%s url=%s videos=%s images=%s audios=%s",
        req_id,
        user_id,
        original_url,
        videos,
        images,
        audios,
    )

    # Build keyboard
    kb = None
    try:
        kb = build_summary_keyboard(ctx, result, user_id=user_id, chat_id=message.chat_id, message_id=None)
    except Exception:
        logger.exception("failed_build_keyboard")

    # Decide flows based on medias
    videos_list = [m for _, m in iter_medias(result) if is_video(m)]
    image_medias = [m for _, m in iter_medias(result) if is_image(m)]

    video_sent = False
    # Prefer video if available
    try:
        if videos_list:
            from bot.media_utils import choose_best_video

            best = choose_best_video(videos_list)
            if best:
                best_video_url = best.get("url") or best.get("download_url") or ""
                try:
                    await message.reply_video(
                        video=best_video_url,
                        caption=caption_text or None,
                        supports_streaming=True,
                        reply_markup=kb,
                    )
                    video_sent = True
                except Exception:
                    logger.exception("send_best_video_failed_post")
                    # Fallback: download into memory then upload
                    try:
                        async with aiohttp.ClientSession() as session:
                            size = await api.head_size(session, best_video_url)
                            if size is not None and size > ctx.settings.max_upload_bytes:
                                await message.reply_text(
                                    f"Ukuran video terlalu besar untuk diupload ({size} bytes). Mengirim tautan saja.",
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text="Buka di Browser", url=best_video_url)]]),
                                )
                            else:
                                try:
                                    data = await api.download_to_bytes(session, best_video_url, ctx.settings.max_upload_bytes)
                                except TooLargeError as e:
                                    await message.reply_text(
                                        f"Ukuran video terlalu besar untuk diupload ({e.size} bytes).",
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text="Buka di Browser", url=best_video_url)]]),
                                    )
                                else:
                                    bio = io.BytesIO(data)
                                    filename = (best.get("filename") or f"video_{req_id}.mp4")
                                    bio.name = filename
                                    await message.reply_video(
                                        video=bio,
                                        caption=caption_text or None,
                                        supports_streaming=True,
                                        reply_markup=kb,
                                    )
                                    video_sent = True
                    except Exception:
                        logger.exception("send_best_video_fallback_download_failed id=%s", req_id)
    except Exception:
        logger.exception("send_best_video_failed")

    # Images: TikTok groups as album, others sequential
    if image_medias:
        if platform in ("tiktok", "facebook", "instagram", "threads") and len(image_medias) > 1:
            try:
                groups = [image_medias[i : i + 10] for i in range(0, len(image_medias), 10)]
                for g_idx, group in enumerate(groups):
                    media_group = []
                    for idx_in_group, m in enumerate(group):
                        if g_idx == 0 and idx_in_group == 0:
                            cap = f"🖼️ {pick_caption(author, title)}"
                            media_group.append(InputMediaPhoto(media=m.get("url"), caption=cap))
                        else:
                            media_group.append(InputMediaPhoto(media=m.get("url")))
                    await message.reply_media_group(media=media_group)
            except Exception:
                logger.exception("send_image_group_failed")
        else:
            for idx, m in enumerate(image_medias, start=1):
                try:
                    await message.reply_photo(photo=m.get("url"))
                except Exception:
                    logger.exception("send_image_failed idx=%s", idx)

    # If no video was sent, send caption + buttons after images
    if not video_sent:
        if caption_text:
            if kb:
                await message.reply_text(caption_text, reply_markup=kb)
            else:
                await message.reply_text(caption_text)
        elif kb:
            await message.reply_text(".", reply_markup=kb)
