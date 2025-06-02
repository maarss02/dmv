import discord
from discord import app_commands
import os
import random
import asyncio

# Remplace ici par ton vrai ID de serveur
GUILD_ID = 1370086363034161162  # ← À mettre à jour

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
    user = interaction.user
    guild = interaction.guild

    await interaction.response.defer()

    if random.randint(1, 6) == 1:
        try:
            await user.timeout(discord.utils.utcnow() + discord.timedelta(minutes=10))
            await interaction.followup.send(f"💥 {user.mention} a perdu ! Mute 10 minutes.")
        except:
            await interaction.followup.send("❌ Je n'ai pas pu mute ce membre.")
    else:
        role = discord.utils.get(guild.roles, name="VIP")
        if role:
            await user.add_roles(role)
            await interaction.followup.send(f"😎 {user.mention} a survécu ! VIP 10 minutes 👑")
            await asyncio.sleep(600)
            await user.remove_roles(role)
        else:
            await interaction.followup.send("⚠️ Le rôle `VIP` n'existe pas.")

client.run(os.getenv("TOKEN"))

