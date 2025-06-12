import os
import re
import time
import asyncio
import discord
from discord.ext import commands
from discord import ui, app_commands, Interaction, PermissionOverwrite, ButtonStyle, Embed, TextStyle
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ===== CONFIGURATION =====
MEDIA_CHANNEL_IDS = [1371204189908369550, 1370165104943042671]
NOTIF_CHANNEL_ID = 1344287288946982936
NOTIF_ROLE_ID = 1344287286527004770
CREATOR_VOCAL_ID = 1382766373825937429
VOCAL_CATEGORY_ID = 1382767784064323755
ROLE_MEMBRES = 1344287286585458749
ROLE_SCRIMS = 1378428377412931644
ROLE_NSFW = 1344287286527004772

ROLE_CHOICES = {
    "Membres": ROLE_MEMBRES,
    "Scrims": ROLE_SCRIMS,
    "NSFW": ROLE_NSFW,
}

notification_interval = 60 * 60  # 1h
last_notification_time = 0

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🌐 Slash commands synchronisées : {len(synced)}")
    except Exception as e:
        print(f"❌ Erreur de synchronisation des slash commands : {e}")

@bot.event
async def on_message(message):
    global last_notification_time

    if message.author.bot:
        return

    if message.channel.id in MEDIA_CHANNEL_IDS or message.channel.id == NOTIF_CHANNEL_ID:
        print(f"[DEBUG] Message reçu dans salon {message.channel.id} : {message.content}")

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

    if message.channel.id == NOTIF_CHANNEL_ID:
        now = time.time()
        if now - last_notification_time >= notification_interval:
            try:
                await message.channel.send(f"<@&{NOTIF_ROLE_ID}>")
                last_notification_time = now
                print("🔔 Mention @notification envoyée.")
            except Exception as notif_error:
                print(f"❌ Erreur notification : {notif_error}")
        else:
            print("⏱️ Notification ignorée (moins d'1h depuis la dernière).")

    await bot.process_commands(message)

class VocalModal(ui.Modal, title="Création de salon vocal"):
    nom = ui.TextInput(label="Nom du salon", placeholder="ex: Chill Zone", max_length=32)
    slots = ui.TextInput(label="Nombre de personnes (1-15)", placeholder="ex: 5", max_length=2)

    def __init__(self):
        super().__init__(timeout=300)
        self.role_select = ui.Select(
            placeholder="Choisir un rôle autorisé",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label="Membres", value="Membres"),
                discord.SelectOption(label="Scrims", value="Scrims"),
                discord.SelectOption(label="NSFW", value="NSFW")
            ]
        )
        self.add_item(self.role_select)

    async def on_submit(self, interaction: Interaction):
        try:
            nom = self.nom.value
            slots = int(self.slots.value)
            role_label = self.role_select.values[0]

            if not 1 <= slots <= 15:
                await interaction.response.send_message("❌ Nombre de slots invalide (1-15).", ephemeral=True)
                return

            role = interaction.guild.get_role(ROLE_CHOICES[role_label])
            category = interaction.guild.get_channel(VOCAL_CATEGORY_ID)
            everyone = interaction.guild.default_role

            overwrites = {
                everyone: PermissionOverwrite(connect=False),
                role: PermissionOverwrite(connect=True),
                interaction.guild.me: PermissionOverwrite(connect=True, manage_channels=True)
            }

            vocal = await interaction.guild.create_voice_channel(
                name=nom,
                user_limit=slots,
                overwrites=overwrites,
                category=category
            )

            await interaction.response.send_message(f"✅ Salon vocal créé : **{vocal.name}** *(limite {slots}, rôle : <@&{role.id}>)*", ephemeral=True)

            async def auto_delete_if_empty():
                await asyncio.sleep(180)
                if len(vocal.members) == 0:
                    await vocal.delete()
                    print(f"🗑️ Salon vocal supprimé (inactif) : {vocal.name}")

            asyncio.create_task(auto_delete_if_empty())

        except Exception as e:
            await interaction.response.send_message(f"❌ Erreur : {e}", ephemeral=True)

@bot.tree.command(name="vocal", description="Créer un salon vocal avec un formulaire pop-up")
async def vocal_slash(interaction: Interaction):
    await interaction.response.send_modal(VocalModal())

@bot.command(name="vocs")
@commands.has_permissions(manage_guild=True)
async def vocs(ctx):
    category = ctx.guild.get_channel(VOCAL_CATEGORY_ID)
    if not category:
        await ctx.send("❌ Catégorie introuvable.")
        return

    vocaux = [c for c in category.voice_channels if c.id != CREATOR_VOCAL_ID]
    if not vocaux:
        await ctx.send("📭 Aucun salon vocal temporaire actif.")
        return

    await ctx.send(f"📋 Liste des vocaux dans **{category.name}** :")
    for vocal in vocaux:
        await ctx.send(f"🔊 **{vocal.name}** – `{len(vocal.members)} connecté(s)`")

TOKEN = os.getenv("TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Token introuvable. Assure-toi qu'il est bien configuré.")
