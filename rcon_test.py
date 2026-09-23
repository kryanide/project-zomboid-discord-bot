# If the bot is having some trouble with RCON run `python rcon_test.py` to see if it's an issue with
# RCON itself

import os
from dotenv import load_dotenv
from rcon.source import Client

load_dotenv()

HOST = os.getenv("RCON_HOST", "127.0.0.1")
PORT = int(os.getenv("RCON_PORT", "27015"))
PASSWORD = os.getenv("RCON_PASSWORD")

with Client(HOST, PORT, passwd=PASSWORD) as client:
    print(client.run("players"))