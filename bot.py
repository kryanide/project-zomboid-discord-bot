import os
import discord
import asyncio
import socket
import logging
import messages
import random
import json
import subprocess
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

# Turns "123,456" into [123, 456]
# Removes any possible spaces. .strip is there as a safety measure but it's probably not needed
GUILD_IDS = [int(g.strip()) for g in os.getenv("GUILD_IDS").split(",")]

HOST = os.getenv("RCON_HOST", "127.0.0.1")
PORT = int(os.getenv("RCON_PORT", "27015"))
PASSWORD = os.getenv("RCON_PASSWORD")
ADMIN = int(os.getenv("ADMIN_ROLE_ID"))
BAT_FILE = os.getenv("SERVER_BAT")

SETTINGS_FILE = "settings.json"

# Load from settings.json, however settings.default.json loads first
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

    # Since commands start global, copy to the guild so the sync is instant
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

# helper function so I can have each individual command be private or public.
# Returns True by default in case I forgot to add the command to the json file.
def is_ephemeral(interaction: discord.Interaction) -> bool:
    return settings["ephemeral"].get(interaction.command.name, True)

# a helper function to get a message from [messages.py]
# if applicable, grabs a random message, if there's an issue returns the fallback
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

# Usage of defer here (and throughout the code) gives us a 15 minute window to send follow up messages
# Without it Discord drops the interaction within 3s
# The only command which doesn't need it is /ping (the command above)

@bot.tree.command(description="See who is online, if anyone.")
async def players(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=is_ephemeral(interaction))
    try:
        # Without to_thread the whole bot would freeze, which would invite problems like disconnects
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

# Catching OSError here covers both ConnectionRefusedError and TimeoutError
# On a closed port the connection timed out rather than refused
# (OSError is the parent of both)
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
# -------------------------SHUTDOWN----------------------------------------


@bot.tree.command(description="Stop the server")
async def stop(interaction: discord.Interaction):
    STOP_DELAY = settings["stop_delay_seconds"]
    if not any(r.id == ADMIN for r in interaction.user.roles):
        log_command(interaction, "denied", logging.WARNING)
        # I use send_message instead of reply() as the message is sent before defer(), which reply() relies on
        # This is the same in /start
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
        # Although this is technically an error, it's the intended outcome. quit kills the server,
        # which takes the RCON connection down with it, so this throws even when it works.
        # That's why it's logged as INFO rather than ERROR.
        log_command(interaction, f"Server shutdown. {e}", logging.INFO)

    await asyncio.sleep(settings["shutdown_check_delay_seconds"])

    # Since we can't tell success from failure above, we call check_status here to verify
    final = await asyncio.to_thread(check_status)
    if final == "offline":
        await reply(interaction, "stop.stopped")
    else:
        await reply(interaction, "stop.still_up")

    

# -------------------------------------------------------------------------
# -------------------------------------------------------------------------
# ----------------------STARTUP--------------------------------------------

@bot.tree.command(description="Start the server")
async def start(interaction: discord.Interaction):
    if not any(r.id == ADMIN for r in interaction.user.roles):
        log_command(interaction, "denied", logging.WARNING)
        await interaction.response.send_message(get_message("start.denied"), ephemeral=True)
        return

    status = await asyncio.to_thread(check_status)

    log_command(interaction)
    await interaction.response.defer(ephemeral=is_ephemeral(interaction))
    if status == "online":
        log_command(interaction, "already online", logging.WARNING)
        await reply(interaction, "start.already_online")
        return

    try:
        proc = subprocess.Popen(
            BAT_FILE,
            cwd=os.path.dirname(BAT_FILE),
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
    except Exception as e:
        log_command(interaction, f"startup failed: {e}", logging.ERROR)
        await reply(interaction, "start.failed")
        return

    await reply(interaction, "start.launching")

    max_attempts = settings["start_timeout_seconds"] // settings["start_poll_seconds"]
    poll_seconds = settings["start_poll_seconds"]

    for attempt in range(max_attempts):
        await asyncio.sleep(poll_seconds)

        if proc.poll() is not None:
            # poll() returns None while the process is running and an exit code once it's finished
            # An early exit means the launch died, which isn't good
            log_command(interaction, "startup failed", logging.ERROR)
            await reply(interaction, "start.failed")
            return
        
        if await asyncio.to_thread(check_status) == "online":
            log_command(interaction, "started")
            await reply(interaction, "start.online")
            return

        # Check every 12th poll, which is roughly every 84s
        # attempt > 0 stops it firing on the first pass, since 0 % 12 is also 0
        if attempt > 0 and attempt % 12 == 0:
            log_command(interaction, "still launching")
            await reply(interaction, "start.still_launching")

    log_command(interaction, "timeout")
    await reply(interaction, "start.timeout")






@bot.event
async def on_ready():
    log.info("Logged in as %s", bot.user)

if __name__ == "__main__":
    # log_handler=None because we use our own logging system
    bot.run(TOKEN, log_handler=None)