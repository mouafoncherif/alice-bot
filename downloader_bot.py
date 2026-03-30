"""
🎬 DownloaderBot Telegram — Téléchargement vidéo/audio multi-plateformes
Dépendances : pip install python-telegram-bot==21.3 yt-dlp
Système      : sudo apt install ffmpeg -y
"""

import os
import logging
import re
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler,
    ContextTypes, filters
)

# ── Configuration ─────────────────────────────────────────────────────────────
TOKEN = "8669159047:AAG9l6UJJpb2AhxMalify6mx_Sj_F2mcBL8"  # Remplacer par votre token BotFather
DOWNLOAD_DIR = "./downloads"
MAX_FILE_SIZE_MB = 50  # Limite Telegram pour les bots (50 MB)

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ── États ─────────────────────────────────────────────────────────────────────
CHOIX_FORMAT, CHOIX_QUALITE = range(2)

# ── Détection de plateforme ───────────────────────────────────────────────────
PLATFORMS = {
    "youtube": (r"(youtube\.com|youtu\.be)", "▶️ YouTube"),
    "tiktok":  (r"tiktok\.com", "🎵 TikTok"),
    "instagram": (r"instagram\.com", "📸 Instagram"),
    "facebook": (r"(facebook\.com|fb\.watch)", "📘 Facebook"),
}

def detect_platform(url: str) -> str:
    for key, (pattern, label) in PLATFORMS.items():
        if re.search(pattern, url, re.IGNORECASE):
            return label
    return "🌐 Autre"

def is_valid_url(url: str) -> bool:
    return url.startswith("http://") or url.startswith("https://")

# ── /start ────────────────────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 *Bienvenue sur DownloaderBot !*\n\n"
        "Envoie-moi un lien vidéo de :\n"
        "▶️ YouTube  🎵 TikTok  📸 Instagram  📘 Facebook\n"
        "_(et bien d'autres plateformes)_\n\n"
        "Je te proposerai ensuite le format et la qualité.",
        parse_mode="Markdown"
    )

# ── Réception du lien ─────────────────────────────────────────────────────────
async def receive_link(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not is_valid_url(url):
        await update.message.reply_text("❌ Lien invalide. Envoie un lien commençant par http:// ou https://")
        return ConversationHandler.END

    platform = detect_platform(url)
    ctx.user_data["url"] = url
    ctx.user_data["platform"] = platform

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 Vidéo", callback_data="format_video"),
         InlineKeyboardButton("🎵 Audio MP3", callback_data="format_audio")],
        [InlineKeyboardButton("❌ Annuler", callback_data="cancel")],
    ])

    await update.message.reply_text(
        f"🔗 Lien détecté : *{platform}*\n\nQuel format veux-tu ?",
        parse_mode="Markdown",
        reply_markup=kb
    )
    return CHOIX_FORMAT

# ── Choix du format ───────────────────────────────────────────────────────────
async def choix_format(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    fmt = query.data  # format_video ou format_audio

    ctx.user_data["format"] = fmt

    if fmt == "format_audio":
        # Pas de choix de qualité pour l'audio
        await query.edit_message_text("⏳ Téléchargement en cours... patiente un instant 🎵")
        await do_download(query, ctx)
        return ConversationHandler.END

    # Choix qualité pour la vidéo
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 360p", callback_data="q_360"),
         InlineKeyboardButton("📺 720p", callback_data="q_720"),
         InlineKeyboardButton("🖥 1080p", callback_data="q_1080")],
        [InlineKeyboardButton("⭐ Meilleure dispo", callback_data="q_best")],
        [InlineKeyboardButton("❌ Annuler", callback_data="cancel")],
    ])
    await query.edit_message_text("🎬 Quelle qualité ?", reply_markup=kb)
    return CHOIX_QUALITE

