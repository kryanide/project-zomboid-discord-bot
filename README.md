# pz-discord-bot

![maintenance](https://img.shields.io/badge/maintenance-actively%20developed-brightgreen)

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

- Windows (the bot launches the server's batch file in a new console window)
- Python 3.11+
- A Project Zomboid dedicated server on the same machine, with RCON enabled
  (`RCONPort` and `RCONPassword` in the server's `.ini`)
- A Discord application with a bot token

## Setup

1. Clone the repo and create a virtual environment:

   ```
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Create a bot in the [Discord developer portal](https://discord.com/developers/applications)
   and invite it to your server with the `bot` and `applications.commands`
   scopes. No privileged intents are needed.

3. Copy `.env.example` to `.env` and fill in every value:

   | Variable | Meaning |
   | --- | --- |
   | `DISCORD_TOKEN` | Bot token from the Discord developer portal |
   | `RCON_HOST` | Usually `127.0.0.1` |
   | `RCON_PORT` | RCON port from the server's `.ini` |
   | `RCON_PASSWORD` | RCON password from the server's `.ini` |
   | `GUILD_IDS` | Comma-separated Discord server IDs to register commands in |
   | `ADMIN_ROLE_ID` | Role ID allowed to run `/start` and `/stop` |
   | `SERVER_BAT` | Full path to the server's start batch file |

   To get server and role IDs, turn on Developer Mode in Discord
   (Settings → Advanced), then right-click the server or role and choose
   **Copy ID**.

   `.env` is gitignored and never committed.

4. Run the bot:

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

## Troubleshooting

If a command fails with an RCON error, run `python rcon_test.py`. It connects
to the server using the values in `.env` and lists online players, with Discord
out of the picture. If it fails too, the problem is RCON itself (wrong port or
password, or the server isn't running), not the bot.

## Planned

- Cogs, so commands can be hot-reloaded
- `/restart`
- Optional arguments, like a custom `/stop` countdown
- Live player count in the bot's status
- Nicer `/players` output
- Mod update checks
- Server console access for admins

## License

MIT, see [LICENSE](LICENSE).
