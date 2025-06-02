import discord
from discord import app_commands
from discord.ext import tasks
import asyncio
import random
import os

intents = discord.Intents.default()
intents.message_content = False  # pas besoin pour slash
intents.members = True  # obligatoire pour add_roles / timeout

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        print("✅ Slash commands synchronisées.")

client = MyClient()

@client.event
async def on_ready():
    print(f"🤖 Connecté en tant que {client.user}")

@client.tree.command(name="roulette", description="Joue à la roulette russe : mute ou VIP ?")
async def roulette(interaction: discord.Interaction):
    user = interaction.user
    guild = interaction.guild

    await interaction.response.defer()  # pour éviter le timeout (pensée aux bots Railway)

    if random.randint(1, 6) == 1:
        try:
            await user.timeout(discord.utils.utcnow() + discord.timedelta(minutes=10))
            await interaction.followup.send(f"💥 {user.mention} a perdu ! Silence pendant 10 minutes.")
        except Exception as e:
            await interaction.followup.send("⚠️ Je ne peux pas mute ce membre. Permissions manquantes.")
            print(f"[Erreur timeout] {e}")
    else:
        role = discord.utils.get(guild.roles, name="VIP")
        if not role:
            await interaction.followup.send("⚠️ Le rôle `VIP` n'existe pas dans ce serveur.")
            return

        await user.add_roles(role)
        await interaction.followup.send(f"😎 {user.mention} a survécu ! VIP pendant 10 minutes 👑")

        await asyncio.sleep(600)
        await user.remove_roles(role)
        try:
            await user.send("⏳ Ton rôle VIP a expiré.")
        except:
            pass

client.run(os.getenv("DISCORD_TOKEN"))