# ── Choix de la qualité ───────────────────────────────────────────────────────
async def choix_qualite(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ctx.user_data["qualite"] = query.data  # q_360, q_720, q_1080, q_best
    await query.edit_message_text("⏳ Téléchargement en cours... patiente un instant 🎬")
    await do_download(query, ctx)
    return ConversationHandler.END

# ── Téléchargement ────────────────────────────────────────────────────────────
async def do_download(query, ctx: ContextTypes.DEFAULT_TYPE):
    url = ctx.user_data.get("url")
    fmt = ctx.user_data.get("format")
    qualite = ctx.user_data.get("qualite", "q_best")
    chat_id = query.message.chat_id

    # Mapping qualité → format yt-dlp (formats pré-mergés, pas besoin de ffmpeg)
    quality_map = {
        "q_360":  "best[height<=360]/best[height<=480]/best",
        "q_720":  "best[height<=720]/best[height<=480]/best",
        "q_1080": "best[height<=1080]/best[height<=720]/best",
        "q_best": "best",
    }

    output_path = os.path.join(DOWNLOAD_DIR, f"{chat_id}_%(title).50s.%(ext)s")

    if fmt == "format_audio":
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_path,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "quiet": True,
        }
    else:
        ydl_opts = {
            "format": quality_map.get(qualite, "bestvideo+bestaudio/best"),
            "outtmpl": output_path,
            "merge_output_format": "mp4",
            "quiet": True,
        }

    try:
        # Téléchargement
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "vidéo")

        # Trouver le fichier téléchargé
        downloaded = None
        for f in os.listdir(DOWNLOAD_DIR):
            if f.startswith(str(chat_id)):
                downloaded = os.path.join(DOWNLOAD_DIR, f)
                break

        if not downloaded:
            await query.message.reply_text("❌ Fichier introuvable après téléchargement.")
            return

        # Vérifier la taille
        size_mb = os.path.getsize(downloaded) / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            os.remove(downloaded)
            await query.message.reply_text(
                f"⚠️ Fichier trop lourd ({size_mb:.1f} MB).\n"
                f"Telegram limite les bots à {MAX_FILE_SIZE_MB} MB.\n\n"
                "💡 Essaie une qualité plus basse (360p) ou un extrait audio."
            )
            return

        # Envoyer le fichier
        await query.message.reply_text(f"✅ *{title}*\n📤 Envoi en cours...", parse_mode="Markdown")

        with open(downloaded, "rb") as f:
            if fmt == "format_audio":
                await ctx.bot.send_audio(chat_id=chat_id, audio=f, title=title)
            else:
                await ctx.bot.send_video(chat_id=chat_id, video=f, supports_streaming=True)

        os.remove(downloaded)

    except yt_dlp.utils.DownloadError as e:
        err = str(e)
        if "Private" in err or "login" in err.lower():
            msg = "🔒 Cette vidéo est privée ou nécessite une connexion."
        elif "copyright" in err.lower():
            msg = "⛔ Vidéo bloquée pour raisons de droits d'auteur."
        else:
            msg = f"❌ Erreur de téléchargement :\n`{err[:200]}`"
        await query.message.reply_text(msg, parse_mode="Markdown")

    except Exception as e:
        await query.message.reply_text(f"❌ Erreur inattendue : `{str(e)[:200]}`", parse_mode="Markdown")

    finally:
        # Nettoyage au cas où
        for f in os.listdir(DOWNLOAD_DIR):
            if f.startswith(str(chat_id)):
                try:
                    os.remove(os.path.join(DOWNLOAD_DIR, f))
                except Exception:
                    pass
        ctx.user_data.clear()

# ── Annulation ────────────────────────────────────────────────────────────────
async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("❌ Annulé.")
    else:
        await update.message.reply_text("❌ Annulé.")
    ctx.user_data.clear()
    return ConversationHandler.END

# ── /help ─────────────────────────────────────────────────────────────────────
async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Comment utiliser DownloaderBot :*\n\n"
        "1️⃣ Copie le lien d'une vidéo\n"
        "2️⃣ Colle-le ici et envoie\n"
        "3️⃣ Choisis *Vidéo* ou *Audio MP3*\n"
        "4️⃣ Choisis la qualité (pour les vidéos)\n"
        "5️⃣ Reçois ton fichier ! 🎉\n\n"
        "✅ *Plateformes supportées :*\n"
        "▶️ YouTube  🎵 TikTok  📸 Instagram  📘 Facebook\n"
        "Twitter/X, Dailymotion, Vimeo, Reddit et +1000 autres\n\n"
        "⚠️ *Limite :* fichiers jusqu'à 50 MB\n"
        "💡 *Astuce :* pour les longues vidéos YouTube, préfère 360p ou MP3",
        parse_mode="Markdown"
    )

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, receive_link)],
        states={
            CHOIX_FORMAT:  [CallbackQueryHandler(choix_format,  pattern="^format_")],
            CHOIX_QUALITE: [CallbackQueryHandler(choix_qualite, pattern="^q_")],
        },
        fallbacks=[
            CallbackQueryHandler(cancel, pattern="^cancel$"),
            CommandHandler("cancel", cancel),
        ],
        per_user=True,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(conv)

    logging.info("🎬 DownloaderBot démarré !")
    app.run_polling()

if __name__ == "__main__":
    main()
