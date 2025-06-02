import discord
from discord import app_commands
import os
import random
import asyncio
from datetime import timedelta  # ✅ corrigé ici

# Remplace avec l'ID de ton serveur Discord
GUILD_ID = 123456789012345678  # ← mets ton vrai ID ici

intents = discord.Intents.default()
intents.members = True  # pour add_roles / timeout

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)

        # 🧼 Nettoyage des commandes globales (cache slash Discord)
        try:
            self.tree.clear_commands(guild=None)
            await self.tree.sync()
            print("🧹 Commandes globales vidées")
        except Exception as e:
            print(f"[Erreur purge globale] {e}")

        # ✅ Sync ciblée sur ton serveur
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print(f"✅ Slash command sync sur {GUILD_ID}")

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
            try:
                await user.timeout(discord.utils.utcnow() + timedelta(minutes=10))
                await interaction.followup.send(f"💥 {user.mention} a perdu ! Silence 10 minutes.")
            except Exception as e:
                await interaction.followup.send("❌ Impossible de mute. Vérifie les permissions.")
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
            try:
                await user.send("⏳ Ton rôle VIP a expiré.")
            except:
                pass

    except Exception as e:
        await interaction.followup.send("❌ Une erreur est survenue.")
        print(f"[Erreur roulette] {e}")

# 🔐 Token depuis Railway variable d'environnement
client.run(os.getenv("TOKEN"))

