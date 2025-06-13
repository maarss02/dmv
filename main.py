import os
import re
import time
import asyncio
import discord
from discord.ext import commands
from discord import ui, Interaction, ButtonStyle, TextStyle, Embed, PermissionOverwrite
from dotenv import load_dotenv

# === CONFIGURATION ===
MEDIA_CHANNEL_IDS = [1371204189908369550, 1370165104943042671]
NOTIF_CHANNEL_ID = 1344287288946982936
NOTIF_ROLE_ID = 1344287286527004770
CREATOR_BUTTON_CHANNEL = 1382771825775476746
VOCAL_CATEGORY_ID = 1382767784064323755
ROLE_MEMBRES = 1344287286585458749
ROLE_SCRIMS = 1378428377412931644
ROLE_BOT_MUSIC = 1345877829811699755

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

active_vocals = {}
notification_interval = 60 * 60  # 1h
last_notification_time = 0

class VocalModal(ui.Modal, title="Créer un salon vocal"):
    nom = ui.TextInput(label="Nom du salon", placeholder="ex: Chill Zone", max_length=32)
    slots = ui.TextInput(label="Nombre de personnes (1-15)", placeholder="ex: 5", max_length=2)

    def __init__(self, role_id: int, user_id: int):
        super().__init__(timeout=300)
        self.role_id = role_id
        self.user_id = user_id

    async def on_submit(self, interaction: Interaction):
        try:
            nom = self.nom.value
            slots = int(self.slots.value)

            if not 1 <= slots <= 15:
                await interaction.response.send_message("❌ Nombre de slots invalide (1-15).", ephemeral=True)
                return

            if self.user_id in active_vocals:
                await interaction.response.send_message("❌ Tu as déjà un salon actif.", ephemeral=True)
                return

            guild = interaction.guild
            await guild.chunk()  # charge les membres si besoin
            category = guild.get_channel(VOCAL_CATEGORY_ID)
            if not category:
                await interaction.response.send_message("❌ Erreur : catégorie introuvable.", ephemeral=True)
                return

            member = guild.get_member(self.user_id)
            if not member:
                await interaction.response.send_message("❌ Impossible de retrouver ton profil sur le serveur.", ephemeral=True)
                return

            role = guild.get_role(self.role_id)
            if not role:
                await interaction.response.send_message("❌ Impossible de retrouver le rôle sélectionné.", ephemeral=True)
                return

            bot_music_role = guild.get_role(ROLE_BOT_MUSIC)
            if not bot_music_role:
                await interaction.response.send_message("❌ Impossible de retrouver le rôle des bots musique.", ephemeral=True)
                return

            everyone = guild.default_role

            overwrites = {
                everyone: PermissionOverwrite(connect=False),
                role: PermissionOverwrite(connect=True),
                bot_music_role: PermissionOverwrite(connect=True),
                guild.me: PermissionOverwrite(connect=True, manage_channels=True)
            }

            vocal = await guild.create_voice_channel(
                name=nom,
                user_limit=slots,
                overwrites=overwrites,
                category=category
            )

            active_vocals[self.user_id] = vocal.id

            await interaction.response.send_message(
                f"✅ Salon vocal **{nom}** créé avec succès (limite {slots}, rôle : <@&{role.id}>)",
                ephemeral=True
            )

            async def auto_delete():
                await asyncio.sleep(300)
                if len(vocal.members) == 0:
                    await vocal.delete()
                    if self.user_id in active_vocals and active_vocals[self.user_id] == vocal.id:
                        del active_vocals[self.user_id]
                    print(f"🗑️ Salon vocal supprimé (inactif) : {vocal.name}")

            asyncio.create_task(auto_delete())

        except Exception as e:
            await interaction.response.send_message(f"❌ Erreur : {e}", ephemeral=True)

class RoleChoiceView(ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        self.user_id = user_id

    @ui.button(label="👤 Membres", style=ButtonStyle.primary)
    async def membre_btn(self, interaction: Interaction, button: ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("Ce menu ne t'est pas destiné.", ephemeral=True)
        await interaction.response.send_modal(VocalModal(role_id=ROLE_MEMBRES, user_id=self.user_id))

    @ui.button(label="🛡️ Scrims", style=ButtonStyle.success)
    async def scrim_btn(self, interaction: Interaction, button: ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("Ce menu ne t'est pas destiné.", ephemeral=True)
        await interaction.response.send_modal(VocalModal(role_id=ROLE_SCRIMS, user_id=self.user_id))

class CreateVocalView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="🎧 Créer un vocal", style=ButtonStyle.success)
    async def create_vocal_button(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_message(
            "Sélectionne le rôle autorisé à rejoindre ton salon :",
            view=RoleChoiceView(user_id=interaction.user.id),
            ephemeral=True
        )

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")
    try:
        channel = bot.get_channel(CREATOR_BUTTON_CHANNEL)
        async for msg in channel.history(limit=10):
            if msg.author == bot.user:
                await msg.delete()
        await channel.send("🎧 Clique ci-dessous pour créer ton salon vocal :", view=CreateVocalView())
    except Exception as e:
        print(f"❌ Erreur affichage bouton vocal : {e}")

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
                try:
                    await message.author.send(
                        "👋 Ton message a été supprimé car ce salon est réservé aux BOT.\n\n"
                        "💬 Tu veux discuter ? Tu as ce salon : <#1378524605165207562>\n"
                        "🔎 Tu recherches des personnes ? C’est par ici : <#1378397438204968981>\n\n"
                        "👉 Si ça ne se lance pas automatiquement, tape la commande `/forcestart`."
                    )
                except Exception:
                    pass
            except Exception as e:
                print(f"Erreur suppression message : {e}")

    if message.channel.id == NOTIF_CHANNEL_ID:
        now = time.time()
        if now - last_notification_time >= notification_interval:
            try:
                await message.channel.send(f"<@&{NOTIF_ROLE_ID}>")
                last_notification_time = now
            except Exception as e:
                print(f"Erreur notification : {e}")

    await bot.process_commands(message)

@bot.command(name="vocs")
@commands.has_permissions(manage_guild=True)
async def vocs(ctx):
    category = ctx.guild.get_channel(VOCAL_CATEGORY_ID)
    if not category:
        await ctx.send("❌ Catégorie introuvable.")
        return

    vocaux = [c for c in category.voice_channels if c.id != CREATOR_BUTTON_CHANNEL]
    if not vocaux:
        await ctx.send("📭 Aucun salon vocal temporaire actif.")
        return

    await ctx.send(f"📋 Liste des vocaux dans **{category.name}** :")
    for vocal in vocaux:
        await ctx.send(f"🔊 **{vocal.name}** – `{len(vocal.members)} connecté(s)`")

# === Lancer le bot ===
load_dotenv()
TOKEN = os.getenv("TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Token introuvable.")
