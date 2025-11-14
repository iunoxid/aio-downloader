from __future__ import annotations

import logging

from telegram.ext import Application, ApplicationBuilder

from .context import BotContext
from handlers import register_handlers

logger = logging.getLogger("bot")


def build_app(ctx: BotContext) -> Application:
    builder = ApplicationBuilder().token(ctx.settings.telegram_bot_token)
    try:
        from telegram.ext import AIORateLimiter as _AIORateLimiter  # type: ignore

        builder = builder.rate_limiter(_AIORateLimiter())
    except Exception as e:
        logger.warning(
            'Rate limiter not enabled (%s). Install optional extra: pip install "python-telegram-bot[rate-limiter]==21.6"',
            e,
        )
    app = builder.build()
    register_handlers(app, ctx)
    return app
