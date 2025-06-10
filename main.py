import os
import re
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ID du salon média à surveiller — à modifier avec l'ID réel
MEDIA_CHANNEL_ID =  # Remplace ceci par le bon ID

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
        except Exception as e:
            print(f"Erreur lors de la suppression : {e}")

    await bot.process_commands(message)

# Récupération et lancement du token
TOKEN = os.getenv("TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Token introuvable. Assure-toi qu'il est bien dans le fichier .env.")
