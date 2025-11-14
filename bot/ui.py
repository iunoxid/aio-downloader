from __future__ import annotations

from typing import Any, List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .context import BotContext
from .media_utils import iter_medias, is_audio


def build_summary_keyboard(ctx: BotContext, result: dict, *, user_id: int, chat_id: int, message_id: int | None = None) -> InlineKeyboardMarkup | None:
    buttons: List[List[InlineKeyboardButton]] = []
    # audio-only buttons (per requirements)
    for idx, m in iter_medias(result):
        url = m.get("url") or m.get("download_url") or ""
        ext = (m.get("extension") or m.get("ext") or "").lower()
        if is_audio(m) or ext == "mp3":
            token = ctx.callbacks.new_audio_token(
                user_id=user_id,
                chat_id=chat_id,
                message_id=message_id or -1,
                media_url=url,
                filename_hint=m.get("filename") or f"audio_{idx}.{ext or 'mp3'}",
            )
            buttons.append([
                InlineKeyboardButton(text="Download MP3", callback_data=f"mp3:{token}"),
                InlineKeyboardButton(text="Buka di Browser", url=url),
            ])

    # Fallback open original link if present
    if (result.get("url")):
        buttons.append([InlineKeyboardButton(text="Buka Konten Asli", url=result["url"])])

    # Top-level mp3 link support
    top_mp3 = result.get("mp3")
    if isinstance(top_mp3, str) and top_mp3.startswith("http"):
        token = ctx.callbacks.new_audio_token(
            user_id=user_id,
            chat_id=chat_id,
            message_id=message_id or -1,
            media_url=top_mp3,
            filename_hint="audio.mp3",
        )
        buttons.append([
            InlineKeyboardButton(text="Download MP3", callback_data=f"mp3:{token}"),
            InlineKeyboardButton(text="Buka di Browser", url=top_mp3),
        ])

    return InlineKeyboardMarkup(buttons) if buttons else None

