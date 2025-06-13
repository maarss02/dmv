import os
import re
import time
import asyncio
import discord
from discord.ext import commands
from discord import ui, Interaction, PermissionOverwrite
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# === CONFIGURATION ===
MEDIA_CHANNEL_IDS = [1371204189908369550, 1370165104943042671]
NOTIF_CHANNEL_ID = 1344287288946982936
NOTIF_ROLE_ID = 1344287286527004770
CREATOR_VOCAL_ID = 1382766373825937429
VOCAL_CATEGORY_ID = 1382767784064323755
VOCAL_COMMAND_CHANNEL_ID = 1382771825775476746

ROLE_MEMBRES = 1344287286585458749
ROLE_SCRIMS = 1378428377412931644

notification_interval = 60 * 60  # 1h
last_notification_time = 0

# === MODAL DE CRÉATION ===
class VocalModal(ui.Modal, title="Créer ton salon vocal"):
    nom = ui.TextInput(label="Nom du salon", placeholder="ex: Chill Zone", max_length=32)
    slots = ui.TextInput(label="Nombre de personnes (1-15)", placeholder="ex: 5", max_length=2)

    def __init__(self, role_id):
        super().__init__(timeout=300)
        self.role_id = role_id

    async def on_submit(self, interaction: Interaction):
        try:
            nom = self.nom.value
            slots = int(self.slots.value)

            if not 1 <= slots <= 15:
                await interaction.response.send_message("❌ Nombre de slots invalide (1-15).", ephemeral=True)
                return

            role = interaction.guild.get_role(self.role_id)
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

            await interaction.response.send_message(
                f"✅ Salon vocal créé : **{vocal.name}** *(limite {slots}, rôle : <@&{role.id}>)*",
                ephemeral=True
            )

            async def auto_delete_if_empty():
                await asyncio.sleep(180)
                if len(vocal.members) == 0:
                    await vocal.delete()
                    print(f"🗑️ Salon vocal supprimé (inactif) : {vocal.name}")

            asyncio.create_task(auto_delete_if_empty())

        except Exception as e:
            await interaction.response.send_message(f"❌ Erreur : {e}", ephemeral=True)

# === SOUS-BOUTONS POUR RÔLE ===
class SelectRoleView(ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @ui.button(label="👤 Membres", style=discord.ButtonStyle.primary)
    async def membres(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_modal(VocalModal(ROLE_MEMBRES))

    @ui.button(label="🛡️ Scrims", style=discord.ButtonStyle.success)
    async def scrims(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_modal(VocalModal(ROLE_SCRIMS))

# === BOUTON PRINCIPAL "Créer un vocal" ===
class CreateVocalEntryView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="🎧 Créer un vocal", style=discord.ButtonStyle.green, custom_id="create_vocal_start")
    async def start(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_message(
            "🛠️ Choisis un rôle autorisé à rejoindre ton salon vocal :",
            view=SelectRoleView(),
            ephemeral=True
        )

# === AU LANCEMENT ===
@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")
    bot.add_view(CreateVocalEntryView())  # Pour persistance du bouton

    try:
        channel = bot.get_channel(VOCAL_COMMAND_CHANNEL_ID)
        if channel:
            async for msg in channel.history(limit=10):
                if msg.author == bot.user and any(comp.custom_id == "create_vocal_start" for row in msg.components for comp in row.children):
                    print("✅ Bouton principal déjà présent.")
                    break
            else:
                await channel.send("**🎤 Crée ton salon vocal avec accès privé :**", view=CreateVocalEntryView())
                print("✅ Bouton principal envoyé.")
    except Exception as e:
        print(f"❌ Erreur bouton vocal : {e}")

# === GESTION MESSAGES SUPPRIMÉS OU NOTIF ===
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
                print(f"❌ Message supprimé : {message.content}")
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
                print(f"Erreur suppression message : {e}")

    if message.channel.id == NOTIF_CHANNEL_ID:
        now = time.time()
        if now - last_notification_time >= notification_interval:
            try:
                await message.channel.send(f"<@&{NOTIF_ROLE_ID}>")
                last_notification_time = now
                print("🔔 Notification envoyée.")
            except Exception as notif_error:
                print(f"❌ Erreur notification : {notif_error}")
        else:
            print("⏱️ Notification ignorée (moins d'1h)")

    await bot.process_commands(message)

# === LANCEMENT BOT ===
TOKEN = os.getenv("TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Token manquant. Configure le via Railway ou un .env local.")
