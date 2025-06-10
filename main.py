import os
import re
import time
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env (inutile sur Railway, mais ok si local)
load_dotenv()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 🔧 ID du salon média à surveiller
MEDIA_CHANNEL_ID = 1371204189908369550

# 🔔 ID du salon à notifier (quand un message est posté)
NOTIF_CHANNEL_ID = 137888888888888888  # remplace par ton salon cible
NOTIF_ROLE_ID = 1344287288946982936     # remplace par l'ID du rôle @notification

# ⏱️ Intervalle entre mentions en secondes (1h)
notification_interval = 60 * 60
last_notification_time = 0

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")

@bot.event
async def on_message(message):
    global last_notification_time

    if message.author.bot:
        return

    # 🎯 Si message dans le salon média
    if message.channel.id == MEDIA_CHANNEL_ID:
        has_link = re.search(r'https?://', message.content)
        has_attachment = len(message.attachments) > 0
        has_embed = len(message.embeds) > 0

        if not (has_link or has_attachment or has_embed):
            try:
                await message.delete()
                print(f"❌ Message supprimé : {message.content}")

                # ✅ MP à l’auteur
                try:
                    await message.author.send(
                        "👋 Ton message a été supprimé car ce salon est réservé aux BOT.\n\n"
                        "💬 Tu veux discuter ? Tu as ce salon : <#1378524605165207562>\n"
                        "🔎 Tu recherches des personnes ? C’est par ici : <#1378397438204968981>\n\n"
                        "👉 Si ça ne se lance pas automatiquement, tape la commande `/forcestart`."
                    )
                except Exception as dm_error:
                    print(f"⚠️ Impossible d'envoyer un DM à {message.author}: {dm_error}")

            except Exception as e:
                print(f"Erreur lors de la suppression : {e}")

    # 🔔 Notification dans un salon spécifique avec délai de 1h
    elif message.channel.id == NOTIF_CHANNEL_ID:
        now = time.time()
        if now - last_notification_time >= notification_interval:
            try:
                await message.channel.send(f"<@&{1344287286527004770}>")
                last_notification_time = now
                print("🔔 Mention @notification envoyée.")
            except Exception as notif_error:
                print(f"❌ Erreur lors de l'envoi de la notification : {notif_error}")
        else:
            print("⏱️ Notification ignorée (déjà envoyée dans l'heure).")

    await bot.process_commands(message)

# 🎯 Lancer le bot
TOKEN = os.getenv("TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Token introuvable. Assure-toi qu'il est bien dans le fichier .env ou dans Railway.")

