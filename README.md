# pz-discord-bot

A small Discord bot for controlling a self-hosted Project Zomboid dedicated server.
It starts and stops the server, reports whether it is up, and lists who is online.

Server control runs over RCON, and startup launches the server's batch file
directly, so the bot has to run on the same machine as the server.

## Commands

| Command | Description | Admin only |
| --- | --- | --- |
| `/ping` | Check the bot is alive | No |
| `/status` | Report whether the server is up | No |
| `/players` | List who is online | No |
| `/start` | Launch the server and report when it is live | Yes |
| `/stop` | Warn players, save, and shut the server down | Yes |

`/start` opens the server's batch file in a new console window, then polls
until the port answers or the timeout runs out. `/stop` sends an in-game
warning, waits, saves the world, then quits and verifies the server is down.

Admin commands check for the role ID set in `ADMIN_ROLE_ID`.

## Requirements

- Python 3.11+
- A Project Zomboid dedicated server on the same machine, with RCON enabled
  (`RCONPort` and `RCONPassword` in the server's `.ini`)
- A Discord application with a bot token

## Setup

1. Clone the repo and create a virtual environment:

   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and fill in every value:

   | Variable | Meaning |
   | --- | --- |
   | `DISCORD_TOKEN` | Bot token from the Discord developer portal |
   | `RCON_HOST` | Usually `127.0.0.1` |
   | `RCON_PORT` | RCON port from the server's `.ini` |
   | `RCON_PASSWORD` | RCON password from the server's `.ini` |
   | `GUILD_IDS` | Comma-separated Discord server IDs to register commands in |
   | `ADMIN_ROLE_ID` | Role ID allowed to run `/start` and `/stop` |
   | `SERVER_BAT` | Full path to the server's start batch file |

   `.env` is gitignored and never committed.

3. Run the bot:

   ```
   start_bot.bat
   ```

   Or directly: `.venv\Scripts\python.exe bot.py`

Commands are synced per guild on startup, so they appear immediately.

## Settings

`settings.default.json` is committed and holds the defaults. To change
anything, create a `settings.json` next to it with only the keys you want to
override; it loads second and wins. `settings.json` is gitignored, so local
tweaks stay local.

| Key | Default | Meaning |
| --- | --- | --- |
| `ephemeral` | all `true` | Per-command: `true` means only the caller sees the reply |
| `stop_delay_seconds` | 10 | Warning time before `/stop` saves and quits |
| `shutdown_check_delay_seconds` | 10 | Wait before verifying the server is down |
| `status_timeout_seconds` | 2 | Socket timeout for status checks |
| `start_timeout_seconds` | 600 | How long `/start` waits for the server |
| `start_poll_seconds` | 5 | Time between startup checks |

## Messages

All user-facing text lives in `messages.py`, keyed by name (`stop.saving`,
`start.timeout`). Where a key holds a list, one line is picked at random.
Editing that file changes the bot's voice without touching any logic.

## Logging

Logs go to the console and to `bot.log`, including who ran each command and
how it turned out. `bot.log` is gitignored.

## TODO

### Features

- [ ] Cogs, so commands can be hot-reloaded without restarting the bot
- [ ] Arguments for commands (e.g. `/stop` takes a custom shutdown timer)
- [ ] Live player count in the bot's status, visible on its profile
- [ ] Custom `/players` message instead of the raw RCON output
- [ ] `/restart`, so you don't have to run `/stop` and `/start` back to back
- [ ] A way to check whether any mods have updated
- [ ] Custom RCON command execution (admin only)
- [ ] A way to check the server console (e.g. the bot posts the console log as a .txt file)
- [ ] Custom acknowledgement message instead of Discord's "thinking..."
- [ ] Multi-step commands (`/stop`, `/start`) edit one message as they progress instead of posting several

### Housekeeping

- [ ] `/update`: pull the latest code from git and restart the bot
- [ ] Run the bot as a Windows service
- [ ] Per-guild admin roles
- [ ] Command to change settings from Discord
- [ ] Shared error handler for commands
- [ ] Log rotation for `bot.log`
- [ ] Cleanup: unused `save_settings`, `SETTINGS_FILE` not used in `load_settings`, `check_players` duplicating `rcon_command`
- [ ] Respond to the interaction before `check_status` in `/stop` and `/start`, so a slow status check can't hit Discord's 3-second limit
