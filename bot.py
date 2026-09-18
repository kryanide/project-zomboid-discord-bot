import os
import discord
import asyncio
from rcon.source import Client
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

HOST = os.getenv("RCON_HOST", "127.0.0.1")
PORT = int(os.getenv("RCON_PORT", "27015"))
PASSWORD = os.getenv("RCON_PASSWORD")


class Bot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)


bot = Bot()


@bot.tree.command(description="Check the bot is alive")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("pong", ephemeral=True)

def checkPlayers():
    with Client(HOST, PORT, passwd=PASSWORD) as client:
        return client.run("players")

@bot.tree.command(description="See who is online, if anyone.")
async def players(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        result = await asyncio.to_thread(checkPlayers)
    except Exception as e:
        await interaction.followup.send(f"failed: {e}", ephemeral=True)
        return
    await interaction.followup.send(result, ephemeral=True)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


bot.run(TOKEN)