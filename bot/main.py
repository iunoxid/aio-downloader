from __future__ import annotations

import asyncio
import logging
from urllib.parse import urlparse
import time

from dotenv import load_dotenv

from .app import build_app
from .config import load_settings
from .context import BotContext
from .state import CallbackStore, UserSemaphores
from .platforms import SUPPORTED_PLATFORMS


load_dotenv()
settings = load_settings()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s :: %(message)s")
logger = logging.getLogger("bot")


async def main_async():
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN belum diset.")
    if not settings.downloader_api_base_url:
        raise RuntimeError("DOWNLOADER_API_BASE_URL belum diset.")

    ctx = BotContext(
        settings=settings,
        callbacks=CallbackStore(),
        semaphores=UserSemaphores(settings.max_concurrent_per_user),
        started_at=time.time(),
    )
    app = build_app(ctx)
    # Pretty startup summary
    logger.info("================ AIO Downloader Bot ================")
    logger.info("Platforms: %s", ", ".join(sorted(SUPPORTED_PLATFORMS.keys())))
    # Endpoint summary per platform (from YAML):
    try:
        def _host(u: str) -> str:
            try:
                return urlparse(u).netloc or u
            except Exception:
                return u
        eps = []
        for p in sorted(SUPPORTED_PLATFORMS.keys()):
            ep = ctx.settings.endpoints_per_platform.get(p) or ctx.settings.downloader_api_base_url
            eps.append(f"{p}={_host(ep)}")
        logger.info("Endpoints: %s", ", ".join(eps))
    except Exception:
        logger.exception("failed_log_endpoints")
    logger.info("====================================================")
    logger.info("Bot starting... kirim /start ke bot Telegram Anda.")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    try:
        await asyncio.Future()
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main_async())
