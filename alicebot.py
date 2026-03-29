import random
import asyncio
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Configuration des logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 🔑 TON TOKEN (sera pris des variables d'environnement)
import os
TOKEN = os.getenv("BOT_TOKEN")

# ❤️ CHAT ID DE ALICE
ALICE_CHAT_ID = 5732902032

# 💌 Tous tes messages
messages = [
    "Alice… même quand je ne parle pas, je pense à toi ❤️",
    "Chaque seconde sans toi est une seconde en trop 💔",
    "Tu es ma paix dans ce chaos 🌙",
    "Je n'ai pas besoin de te voir pour te sentir près de moi 💫",
    "Lyra… tu es mon étoile ✨",
    "Je t'aime plus que les mots ne peuvent le dire 💖",
    "Allez… même quand je ne parle pas, je pense à toi 💕",
    "🌅 Bonjour Alice… Tu es plus forte que ce que tu penses.",
    "☀️ Réveille-toi belle âme. Tu mérites tout le bonheur du monde.",
    "💪 Tu as survécu à 100% de tes mauvais jours.",
    "🌻 N'oublie jamais ta valeur.",
    "✨ Le meilleur est à venir. Garde la tête haute.",
    "🌸 Avance un pas à la fois, je suis là.",
    "🌤️ Comment se passe ta journée ? Prends soin de toi.",
    "💖 Tu es tellement aimée.",
    "🎯 Tu es une guerrière.",
    "📚 Ferme les mauvais chapitres, ouvre-en de meilleurs.",
    "💫 Tu es complète par toi-même.",
    "🦋 Cette épreuve te rendra plus forte.",
    "🌙 Repose-toi bien, je veille sur toi.",
    "⭐ Dors bien, demain sera plus doux.",
    "💪 Chaque jour qui passe te rapproche de ta renaissance.",
    "🌹 Les plus belles fleurs naissent dans les sols les plus durs.",
    "🎀 Demain est une nouvelle chance.",
    "💕 Laisse tes peines s'envoler."
]

# 🔔 ENVOI AUTO TOUTES LES HEURES
async def send_auto_messages(app):
    """Envoie un message toutes les heures"""
    logger.info("🔄 Envoi automatique toutes les heures - DÉMARRÉ")

    last_hour = -1

    while True:
        try:
            now = datetime.now()
            current_hour = now.hour

            if current_hour != last_hour:
                message = random.choice(messages)
                final_message = f"💕 {message}\n\n⏰ {current_hour}:00"

                await app.bot.send_message(chat_id=ALICE_CHAT_ID, text=final_message)
                logger.info(f"✅ Message envoyé à Alice à {current_hour}h")

                last_hour = current_hour

            await asyncio.sleep(30)

        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
            await asyncio.sleep(60)

# Commandes
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💖 Bot actif !\n\n"
        "Commandes:\n"
        "/id - Récupérer ton chat ID\n"
        "/status - État du bot\n"
        "/next - Aperçu du prochain message\n"
        "/send [texte] - Envoyer à Alice\n"
        "/love - Message aléatoire"
    )

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    await update.message.reply_text(f"📌 Ton chat_id est : `{chat_id}`")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    await update.message.reply_text(
        f"✅ Bot actif !\n"
        f"⏰ Heure: {now.strftime('%H:%M:%S')}\n"
        f"📨 Envoi à: {ALICE_CHAT_ID}\n"
        f"💬 {len(messages)} messages disponibles"
    )

async def next_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    preview = random.choice(messages)
    await update.message.reply_text(f"📝 Exemple de message:\n\n💕 {preview}")

async def love(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = random.choice(messages)
    await update.message.reply_text(f"💌 {message}")

async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if args:
        custom_message = " ".join(args)
        await update.message.reply_text(f"✅ Envoyé à Alice: {custom_message}")
        await context.bot.send_message(chat_id=ALICE_CHAT_ID, text=f"💌 {custom_message}")
    else:
        await update.message.reply_text("Usage: /send [message]")

# 🚀 MAIN
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", get_id))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("next", next_message))
    app.add_handler(CommandHandler("love", love))
    app.add_handler(CommandHandler("send", send_message))

    logger.info("🚀 Bot démarré sur Railway !")

    async def post_init(application):
        asyncio.create_task(send_auto_messages(application))
        logger.info("✨ Envoi automatique activé")

    app.post_init = post_init
    app.run_polling()

if __name__ == "__main__":
    main()
