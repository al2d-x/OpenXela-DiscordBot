import os
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()  # loads .env into environment variables

app = FastAPI()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")


@app.get("/health")
def health():
    return {
        "ok": True,
        "token_loaded": bool(DISCORD_TOKEN),
        "client_id": DISCORD_CLIENT_ID
    }
