import discord
from discord import app_commands
import os
import random
import asyncio
from datetime import timedelta

intents = discord.Intents.default()
intents.members = True

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    GUILD_ID = 1370086363034161162  # Remplace avec ton vrai ID de serveur

async def setup_hook(self):
    print("🔧 Sync locale forcée")
    guild = discord.Object(id=GUILD_ID)

    self.tree.clear_commands(guild=guild)
    await self.tree.sync(guild=guild)
    print(f"✅ Slash sync locale sur {GUILD_ID}")


client = MyClient()

@client.event
async def on_ready():
    print(f"🤖 Connecté en tant que {client.user}")

@client.tree.command(name="ping", description="Test si le bot répond bien")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong !")

@client.tree.command(name="roulette", description="Joue à la roulette russe : mute ou VIP ?")
async def roulette(interaction: discord.Interaction):
    await interaction.response.defer()
    user = interaction.user
    guild = interaction.guild

    try:
        if random.randint(1, 6) == 1:
            try:
                await user.timeout(discord.utils.utcnow() + timedelta(minutes=10))
                await interaction.followup.send(f"💥 {user.mention} a perdu ! Silence 10 minutes.")
            except Exception as e:
                await interaction.followup.send("❌ Je ne peux pas mute ce membre.")
                print(f"[Erreur timeout] {e}")
        else:
            role = discord.utils.get(guild.roles, name="VIP")
            if not role:
                role = await guild.create_role(name="VIP")
                print("🔧 Rôle VIP créé.")

            await user.add_roles(role)
            await interaction.followup.send(f"😎 {user.mention} a survécu ! VIP 10 minutes 👑")
            await asyncio.sleep(600)
            await user.remove_roles(role)

    except Exception as e:
        await interaction.followup.send("❌ Une erreur est survenue.")
        print(f"[Erreur roulette] {e}")

client.run(os.getenv("TOKEN"))



