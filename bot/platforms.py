from __future__ import annotations

from urllib.parse import urlparse


SUPPORTED_PLATFORMS = {
    "tiktok": [
        "tiktok.com",
        "vt.tiktok.com",
    ],
    "youtube": [
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "youtu.be",
    ],
    "douyin": [
        "douyin.com",
        "iesdouyin.com",
    ],
    "facebook": [
        "facebook.com",
        "fb.watch",
        "m.facebook.com",
        "web.facebook.com",
    ],
    "instagram": [
        "instagram.com",
        "www.instagram.com",
    ],
    "threads": [
        "threads.net",
        "www.threads.net",
    ],
}


def detect_platform(url: str) -> str | None:
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
    except Exception:
        return None

    for platform, domains in SUPPORTED_PLATFORMS.items():
        for d in domains:
            if host == d or host.endswith("." + d):
                return platform
    return None


def is_supported_url(url: str) -> bool:
    return detect_platform(url) is not None


def sample_urls_text() -> str:
    return (
        "Contoh URL yang didukung:\n"
        "- TikTok: https://www.tiktok.com/@user/video/123\n"
        "- Douyin: https://www.douyin.com/video/123\n"
        "- Instagram: https://www.instagram.com/p/POST_ID/\n"
        "- Threads: https://www.threads.net/@user/post/123\n"
        "- Facebook: https://www.facebook.com/watch/?v=123\n"
        "- YouTube: https://www.youtube.com/watch?v=VIDEO_ID\n"
    )
