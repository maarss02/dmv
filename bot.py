import discord
from discord import app_commands
import os
import random
import asyncio

# Remplace par l'ID de ton serveur (clic droit sur le nom du serveur > Copier l'identifiant)
GUILD_ID = 1370086363034161162

intents = discord.Intents.default()
intents.members = True

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print(f"✅ Slash commands synchronisées avec le serveur {GUILD_ID}")

client = MyClient()

@client.event
async def on_ready():
    print(f"🤖 Connecté en tant que {client.user}")

@client.tree.command(name="roulette", description="Joue à la roulette russe : mute ou VIP ?")
async def roulette(interaction: discord.Interaction):
    await interaction.response.defer()

    user = interaction.user
    guild = interaction.guild

    try:
        if random.randint(1, 6) == 1:
            # Mute 10 minutes
            await user.timeout(discord.utils.utcnow() + discord.timedelta(minutes=10))
            await interaction.followup.send(f"💥 {user.mention} a perdu ! Silence pendant 10 minutes.")
        else:
            # Rôle VIP
            role = discord.utils.get(guild.roles, name="VIP")
            if not role:
                # Créer le rôle automatiquement s'il n'existe pas
                role = await guild.create_role(name="VIP")
                print("🔧 Rôle VIP créé automatiquement.")

            await user.add_roles(role)
            await interaction.followup.send(f"😎 {user.mention} a survécu ! VIP pendant 10 minutes 👑")

            await asyncio.sleep(600)
            await user.remove_roles(role)
            try:
                await user.send("⏳ Ton rôle VIP a expiré.")
            except:
                pass

    except Exception as e:
        await interaction.followup.send("❌ Une erreur est survenue.")
        print(f"[Erreur roulette] {e}")

# Token depuis Railway
client.run(os.getenv("TOKEN"))

