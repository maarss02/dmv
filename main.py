import os
import re
import time
import asyncio
import discord
from discord.ext import commands, tasks
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
ANNONCE_BUTTON_CHANNEL = 1344287289215287325
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

# ============ VOCAL SYSTEM ============

class VocalModal(ui.Modal, title="Créer un salon vocal"):
    nom = ui.TextInput(label="Nom du salon", placeholder="ex: Chill Zone", max_length=32)
    slots = ui.TextInput(label="Nombre de personnes (1-15)", placeholder="ex: 5", max_length=2)

    def __init__(self, role_id: int, user_id: int):
        super().__init__(timeout=300)
        self.role_id = role_id
        self.user_id = user_id

    async def on_submit(self, interaction: Interaction):
        try:
            nom = f"˒﹚) {self.nom.value}"
            slots = int(self.slots.value)

            if not 1 <= slots <= 15:
                return await interaction.response.send_message("❌ Nombre de slots invalide (1-15).", ephemeral=True)
            if self.user_id in active_vocals:
                return await interaction.response.send_message("❌ Tu as déjà un salon actif.", ephemeral=True)

            guild = interaction.guild
            await guild.chunk()
            category = guild.get_channel(VOCAL_CATEGORY_ID)

            role = guild.get_role(self.role_id)
            bot_music_role = guild.get_role(ROLE_BOT_MUSIC)

            overwrites = {
                guild.default_role: PermissionOverwrite(connect=False),
                role: PermissionOverwrite(
                    view_channel=True, connect=True, speak=True, stream=True,
                    use_voice_activation=True, use_soundboard=True, use_external_sounds=True
                ),
                bot_music_role: PermissionOverwrite(view_channel=True, connect=True),
                guild.me: PermissionOverwrite(view_channel=True, connect=True, manage_channels=True)
            }

            vocal = await guild.create_voice_channel(
                name=nom, user_limit=slots,
                overwrites=overwrites, category=category
            )
            active_vocals[self.user_id] = vocal.id

            await interaction.response.send_message(
                f"✅ Salon vocal **{nom}** créé avec succès (limite {slots}, rôle <@&{role.id}>)",
                ephemeral=True
            )

            await refresh_vocal_button_once()

            async def auto_delete():
                await asyncio.sleep(300)
                if len(vocal.members) == 0:
                    try:
                        await vocal.delete()
                    except discord.NotFound:
                        pass
                    if active_vocals.get(self.user_id) == vocal.id:
                        del active_vocals[self.user_id]

            asyncio.create_task(auto_delete())

        except Exception as e:
            await interaction.response.send_message(f"❌ Erreur : {e}", ephemeral=True)

class RoleChoiceView(ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        self.user_id = user_id

    @ui.button(label="👤 Membres", style=ButtonStyle.primary, custom_id="vocal_membres")
    async def membre_btn(self, interaction: Interaction, _):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("Ce menu ne t'est pas destiné.", ephemeral=True)
        await interaction.response.send_modal(VocalModal(ROLE_MEMBRES, self.user_id))

    @ui.button(label="🛡️ Scrims", style=ButtonStyle.success, custom_id="vocal_scrims")
    async def scrims_btn(self, interaction: Interaction, _):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("Ce menu ne t'est pas destiné.", ephemeral=True)
        await interaction.response.send_modal(VocalModal(ROLE_SCRIMS, self.user_id))

class CreateVocalView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="🎧 Créer un vocal", style=ButtonStyle.success, custom_id="creer_vocal")
    async def create_btn(self, interaction: Interaction, _):
        await interaction.response.send_message(
            "Sélectionne le rôle autorisé à rejoindre ton salon :",
            view=RoleChoiceView(user_id=interaction.user.id),
            ephemeral=True
        )

# ============ REFRESH ============

@tasks.loop(minutes=60)
async def refresh_vocal_button():
    await refresh_vocal_button_once()

async def refresh_vocal_button_once():
    try:
        ch = bot.get_channel(CREATOR_BUTTON_CHANNEL)
        if not ch:
            print("❌ Salon de création vocal introuvable.")
            return
        async for msg in ch.history(limit=10):
            if msg.author == bot.user:
                try:
                    await msg.delete()
                except:
                    pass
        await ch.send("🎧 Clique ci-dessous pour créer ton salon vocal :", view=CreateVocalView())
    except Exception as e:
        print(f"❌ Erreur dans refresh_vocal_button : {e}")

# ============ EVENTS ============

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")
    try:
        bot.add_view(CreateVocalView())  # Pour que les boutons persistent
        await refresh_vocal_button_once()
        refresh_vocal_button.start()
    except Exception as e:
        print(f"❌ Erreur dans on_ready : {e}")

@bot.event
async def on_message(message):
    global last_notification_time
    if message.author.bot:
        return

    if message.channel.id in MEDIA_CHANNEL_IDS:
        if not (re.search(r'https?://', message.content) or message.attachments or message.embeds):
            try:
                await message.delete()
                await message.author.send(
                    "👋 Ton message a été supprimé car ce salon est réservé aux BOT.\n\n"
                    "💬 Salon discussion : <#1378524605165207562>\n"
                    "🔎 Recherches : <#1378397438204968981>\n"
                    "👉 Tape `/forcestart` si besoin."
                )
            except:
                pass

    if message.channel.id == NOTIF_CHANNEL_ID:
        now = time.time()
        if now - last_notification_time >= notification_interval:
            await message.channel.send(f"<@&{NOTIF_ROLE_ID}>")
            last_notification_time = now

    await bot.process_commands(message)

# ============ COMMANDE DEBUG ============

@bot.command()
@commands.has_permissions(administrator=True)
async def vocs(ctx):
    category = ctx.guild.get_channel(VOCAL_CATEGORY_ID)
    vocaux = [c for c in category.voice_channels if c.id != CREATOR_BUTTON_CHANNEL]
    if not vocaux:
        return await ctx.send("📭 Aucun salon vocal temporaire actif.")
    for v in vocaux:
        await ctx.send(f"🔊 **{v.name}** – `{len(v.members)} connecté(s)`")

# ============ START BOT ============

load_dotenv()
TOKEN = os.getenv("TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Token introuvable.")
