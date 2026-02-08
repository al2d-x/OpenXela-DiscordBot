# OpenXela Discord Bot

Basic administrative tasks bot for Discord.

## Features

| Feature | Command(s) | What it does |
| --- | --- | --- |
| Temp Voice Hubs | `!sethub`, `!unsethub`, `!listhubs` | Mark voice channels as hubs so joining them creates a temporary room and moves the user into it. |
| Temp Voice Category | `!settempcategory`, `!cleartempcategory` | Choose which category new temp voice rooms are created under (falls back to the hub's category if unset). |
| Command Channel Restriction | `!setcommandchannel`, `!clearcommandchannel`, `!commandchannel` | Restrict non-admin prefix commands to one text channel; admins and guild owner can run commands anywhere. |
| Room Management | `/room name`, `/room limit`, `/room lock`, `/room unlock`, `/room transfer` | Rename, set user limit, lock/unlock, and transfer ownership of a managed temp room. Ownership auto-transfers to the oldest member when the owner leaves. |
| Help | `!help` | Shows the bot repo and quick usage hints. |

## Setup

1. Create `.env` from `.env.example`.
2. Install dependencies:

   pip install -r requirements.txt

## Run

- Bot: `python run_bot.py`
- API: `python run_api.py`

## Discord Portal Intents

Enable these for your bot in Discord Developer Portal -> Bot -> Privileged Gateway Intents:

- `SERVER MEMBERS INTENT`
- `MESSAGE CONTENT INTENT`

## Slash Command Sync

- For fast dev iteration, set `DEV_GUILD_ID` in `.env` to sync slash commands to one guild.
- Leave `DEV_GUILD_ID` empty to sync globally (production).

## Logging

- `LOG_LEVEL` controls verbosity (prod default: `WARNING`; use `INFO` or `DEBUG` for dev).
- `LOG_TO_FILE=true` enables rotating file logs at `LOG_FILE`.
- `LOG_JSON=true` outputs JSON logs.
- `LOG_AUDIT_FILE` writes audit logs to a separate file if set.

## Data & Schema

- Shared DB schema lives in `app/db/schema.sql`.
- Feature-specific schemas live under each feature (e.g. `app/features/temp_voice/schema.sql`).
- `init_db` loads all schema files on startup, so new tables are created automatically.

## Admin Commands

- `!sethub <voice_channel>`
- `!unsethub <voice_channel>`
- `!settempcategory <category>`
- `!cleartempcategory`
- `!listhubs`
- `!setcommandchannel [text_channel]`
- `!clearcommandchannel`

## General Commands

- `!help`
- `!commandchannel`
