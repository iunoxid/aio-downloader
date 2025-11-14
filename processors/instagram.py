from __future__ import annotations

from .generic import process_generic
from bot.context import BotContext


async def process_instagram(ctx: BotContext, *, platform: str, message, url: str, req_id: str, user_id: int) -> None:
    await process_generic(ctx, platform=platform, message=message, url=url, req_id=req_id, user_id=user_id)

