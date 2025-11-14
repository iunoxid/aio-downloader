from __future__ import annotations

from telegram.ext import CommandHandler, ContextTypes
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton

from bot.platforms import sample_urls_text


async def _start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    msg = []
    msg.append("👋 Selamat datang di AIO Downloader Bot!")
    msg.append("")
    msg.append("✨ Dukungan platform:")
    msg.append("- TikTok • Douyin • Instagram • Threads • Facebook • YouTube")
    msg.append("")
    msg.append("📌 Cara pakai:")
    msg.append("1) Kirim URL konten ke sini")
    msg.append("2) Bot akan menyiapkan media atau tombol unduh")
    msg.append("   • YouTube: bot mengirim tombol kualitas (tanpa upload video)")
    msg.append("")
    msg.append("ℹ️ Catatan:")
    msg.append("- Bot tidak menyimpan file")
    msg.append("- Hormati hak cipta & ToS platform")
    msg.append("- Jika ukuran melebihi batas upload Telegram, bot mengirim tautan langsung")
    msg.append("")
    msg.append(sample_urls_text().strip())
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text="Bantuan", callback_data="help"),
            InlineKeyboardButton(text="Runtime", callback_data="runtime"),
        ]
    ])
    await update.message.reply_text("\n".join(msg), reply_markup=kb)


def start_handler() -> CommandHandler:
    return CommandHandler("start", _start)
