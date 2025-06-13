# Voici le fichier complet `main.py` mis à jour avec la suppression auto des vocaux au bout de 5 minutes

import os
import re
import time
import asyncio
import discord
from discord.ext import commands
from discord import ui, app_commands, Interaction, PermissionOverwrite, ButtonStyle
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
ROLE_MUSIC_BOTS = 411916947773587456

notification_interval = 60 * 60  # 1h
last_notification_time = 0
AUTO_DELETE_DELAY_SECONDS = 300  # 5 minutes

active_vocals = {}  # user_id: channel_id


class VocalModal(ui.Modal, title="Création de salon vocal"):
    def __init__(self, role_id: int):
        super().__init__()
        self.role_id = role_id

        self.nom = ui.TextInput(label="Nom du salon", placeholder="ex: Chill Zone", max_length=32)
        self.slots = ui.TextInput(label="Nombre de personnes (1-15)", placeholder="ex: 5", max_length=2)
        self.add_item(self.nom)
        self.add_item(self.slots)

    async def on_submit(self, interaction: Interaction):
        user_id = interaction.user.id
        if user_id in active_vocals:
            await interaction.response.send_message("❌ Tu as déjà un salon vocal actif.", ephemeral=True)
            return

        try:
            nom = self.nom.value
            slots = int(self.slots.value)

            if not 1 <= slots <= 15:
                await interaction.response.send_message("❌ Nombre de slots invalide (1-15).", ephemeral=True)
                return

            guild = interaction.guild
            role = guild.get_role(self.role_id)
            category = guild.get_channel(VOCAL_CATEGORY_ID)
            everyone = guild.default_role
            music_role = guild.get_role(ROLE_MUSIC_BOTS)

            overwrites = {
                everyone: PermissionOverwrite(connect=False),
                role: PermissionOverwrite(connect=True),
                guild.me: PermissionOverwrite(connect=True, manage_channels=True),
                music_role: PermissionOverwrite(connect=True)
            }

            vocal = await guild.create_voice_channel(
                name=nom,
                user_limit=slots,
                overwrites=overwrites,
                category=category
            )

            active_vocals[user_id] = vocal.id

            await interaction.response.send_message(
                f"✅ Salon vocal créé : **{vocal.name}** *(limite {slots}, rôle : <@&{role.id}>)*",
                ephemeral=True
            )

            async def auto_delete():
                await asyncio.sleep(AUTO_DELETE_DELAY_SECONDS)
                if len(vocal.members) == 0:
                    await vocal.delete()
                    if user_id in active_vocals and active_vocals[user_id] == vocal.id:
                        del active_vocals[user_id]
                    print(f"🗑️ Salon vocal supprimé (inactif) : {vocal.name}")

            asyncio.create_task(auto_delete())

        except Exception as e:
            await interaction.response.send_message(f"❌ Erreur : {e}", ephemeral=True)


class CreateVocalView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ui.Button(label="👤 Membres", style=ButtonStyle.primary, custom_id="vocal_membres"))
        self.add_item(ui.Button(label="🛡️ Scrims", style=ButtonStyle.success, custom_id="vocal_scrims"))


@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🌐 Slash commands synchronisées : {len(synced)}")
    except Exception as e:
        print(f"❌ Erreur de synchronisation des slash commands : {e}")

    target_channel = bot.get_channel(1382771825775476746)
    if target_channel:
        try:
            await target_channel.send("🎧 Clique sur un des boutons pour créer un vocal :", view=CreateVocalView())
        except:
            pass


@bot.event
async def on_message(message):
    global last_notification_time

    if message.author.bot:
        return

    if message.channel.id in MEDIA_CHANNEL_IDS:
        has_link = re.search(r'https?://', message.content)
        has_attachment = len(message.attachments) > 0
        has_embed = len(message.embeds) > 0

        if not (has_link or has_attachment or has_embed):
            try:
                await message.delete()
                await message.author.send(
                    "👋 Ton message a été supprimé car ce salon est réservé aux BOT.\n\n"
                    "💬 Tu veux discuter ? Tu as ce salon : <#1378524605165207562>\n"
                    "🔎 Tu recherches des personnes ? C’est par ici : <#1378397438204968981>\n\n"
                    "👉 Si ça ne se lance pas automatiquement, tape la commande `/forcestart`."
                )
            except:
                pass

    if message.channel.id == NOTIF_CHANNEL_ID:
        now = time.time()
        if now - last_notification_time >= notification_interval:
            await message.channel.send(f"<@&{NOTIF_ROLE_ID}>")
            last_notification_time = now

    await bot.process_commands(message)


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


@bot.event
async def on_interaction(interaction: Interaction):
    if interaction.type.name == "component":
        if interaction.data["custom_id"] == "vocal_membres":
            await interaction.response.send_modal(VocalModal(ROLE_MEMBRES))
        elif interaction.data["custom_id"] == "vocal_scrims":
            await interaction.response.send_modal(VocalModal(ROLE_SCRIMS))
    else:
        await bot.process_application_commands(interaction)


TOKEN = os.getenv("TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Token introuvable. Assure-toi qu'il est bien configuré.")

