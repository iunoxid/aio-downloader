from __future__ import annotations

import logging
from typing import Any, Dict, List

import aiohttp

from bot.context import BotContext
from bot.downloader_client import DownloaderError
from bot.media_normalizer import normalize_result
from handlers.flow import send_result_flow
from handlers.utils import build_api


def _build_tiktok_result(data: Dict[str, Any], original_url: str) -> Dict[str, Any]:
    # Map ttsave-style response to normalized schema expected by send_result_flow
    dlink = data.get("dlink") or {}
    video_info = data.get("videoInfo") or {}

    medias: List[Dict[str, Any]] = []
    nowm = dlink.get("nowm") or video_info.get("nowm")
    if isinstance(nowm, str) and nowm.startswith("http"):
        medias.append(
            {
                "type": "video",
                "url": nowm,
                "extension": "mp4",
                "quality": "no_watermark",
                "filename": "tiktok_nowm.mp4",
                "mimeType": "video/mp4",
            }
        )
    wm = dlink.get("wm") or video_info.get("wm")
    if isinstance(wm, str) and wm.startswith("http"):
        medias.append(
            {
                "type": "video",
                "url": wm,
                "extension": "mp4",
                "quality": "watermark",
                "filename": "tiktok_wm.mp4",
                "mimeType": "video/mp4",
            }
        )
    audio = dlink.get("audio")
    if isinstance(audio, str) and audio.startswith("http"):
        medias.append(
            {
                "type": "audio",
                "url": audio,
                "extension": "mp3",
                "quality": "audio",
                "filename": "tiktok_audio.mp3",
                "mimeType": "audio/mpeg",
                "is_audio": True,
            }
        )

    result = {
        "url": original_url,
        "author": data.get("creator") or data.get("username"),
        "title": data.get("description"),
        "thumbnail": dlink.get("cover"),
        "medias": medias,
    }
    return result


async def process_tiktok(ctx: BotContext, *, platform: str, message, url: str, req_id: str, user_id: int) -> None:
    logger = logging.getLogger("bot")
    api = build_api(ctx, platform)
    try:
        async with aiohttp.ClientSession() as session:
            # Resolve shortlink first to improve success rate
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
            success = data.get("success")
            if success is False:
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
        mapped = _build_tiktok_result(data, url)
        norm_result = normalize_result(mapped, platform)

    await send_result_flow(ctx, platform=platform, message=message, result=norm_result, req_id=req_id, user_id=user_id, api=api, original_url=url)

