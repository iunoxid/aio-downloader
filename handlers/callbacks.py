from __future__ import annotations

import os
from typing import List

import aiohttp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes

import io
from bot.context import BotContext
from bot.downloader_client import DownloaderClient, TooLargeError


async def _on_mp3_callback(ctx: BotContext, update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.callback_query:
        return
    cq = update.callback_query
    user = cq.from_user
    data = cq.data or ""
    if not data.startswith("mp3:"):
        return
    token = data.split(":", 1)[1]

    task = ctx.callbacks.get_audio_task(token)
    if not task:
        await cq.answer("Permintaan MP3 sudah kadaluarsa.", show_alert=False)
        return
    if user.id != task.user_id:
        await cq.answer("Tombol ini bukan milik Anda.", show_alert=True)
        return
    if not ctx.callbacks.mark_in_progress(token):
        await cq.answer("Sedang menyiapkan MP3...", show_alert=False)
        return

    # Update button label to show progress
    try:
        if cq.message and cq.message.reply_markup:
            new_rows: List[List[InlineKeyboardButton]] = []
            for row in cq.message.reply_markup.inline_keyboard:
                new_row: List[InlineKeyboardButton] = []
                for b in row:
                    if b.callback_data == data:
                        new_row.append(InlineKeyboardButton(text="Menyiapkan MP3...", callback_data=data))
                    else:
                        new_row.append(b)
                new_rows.append(new_row)
            await cq.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(new_rows))
    except Exception:
        pass

    await cq.answer("Menyiapkan MP3...", show_alert=False)

    api = DownloaderClient(
        base_url=os.getenv("DOWNLOADER_API_BASE_URL_AUDIO") or ctx.settings.downloader_api_base_url,
        api_key=ctx.settings.downloader_api_key,
        connect_timeout=ctx.settings.http_connect_timeout,
        read_timeout=ctx.settings.http_read_timeout,
        total_timeout=ctx.settings.http_total_timeout,
    )

    try:
        async with aiohttp.ClientSession() as session:
            size = await api.head_size(session, task.media_url)
            if size is not None and size > ctx.settings.max_upload_bytes:
                await context.bot.send_message(
                    chat_id=task.chat_id,
                    text=f"File MP3 terlalu besar untuk diupload ({size} bytes). Gunakan tautan berikut:",
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text="Buka di Browser", url=task.media_url)]]
                    ),
                )
            else:
                try:
                    data_bytes = await api.download_to_bytes(session, task.media_url, ctx.settings.max_upload_bytes)
                except TooLargeError as e:
                    await context.bot.send_message(
                        chat_id=task.chat_id,
                        text=f"File MP3 terlalu besar untuk diupload ({e.size} bytes). Tautan dikirim.",
                        reply_markup=InlineKeyboardMarkup(
                            [[InlineKeyboardButton(text="Buka di Browser", url=task.media_url)]]
                        ),
                    )
                else:
                    bio = io.BytesIO(data_bytes)
                    bio.name = task.filename_hint or "audio.mp3"
                    await context.bot.send_audio(chat_id=task.chat_id, audio=bio)
    except Exception:
        await context.bot.send_message(chat_id=task.chat_id, text="Gagal menyiapkan MP3.")
    finally:
        pass

    # Update button to success
    try:
        if cq.message and cq.message.reply_markup:
            new_rows: List[List[InlineKeyboardButton]] = []
            for row in cq.message.reply_markup.inline_keyboard:
                new_row: List[InlineKeyboardButton] = []
                for b in row:
                    if b.callback_data == data:
                        new_row.append(InlineKeyboardButton(text="MP3 siap", callback_data=None))
                    else:
                        new_row.append(b)
                new_rows.append(new_row)
            await cq.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(new_rows))
    except Exception:
        pass


def mp3_callback_handler(ctx: BotContext) -> CallbackQueryHandler:
    return CallbackQueryHandler(lambda u, c: _on_mp3_callback(ctx, u, c), pattern=r"^mp3:")

