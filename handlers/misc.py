from __future__ import annotations

import time
from typing import List

from telegram import Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from bot.context import BotContext


def _format_seconds(secs: float) -> str:
    s = int(secs)
    d, s = divmod(s, 86400)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    parts: List[str] = []
    if d:
        parts.append(f"{d}d")
    if h or parts:
        parts.append(f"{h}h")
    if m or parts:
        parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts)


async def on_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        target = update.callback_query.message
    else:
        target = update.effective_message
    if not target:
        return
    text = (
        "🤝 Bantuan\n"
        "- Kirim URL dari platform yang didukung\n"
        "- Bot akan menyiapkan media/tombol unduh\n"
        "- YouTube: bot kirim tombol kualitas (tanpa upload video)\n"
        "- Jika ukuran melebihi batas upload, bot mem‑post tautan\n"
    )
    await target.reply_text(text)


async def on_runtime(ctx: BotContext, update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        target = update.callback_query.message
    else:
        target = update.effective_message
    if not target:
        return
    uptime = _format_seconds(time.time() - ctx.started_at)
    s = ctx.settings
    mb = s.max_upload_bytes / (1024 * 1024)
    text = (
        "🕒 Runtime Bot\n"
        f"- Uptime: {uptime}\n"
        f"- Concurrency/user: {s.max_concurrent_per_user}\n"
        f"- Max upload: {mb:.0f} MB\n"
    )
    await target.reply_text(text)


def help_callback_handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(lambda u, c: on_help(u, c), pattern=r"^help$")


def runtime_callback_handler(ctx: BotContext) -> CallbackQueryHandler:
    return CallbackQueryHandler(lambda u, c: on_runtime(ctx, u, c), pattern=r"^runtime$")


def help_command_handler() -> CommandHandler:
    return CommandHandler("help", on_help)


def runtime_command_handler(ctx: BotContext) -> CommandHandler:
    return CommandHandler("runtime", lambda u, c: on_runtime(ctx, u, c))
