from __future__ import annotations

import logging
from typing import Any, Dict, List

import aiohttp

from bot.context import BotContext
from bot.downloader_client import DownloaderError
from bot.media_normalizer import normalize_result
from handlers.flow import send_result_flow
from handlers.utils import build_api


def _build_instagram_result(data: Dict[str, Any], original_url: str) -> Dict[str, Any]:
    # Map igstory-style response: {"status": true, "data": [url, ...]}
    medias: List[Dict[str, Any]] = []
    items = data.get("data") or []
    if isinstance(items, list):
        for idx, item in enumerate(items, start=1):
            if not isinstance(item, str) or not item.startswith("http"):
                continue
            lower = item.lower()
            if ".mp4" in lower or "mime_type=video" in lower or "video_mp4" in lower:
                medias.append(
                    {
                        "type": "video",
                        "url": item,
                        "extension": "mp4",
                        "quality": "story",
                        "filename": f"instagram_{idx}.mp4",
                        "mimeType": "video/mp4",
                    }
                )
            else:
                medias.append(
                    {
                        "type": "image",
                        "url": item,
                        "extension": None,
                        "quality": "story",
                        "filename": f"instagram_{idx}.jpg",
                        "mimeType": "image/jpeg",
                    }
                )

    return {
        "url": original_url,
        "author": data.get("creator"),
        "title": data.get("description"),
        "medias": medias,
    }


async def process_instagram(ctx: BotContext, *, platform: str, message, url: str, req_id: str, user_id: int) -> None:
    logger = logging.getLogger("bot")
    api = build_api(ctx, platform)
    try:
        async with aiohttp.ClientSession() as session:
            resolved = await api.resolve_redirects(session, url)
            if resolved != url:
                logger.info("url_resolved id=%s from=%s to=%s", req_id, url, resolved)
            params = {api.url_param_name: resolved}
            if api.api_key:
                params[api.apikey_param_name] = api.api_key
            timeout = aiohttp.ClientTimeout(
                total=ctx.settings.http_total_timeout,
                connect=ctx.settings.http_connect_timeout,
                sock_read=ctx.settings.http_read_timeout,
            )
            async with session.get(api.base_url, params=params, timeout=timeout) as resp:
                if resp.status >= 500:
                    raise DownloaderError(f"Server error: {resp.status}")
                if resp.status != 200:
                    text = await resp.text()
                    raise DownloaderError(f"Status {resp.status}: {text[:200]}")
                data = await resp.json(content_type=None)
            status = data.get("status")
            if status is False:
                raise DownloaderError("Downloader returned unsuccess status")
    except DownloaderError as e:
        logger.warning("downloader_error id=%s user=%s url=%s error=%s", req_id, user_id, url, str(e))
        await message.reply_text("Maaf, server downloader sedang sibuk. Coba lagi nanti.")
        return
    except Exception:
        logger.exception("unexpected_downloader_error id=%s user=%s url=%s", req_id, user_id, url)
        await message.reply_text("Terjadi kesalahan saat memproses tautan.")
        return

    if isinstance(data.get("result"), dict):
        raw_result = data.get("result") or {}
        norm_result = normalize_result(raw_result, platform)
    else:
        mapped = _build_instagram_result(data, url)
        norm_result = normalize_result(mapped, platform)

    await send_result_flow(ctx, platform=platform, message=message, result=norm_result, req_id=req_id, user_id=user_id, api=api, original_url=url)

