from __future__ import annotations

import logging

import aiohttp

from bot.context import BotContext
from bot.downloader_client import DownloaderClient
from bot.media_normalizer import normalize_result
from handlers.flow import send_result_flow
from handlers.utils import build_api, fetch_with_redirect


async def process_douyin(ctx: BotContext, *, platform: str, message, url: str, req_id: str, user_id: int) -> None:
    logger = logging.getLogger("bot")
    api = build_api(ctx, platform)
    try:
        async with aiohttp.ClientSession() as session:
            data = await fetch_with_redirect(ctx, api, session, req_id=req_id, user_id=user_id, url=url, platform=platform)
            raw_result = data.get("result") or {}
            medias = raw_result.get("medias") or []
            if not medias:
                try:
                    fb_api = build_api(ctx, "aio")
                    logger.info("douyin_fallback_start id=%s endpoint=%s", req_id, fb_api.base_url)
                    data_fb = await fetch_with_redirect(ctx, fb_api, session, req_id=req_id, user_id=user_id, url=url, platform=platform)
                    res_fb = data_fb.get("result") or {}
                    medias_fb = res_fb.get("medias") or []
                    if medias_fb:
                        data = data_fb
                        logger.info("douyin_fallback_success id=%s count=%s", req_id, len(medias_fb))
                    else:
                        logger.info("douyin_fallback_empty id=%s", req_id)
                except Exception:
                    logger.exception("douyin_fallback_error id=%s", req_id)
    except Exception:
        logger.exception("unexpected_downloader_error id=%s user=%s url=%s", req_id, user_id, url)
        await message.reply_text("Terjadi kesalahan saat memproses tautan.")
        return

    raw_result = data.get("result") or {}
    norm_result = normalize_result(raw_result, platform)
    await send_result_flow(ctx, platform=platform, message=message, result=norm_result, req_id=req_id, user_id=user_id, api=api, original_url=url)
