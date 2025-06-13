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
ANNOUNCE_BUTTON_CHANNEL = 1344287289425268840
ANNOUNCE_POST_CHANNEL = 1344287287168729168
ROLE_MEMBRES = 1344287286585458749
ROLE_SCRIMS = 1378428377412931644
ROLE_BOT_MUSIC = 1345877829811699755
ROLE_MODO = 1344287286585458757
ROLE_FONDATEUR = 1344287286598307900

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

# === MODAL POUR LES VOCAUX ===
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
            await guild.chunk()
            category = guild.get_channel(VOCAL_CATEGORY_ID)
            if not category:
                return await interaction.response.send_message("❌ Catégorie introuvable.", ephemeral=True)

            role = guild.get_role(self.role_id)
            bot_music_role = guild.get_role(ROLE_BOT_MUSIC)
            if not role or not bot_music_role:
                return await interaction.response.send_message("❌ Rôle introuvable.", ephemeral=True)

            overwrites = {
                guild.default_role: PermissionOverwrite(connect=False),
                role: PermissionOverwrite(connect=True),
                bot_music_role: PermissionOverwrite(connect=True),
                guild.me: PermissionOverwrite(connect=True, manage_channels=True)
            }

            vocal = await guild.create_voice_channel(
                name=nom, user_limit=slots, overwrites=overwrites, category=category
            )

            active_vocals[self.user_id] = vocal.id
            await interaction.response.send_message(
                f"✅ Salon **{nom}** créé (limite {slots}, rôle : <@&{role.id}>)", ephemeral=True
            )

            async def auto_delete():
                await asyncio.sleep(300)
                if len(vocal.members) == 0:
                    await vocal.delete()
                    if self.user_id in active_vocals and active_vocals[self.user_id] == vocal.id:
                        del active_vocals[self.user_id]

            asyncio.create_task(auto_delete())

        except Exception as e:
            await interaction.response.send_message(f"❌ Erreur : {e}", ephemeral=True)

# === BOUTONS POUR VOCAUX ===
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

# === ANNONCE ===
class AnnouncementModal(ui.Modal, title="Créer une annonce"):
    contenu = ui.TextInput(label="Contenu de l’annonce", placeholder="Votre message ici...", style=TextStyle.paragraph)

    async def on_submit(self, interaction: Interaction):
        try:
            channel = interaction.guild.get_channel(ANNOUNCE_POST_CHANNEL)
            if not channel:
                return await interaction.response.send_message("❌ Salon d’annonce introuvable.", ephemeral=True)

            async for msg in channel.history(limit=10):
                if msg.author == bot.user:
                    await msg.delete()

            await channel.send(self.contenu.value)
            await interaction.response.send_message("✅ Annonce publiée avec succès.", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"❌ Erreur annonce : {e}", ephemeral=True)

class CreateAnnouncementView(ui.View):
    @ui.button(label="📢 Créer une annonce", style=ButtonStyle.primary)
    async def announce_button(self, interaction: Interaction, button: ui.Button):
        roles = [r.id for r in interaction.user.roles]
        if ROLE_FONDATEUR not in roles and ROLE_MODO not in roles:
            return await interaction.response.send_message("❌ Tu n’as pas la permission.", ephemeral=True)
        await interaction.response.send_modal(AnnouncementModal())

# === EVENTS ===
@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")
    try:
        # Bouton création vocal
        vocal_channel = bot.get_channel(CREATOR_BUTTON_CHANNEL)
        async for msg in vocal_channel.history(limit=10):
            if msg.author == bot.user:
                await msg.delete()
        await vocal_channel.send("🎧 Clique ci-dessous pour créer ton salon vocal :", view=CreateVocalView())

        # Bouton création annonce
        announce_button_channel = bot.get_channel(ANNOUNCE_BUTTON_CHANNEL)
        async for msg in announce_button_channel.history(limit=10):
            if msg.author == bot.user:
                await msg.delete()
        await announce_button_channel.send("📢 Clique ici pour créer une annonce :", view=CreateAnnouncementView())

    except Exception as e:
        print(f"❌ Erreur au démarrage : {e}")

@bot.event
async def on_message(message):
    global last_notification_time

    if message.author.bot:
        return

    if message.channel.id in MEDIA_CHANNEL_IDS:
        has_link = re.search(r'https?://', message.content)
        has_attachment = message.attachments
        has_embed = message.embeds
        if not (has_link or has_attachment or has_embed):
            try:
                await message.delete()
                await message.author.send("❌ Ton message a été supprimé car ce salon est réservé aux bots.")
            except:
                pass

    if message.channel.id == NOTIF_CHANNEL_ID:
        now = time.time()
        if now - last_notification_time >= notification_interval:
            try:
                await message.channel.send(f"<@&{NOTIF_ROLE_ID}>")
                last_notification_time = now
            except:
                pass

    await bot.process_commands(message)

@bot.command(name="vocs")
@commands.has_permissions(manage_guild=True)
async def vocs(ctx):
    category = ctx.guild.get_channel(VOCAL_CATEGORY_ID)
    vocaux = [c for c in category.voice_channels if c.id != CREATOR_BUTTON_CHANNEL]
    if not vocaux:
        return await ctx.send("📭 Aucun salon vocal actif.")
    for v in vocaux:
        await ctx.send(f"🔊 **{v.name}** – `{len(v.members)} connecté(s)`")

# === LANCEMENT ===
load_dotenv()
TOKEN = os.getenv("TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Token introuvable.")
