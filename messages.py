# This file is exclusively for the messages
#
# One flat dict, keys namespaced with a prefix:
#   status.*  - the /status command
#   stop.*    - the /stop command
#   error.*   - things that ideally never get seen
#
# A value can be a single string or a list of variants.
# get_message() in bot.py picks one at random when it's a list.

MESSAGES = {

    # ----- status -------------------------------------------------------
    "status.online": [
        ":green_circle: - All green on our end. Server looks active.",
        ":green_circle: - Got eyes on it, server's up and running. Over.",
        ":green_circle: - Reading you five by five. Server's live.",
        ":green_circle: - Circling now, looks like everyone's still breathing down there.",
    ],
    "status.offline": [
        (
            ":red_circle: - negative, no joy on that frequency "
            "looks like the server is down, over."
        ),
        ":red_circle: - I've been calling for ten minutes. Nobody's home. Server's offline.",
        ":red_circle: - No signal, no lights, nothing. She's dark.",
    ],

    # ----- stop ---------------------------------------------------------
    # Templates - "server" goes in-game via servermsg, "discord" goes to chat
    "stop.server": "SERVER SHUTDOWN IN {} SECONDS. Find somewhere safe.",
    "stop.discord": "Closing the connection!",

    # Responses
    "stop.denied": "Looks like you don't have the permissions for that boss!",
    "stop.already_offline": "She's already dark, boss. Nothing to shut down.",
    "stop.warning_sent": "Word's out. Counting down.",
    "stop.saving": "Saving now, hold your position...",
    "stop.stopping": "Cutting the engines. Stand by.",
    "stop.stopped": "Confirmed. Server's down, everybody's out. Good work.",
    "stop.still_up": (
        "Sent the shutdown but she's still showing signs of life. "
        "Might need eyes on it directly."
    ),
    "stop.save_failed": (
        "Save didn't take, so I'm aborting. "
        "Server's still up - nobody's losing progress over this."
    ),

    # ----- start  -------------------------------------------------------
    "start.denied": "Looks like you don't have the permissions for that boss!",
    "start.already_online": "She's already live, boss. Nothing to start.",
    "start.launching": "Initiating startup sequence... This may take a while.",
    "start.still_launching": "Startup sequence is still running. Stand by.",
    "start.online": "Startup complete. Server's live and running.",
    "start.failed": "Startup failed. Don't know what went wrong. Maybe the logs say what went wrong.",
    "start.timeout": "Startup timed out. Server didn't come online in time.",

    # ----- errors -------------------------------------------------------
    "error.rcon_failed": "Lost the radio halfway through. Couldn't reach the server.",
    "error.no_response": "Sent it. Heard nothing back. Say again?",
    "error.timeout": "Been holding this channel a while now. Nothing's coming through.",
    "error.unknown": "Something came back garbled. Say again?",
    "error.bad_command": "That's not a call sign I recognize, over.",
}
