# OpenXela Discord Bot

Basic administrative tasks bot for Discord.

## Features

| Feature | Command(s) | What it does |
| --- | --- | --- |
| Temp Voice Hubs | `!sethub`, `!unsethub`, `!listhubs` | Mark voice channels as hubs so joining them creates a temporary room and moves the user into it. |
| Temp Voice Category | `!settempcategory`, `!cleartempcategory` | Choose which category new temp voice rooms are created under (falls back to the hub's category if unset). |

## Setup

1. Create `.env` from `.env.example`.
2. Install dependencies:

   pip install -r requirements.txt

## Run

- Bot: `python run_bot.py`
- API: `python run_api.py`

## Admin Commands

- `!sethub <voice_channel>`
- `!unsethub <voice_channel>`
- `!settempcategory <category>`
- `!cleartempcategory`
- `!listhubs`
