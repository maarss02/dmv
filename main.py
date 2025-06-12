import os
import re
import time
import asyncio
import discord
from discord.ext import commands
from discord import ui, Interaction, PermissionOverwrite, ButtonStyle
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
NOTIF_CHANNEL_ID = 137888888888888888  # à remplacer
NOTIF_ROLE_ID = 137899999999999999     # à remplacer
CREATOR_VOCAL_ID = 1382766373825937429
VOCAL_CATEGORY_ID = 1382767784064323755
ROLE_MEMBRES = 1344287286585458749
ROLE_SCRIMS = 1378428377412931644
ROLE_NSFW = 1344287286527004772

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

@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel and after.channel.id == CREATOR_VOCAL_ID:
        try:
            await member.move_to(None)
            await member.send("📝 Tu vas recevoir un formulaire ici pour créer ton salon vocal.")
            modal = VocalModal(author_roles=member.roles)
            # On utilise une interaction factice via DM pour simuler le modal
            # ATTENTION : les modals ne fonctionnent que via interactions boutons/slash — ici on doit revoir logique
        except Exception as e:
            print(f"❌ Erreur d'affichage du formulaire : {e}")

class VocalModal(ui.Modal, title="🎧 Créer votre salon vocal"):
    def __init__(self, author_roles):
        super().__init__()
        self.author_roles = author_roles
        self.nom = ui.TextInput(label="Nom du vocal", placeholder="Ex: Chill, Team X", max_length=32)
        self.slots = ui.TextInput(label="Nombre de personnes (1-15)", placeholder="Ex: 5", default="5")
        self.add_item(self.nom)
        self.add_item(self.slots)

    async def on_submit(self, interaction: Interaction):
        try:
            name = str(self.nom.value)
            limit = int(self.slots.value)
            if not 1 <= limit <= 15:
                await interaction.response.send_message("❌ Le nombre doit être entre 1 et 15.", ephemeral=True)
                return

            options = [ROLE_MEMBRES]
            if any(r.id == ROLE_SCRIMS for r in self.author_roles):
                options.append(ROLE_SCRIMS)
            if any(r.id == ROLE_NSFW for r in self.author_roles):
                options.append(ROLE_NSFW)

            role_id = options[0]
            guild = interaction.guild
            category = guild.get_channel(VOCAL_CATEGORY_ID)
            everyone = guild.default_role
            role = guild.get_role(role_id)

            overwrites = {
                everyone: PermissionOverwrite(connect=False),
                role: PermissionOverwrite(connect=True),
                guild.me: PermissionOverwrite(connect=True, manage_channels=True)
            }

            vocal = await guild.create_voice_channel(name=name, user_limit=limit, overwrites=overwrites, category=category)
            await interaction.response.send_message(f"✅ Salon vocal créé : **{vocal.name}** *(limite {limit}, rôle : <@&{role_id}>)*", ephemeral=True)

            async def auto_delete_if_empty():
                await asyncio.sleep(180)
                if len(vocal.members) == 0:
                    await vocal.delete()
                    print(f"🗑️ Salon vocal supprimé (inactif) : {vocal.name}")

            asyncio.create_task(auto_delete_if_empty())

        except Exception as e:
            await interaction.response.send_message(f"❌ Erreur : {e}", ephemeral=True)

class SupprimerVocalView(ui.View):
    def __init__(self, channel):
        super().__init__(timeout=180)
        self.channel = channel

    @ui.button(label="Supprimer", style=ButtonStyle.danger)
    async def supprimer(self, interaction: Interaction, button: ui.Button):
        try:
            await self.channel.delete()
            await interaction.response.send_message(f"🗑️ Salon vocal **{self.channel.name}** supprimé.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erreur : {e}", ephemeral=True)

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
        view = SupprimerVocalView(vocal)
        await ctx.send(f"🔊 **{vocal.name}** – `{len(vocal.members)} connecté(s)`", view=view)

TOKEN = os.getenv("TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Token introuvable. Assure-toi qu'il est bien configuré.")
