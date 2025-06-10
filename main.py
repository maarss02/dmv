import os
import re
import time
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Charger les variables d'environnement (inutile sur Railway, mais fonctionne localement)
load_dotenv()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 🎯 ID des salons à surveiller pour suppression (média uniquement)
MEDIA_CHANNEL_IDS = [1371204189908369550, 1370165104943042671]

# 🔔 ID du salon à notifier et rôle à ping
NOTIF_CHANNEL_ID = 137888888888888888  # ⬅️ À remplacer par ton vrai salon de notif
NOTIF_ROLE_ID = 137899999999999999     # ⬅️ À remplacer par l’ID du rôle @notification

# ⏱️ Intervalle entre mentions (en secondes)
notification_interval = 60 * 60  # 1h
last_notification_time = 0

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")

@bot.event
async def on_message(message):
    global last_notification_time

    if message.author.bot:
        return

    # 🎯 Filtrage des salons média (suppression si pas lien/media)
    if message.channel.id in MEDIA_CHANNEL_IDS:
        has_link = re.search(r'https?://', message.content)
        has_attachment = len(message.attachments) > 0
        has_embed = len(message.embeds) > 0

        if not (has_link or has_attachment or has_embed):
            try:
                await message.delete()
                print(f"❌ Message supprimé dans salon {message.channel.name} : {message.content}")

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

    # 🔔 Notification dans un salon spécifique (1 fois par heure)
    elif message.channel.id == NOTIF_CHANNEL_ID:
        now = time.time()
        if now - last_notification_time >= notification_interval:
            try:
                await message.channel.send(f"<@&{NOTIF_ROLE_ID}>")
                last_notification_time = now
                print("🔔 Mention @notification envoyée.")
            except Exception as notif_error:
                print(f"❌ Erreur lors de l'envoi de la notification : {notif_error}")
        else:
            print("⏱️ Notification ignorée (moins d'1h depuis la dernière).")

    await bot.process_commands(message)

# 🔐 Lancer le bot
TOKEN = os.getenv("TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Token introuvable. Assure-toi qu'il est bien dans Railway (Variables).")


