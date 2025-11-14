from __future__ import annotations

from telegram.ext import Application

from bot.context import BotContext
from .start import start_handler
from .callbacks import mp3_callback_handler
from .text import text_handler
from .misc import help_callback_handler, runtime_callback_handler, help_command_handler, runtime_command_handler


def register_handlers(app: Application, ctx: BotContext) -> None:
    app.add_handler(start_handler())
    app.add_handler(help_command_handler())
    app.add_handler(runtime_command_handler(ctx))
    app.add_handler(help_callback_handler())
    app.add_handler(runtime_callback_handler(ctx))
    app.add_handler(mp3_callback_handler(ctx))
    app.add_handler(text_handler(ctx))
