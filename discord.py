import discord
from discord.ext import commands
import random
import asyncio
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # important pour gérer rôles et timeouts

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"🤖 Connecté en tant que {bot.user}")

@bot.command()
async def roulette(ctx):
    author = ctx.author
    guild = ctx.guild

    if random.randint(1, 6) == 1:
        try:
            await author.timeout(discord.utils.utcnow() + discord.timedelta(minutes=10))
            await ctx.send(f"💥 {author.mention} a perdu... muet 10 minutes.")
        except Exception as e:
            await ctx.send("⚠️ Impossible de mute. Vérifie les permissions.")
            print(f"Erreur mute : {e}")
    else:
        role = discord.utils.get(guild.roles, name="VIP")
        if not role:
            await ctx.send("⚠️ Le rôle `VIP` n'existe pas.")
            return

        await author.add_roles(role)
        await ctx.send(f"😎 {author.mention} a survécu ! VIP pendant 10 minutes 👑")

        await asyncio.sleep(600)
        await author.remove_roles(role)
        try:
            await author.send("⏳ Ton rôle VIP a expiré.")
        except:
            pass

# Démarre le bot avec le token depuis les variables Railway
bot.run(os.getenv("TOKEN"))
