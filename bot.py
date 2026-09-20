import os
import discord
import asyncio
import socket
import logging
import messages
import random
import json
from rcon.source import Client
from discord import app_commands
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ]
)
log = logging.getLogger("pzbot")

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_IDS = [int(g.strip()) for g in os.getenv("GUILD_IDS").split(",")]

HOST = os.getenv("RCON_HOST", "127.0.0.1")
PORT = int(os.getenv("RCON_PORT", "27015"))
PASSWORD = os.getenv("RCON_PASSWORD")
ADMIN = int(os.getenv("ADMIN_ROLE_ID"))

SETTINGS_FILE = "settings.json"

def load_settings():
    with open("settings.default.json") as f:
        data = json.load(f)
    try:
        with open("settings.json") as f:
            data.update(json.load(f))
    except FileNotFoundError:
        pass
    return data

def save_settings():
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

settings = load_settings()

class Bot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        for gid in GUILD_IDS:
            guild = discord.Object(id=gid)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)


def log_command(interaction, outcome="ok", level=logging.INFO):
    log.log(
        level,
        "/%s by %s (%s) - %s",
        interaction.command.name,
        interaction.user,
        interaction.user.id,
        outcome,
    )

def rcon_command(command):
    with Client(HOST, PORT, passwd=PASSWORD) as client:
        return client.run(command)

def is_ephemeral(interaction: discord.Interaction) -> bool:
    return settings["ephemeral"].get(interaction.command.name, True)

def get_message(key: str, fallback: str = "If you're reading this, kry's code is bad") -> str:
    value = messages.MESSAGES.get(key, fallback)
    return random.choice(value) if isinstance(value, list) else value

async def reply(interaction: discord.Interaction, key: str):
    await interaction.followup.send(get_message(key), ephemeral=is_ephemeral(interaction))

bot = Bot()

# ----------------------PING PONG TEST---------------------------------------

@bot.tree.command(description="Check the bot is alive")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("pong", ephemeral=is_ephemeral(interaction))
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ----------------------CHECK ONLINE PLAYERS---------------------------------
def check_players():
    with Client(HOST, PORT, passwd=PASSWORD) as client:
        return client.run("players")

@bot.tree.command(description="See who is online, if anyone.")
async def players(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=is_ephemeral(interaction))
    try:
        result = await asyncio.to_thread(check_players)
    except Exception as e:
        log_command(interaction, f"failed: {e}", logging.ERROR)
        await interaction.followup.send(f"failed: {e}")
        return
    await interaction.followup.send(result)
    log_command(interaction)
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ----------------------STATUS CHECK-----------------------------------------

def check_status(host=HOST, port=PORT):
    try:
        with socket.create_connection((host, port), settings["status_timeout_seconds"]):
            return "online"
    except OSError:
        return "offline"

@bot.tree.command(description="Is the server on?")
async def status(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=is_ephemeral(interaction))
    try:
        result = await asyncio.to_thread(check_status)
    except Exception as e:
        log_command(interaction, f"failed: {e}", logging.ERROR)
        await reply(interaction, "error.rcon_failed")
        return
    await reply(interaction, f"status.{result}")
    log_command(interaction)

# -------------------------------------------------------------------------
# -------------------------------------------------------------------------
# -------------------------SHUTDOWN-----------------------------------------


@bot.tree.command(description="Stop the server")
async def stop(interaction: discord.Interaction):
    STOP_DELAY = settings["stop_delay_seconds"]
    if not any(r.id == ADMIN for r in interaction.user.roles):
        log_command(interaction, "denied", logging.WARNING)
        await interaction.response.send_message(get_message("stop.denied"), ephemeral=True)
        return

    status = await asyncio.to_thread(check_status)
    
    log_command(interaction)
    await interaction.response.defer(ephemeral=is_ephemeral(interaction))
    if status == "offline":
        log_command(interaction, "already offline", logging.WARNING)
        await reply(interaction, "stop.already_offline")
        return

    try:
        await asyncio.to_thread(
            rcon_command,
            f'servermsg "{get_message("stop.server").format(STOP_DELAY)}"'
        )
        await reply(interaction, "stop.warning_sent")
    except Exception as e:
        log_command(interaction, f"warning failed: {e}", logging.ERROR)
        await reply(interaction, "error.rcon_failed")
        return

    await asyncio.sleep(STOP_DELAY)

    try:
        await reply(interaction, "stop.saving")
        await asyncio.to_thread(rcon_command, 'save')
        log_command(interaction, "saved")
    except Exception as e:
        log_command(interaction, f"save failed {e}", logging.ERROR)
        await reply(interaction, "stop.save_failed")
        return

    try:
        await reply(interaction, "stop.stopping")
        await asyncio.to_thread(rcon_command, 'quit')
    except Exception as e:
        log_command(interaction, f"Server shutdown. {e}", logging.INFO)

    await asyncio.sleep(settings["shutdown_check_delay_seconds"])

    final = await asyncio.to_thread(check_status)
    if final == "offline":
        await reply(interaction, "stop.stopped")
    else:
        await reply(interaction, "stop.still_up")

    

# -------------------------------------------------------------------------
# -------------------------------------------------------------------------


@bot.event
async def on_ready():
    log.info("Logged in as %s", bot.user)

if __name__ == "__main__":
    bot.run(TOKEN, log_handler=None)