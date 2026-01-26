from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List

import aiohttp

from bot.context import BotContext
from bot.downloader_client import DownloaderError
from bot.media_normalizer import normalize_result
from handlers.flow import send_result_flow
from handlers.utils import build_api


def _extract_image_urls(data: Dict[str, Any]) -> List[str]:
    def collect_from_items(items: Iterable[Any], acc: List[str]) -> None:
        for item in items:
            if isinstance(item, str) and item.startswith("http"):
                acc.append(item)
                continue
            if isinstance(item, dict):
                for key in ("url", "src", "image", "img", "imageUrl", "image_url"):
                    val = item.get(key)
                    if isinstance(val, str) and val.startswith("http"):
                        acc.append(val)
                        break

    urls: List[str] = []
    candidates = [
        data.get("images"),
        data.get("image"),
        data.get("image_urls"),
        data.get("imageUrls"),
        data.get("image_list"),
        data.get("imageList"),
        data.get("slides"),
        data.get("photos"),
        data.get("photo"),
        data.get("photoUrls"),
    ]
    video_info = data.get("videoInfo")
    if isinstance(video_info, dict):
        candidates.extend(
            [
                video_info.get("images"),
                video_info.get("image"),
                video_info.get("image_urls"),
                video_info.get("imageUrls"),
                video_info.get("image_list"),
                video_info.get("imageList"),
                video_info.get("slides"),
                video_info.get("photos"),
                video_info.get("photo"),
                video_info.get("photoUrls"),
            ]
        )

    for cand in candidates:
        if isinstance(cand, list):
            collect_from_items(cand, urls)

    seen = set()
    unique_urls: List[str] = []
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        unique_urls.append(url)
    return unique_urls


def _is_audio_url(url: str) -> bool:
    return "mime_type=audio" in url.lower()


def _build_tiktok_result(data: Dict[str, Any], original_url: str) -> Dict[str, Any]:
    # Map ttsave-style response to normalized schema expected by send_result_flow
    dlink = data.get("dlink") or {}
    video_info = data.get("videoInfo") or {}

    medias: List[Dict[str, Any]] = []
    nowm = dlink.get("nowm") or video_info.get("nowm")
    if isinstance(nowm, str) and nowm.startswith("http"):
        if _is_audio_url(nowm):
            medias.append(
                {
                    "type": "audio",
                    "url": nowm,
                    "extension": "m4a",
                    "quality": "audio",
                    "filename": "tiktok_audio.m4a",
                    "mimeType": "audio/mp4",
                    "is_audio": True,
                }
            )
        else:
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
        if _is_audio_url(wm):
            medias.append(
                {
                    "type": "audio",
                    "url": wm,
                    "extension": "m4a",
                    "quality": "audio",
                    "filename": "tiktok_audio.m4a",
                    "mimeType": "audio/mp4",
                    "is_audio": True,
                }
            )
        else:
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

    image_urls = _extract_image_urls(data)
    for idx, image_url in enumerate(image_urls, start=1):
        medias.append(
            {
                "type": "image",
                "url": image_url,
                "extension": None,
                "quality": "photo",
                "filename": f"tiktok_photo_{idx}.jpg",
                "mimeType": None,
            }
        )

    result = {
        "url": original_url,
        "author": None,
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
        if not norm_result.get("medias"):
            mapped = _build_tiktok_result(data, url)
            norm_result = normalize_result(mapped, platform)
    else:
        mapped = _build_tiktok_result(data, url)
        norm_result = normalize_result(mapped, platform)

    await send_result_flow(ctx, platform=platform, message=message, result=norm_result, req_id=req_id, user_id=user_id, api=api, original_url=url)

