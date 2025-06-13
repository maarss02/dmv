import os
import re
import time
import asyncio
import discord
from discord.ext import commands
from discord import ui, Interaction, ButtonStyle, TextStyle, PermissionOverwrite
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
ANNONCE_BUTTON_CHANNEL = 1344287289425268840
ANNONCE_PUBLIC_CHANNEL = 1344287287168729168
ROLE_FONDATEUR = 1344287286598307900
ROLE_MODO = 1344287286585458757

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
active_vocals = {}
notification_interval = 60 * 60
last_notification_time = 0
last_announcement_msg = None

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
                return await interaction.response.send_message("❌ Nombre de slots invalide (1-15).", ephemeral=True)
            if self.user_id in active_vocals:
                return await interaction.response.send_message("❌ Tu as déjà un salon actif.", ephemeral=True)

            guild = interaction.guild
            await guild.chunk()
            category = guild.get_channel(VOCAL_CATEGORY_ID)
            if not category:
                return await interaction.response.send_message("❌ Erreur : catégorie introuvable.", ephemeral=True)
            member = guild.get_member(self.user_id)
            if not member:
                return await interaction.response.send_message("❌ Impossible de retrouver ton profil.", ephemeral=True)
            role = guild.get_role(self.role_id)
            bot_music_role = guild.get_role(ROLE_BOT_MUSIC)
            if not role or not bot_music_role:
                return await interaction.response.send_message("❌ Erreur rôle introuvable.", ephemeral=True)

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
                f"✅ Salon vocal **{nom}** créé (limite {slots}, rôle <@&{role.id}>)", ephemeral=True
            )

            async def auto_delete():
                await asyncio.sleep(300)
                if len(vocal.members) == 0:
                    await vocal.delete()
                    if active_vocals.get(self.user_id) == vocal.id:
                        del active_vocals[self.user_id]
            asyncio.create_task(auto_delete())

        except Exception as e:
            await interaction.response.send_message(f"❌ Erreur : {e}", ephemeral=True)

class RoleChoiceView(ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        self.user_id = user_id

    @ui.button(label="👤 Membres", style=ButtonStyle.primary)
    async def membre_btn(self, interaction: Interaction, _):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("Ce menu ne t'est pas destiné.", ephemeral=True)
        await interaction.response.send_modal(VocalModal(ROLE_MEMBRES, self.user_id))

    @ui.button(label="🛡️ Scrims", style=ButtonStyle.success)
    async def scrims_btn(self, interaction: Interaction, _):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("Ce menu ne t'est pas destiné.", ephemeral=True)
        await interaction.response.send_modal(VocalModal(ROLE_SCRIMS, self.user_id))

class CreateVocalView(ui.View):
    @ui.button(label="🎧 Créer un vocal", style=ButtonStyle.success)
    async def create_btn(self, interaction: Interaction, _):
        await interaction.response.send_message(
            "Sélectionne le rôle autorisé à rejoindre ton salon :",
            view=RoleChoiceView(user_id=interaction.user.id),
            ephemeral=True
        )

# ... (le haut reste identique jusqu'à AnnonceModal)

class AnnonceModal(ui.Modal, title="Créer ou modifier une annonce"):
    mention = ui.Select(
        placeholder="Qui voulez-vous mentionner ?",
        options=[
            discord.SelectOption(label="@everyone", value="everyone"),
            discord.SelectOption(label="@Notif", value="notif"),
            discord.SelectOption(label="Aucune mention", value="none")
        ]
    )
    message = ui.TextInput(
        label="Contenu de l’annonce",
        style=TextStyle.paragraph,
        max_length=2000
    )

    def __init__(self, editing: bool = False):
        super().__init__(timeout=300)
        self.editing = editing
        self.add_item(self.mention)

    async def on_submit(self, interaction: Interaction):
        global last_announcement_msg
        try:
            mention_type = self.mention.values[0]
            mention_text = {
                "everyone": "@everyone",
                "notif": f"<@&{NOTIF_ROLE_ID}>",
                "none": ""
            }.get(mention_type, "")

            content = f"{mention_text}\n{self.message.value}".strip()
            channel = interaction.guild.get_channel(ANNONCE_PUBLIC_CHANNEL)

            if last_announcement_msg:
                await last_announcement_msg.delete()

            last_announcement_msg = await channel.send(content)
            await interaction.response.send_message(
                f"✅ Annonce {'modifiée' if self.editing else 'créée'} avec succès.",
                ephemeral=True
            )

        except Exception as e:
            await interaction.response.send_message(f"❌ Erreur : {e}", ephemeral=True)

class AnnonceButtons(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="📢 Créer une annonce", style=ButtonStyle.primary)
    async def create_annonce(self, interaction: Interaction, _):
        if not any(role.id in [ROLE_FONDATEUR, ROLE_MODO] for role in interaction.user.roles):
            return await interaction.response.send_message("Tu n'as pas la permission.", ephemeral=True)
        await interaction.response.send_modal(AnnonceModal(editing=False))

    @ui.button(label="✏️ Modifier l’annonce", style=ButtonStyle.secondary)
    async def edit_annonce(self, interaction: Interaction, _):
        if not any(role.id in [ROLE_FONDATEUR, ROLE_MODO] for role in interaction.user.roles):
            return await interaction.response.send_message("Tu n'as pas la permission.", ephemeral=True)
        await interaction.response.send_modal(AnnonceModal(editing=True))

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")
    try:
        # Bouton vocal
        channel = bot.get_channel(CREATOR_BUTTON_CHANNEL)
        async for msg in channel.history(limit=10):
            if msg.author == bot.user:
                await msg.delete()
        await channel.send("🎧 Clique ci-dessous pour créer ton salon vocal :", view=CreateVocalView())

        # Boutons d’annonce
        annonce_channel = bot.get_channel(ANNONCE_BUTTON_CHANNEL)
        async for msg in annonce_channel.history(limit=10):
            if msg.author == bot.user:
                await msg.delete()
        await annonce_channel.send("📣 Utilise les boutons ci-dessous pour gérer une annonce :", view=AnnonceButtons())

    except Exception as e:
        print(f"❌ Erreur dans on_ready : {e}")
