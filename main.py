import os
import re
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env (inutile sur Railway, mais ok si local)
load_dotenv()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ID du salon média à surveiller — à modifier avec l'ID réel
MEDIA_CHANNEL_ID = 1371204189908369550

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id != MEDIA_CHANNEL_ID:
        return

    # Vérifie si le message contient un lien, une pièce jointe ou un embed
    has_link = re.search(r'https?://', message.content)
    has_attachment = len(message.attachments) > 0
    has_embed = len(message.embeds) > 0

    if not (has_link or has_attachment or has_embed):
        try:
            await message.delete()
            print(f"❌ Message supprimé : {message.content}")

            # ✅ Envoie un message privé à l’auteur
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

    await bot.process_commands(message)

# Récupération et lancement du token
TOKEN = os.getenv("TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Token introuvable. Assure-toi qu'il est bien dans le fichier .env ou dans Railway.")

