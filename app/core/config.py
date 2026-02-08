import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    discord_token: str
    discord_command_prefix: str
    sqlite_path: str
    delete_delay_seconds: int
    log_level: str
    dev_guild_id: int | None


def require_discord_token(settings: Settings) -> str:
    token = settings.discord_token.strip()
    if not token:
        raise ValueError("DISCORD_TOKEN is required to run the bot")
    return token


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    load_dotenv()

    return Settings(
        discord_token=os.getenv("DISCORD_TOKEN", "").strip(),
        discord_command_prefix=os.getenv("DISCORD_COMMAND_PREFIX", "!").strip() or "!",
        sqlite_path=os.getenv("SQLITE_PATH", "data/bot.db").strip() or "data/bot.db",
        delete_delay_seconds=int(os.getenv("TEMP_DELETE_DELAY_SECONDS", "30")),
        log_level=os.getenv("LOG_LEVEL", "WARNING").upper(),
        dev_guild_id=(
            int(os.getenv("DEV_GUILD_ID", "").strip())
            if os.getenv("DEV_GUILD_ID", "").strip()
            else None
        ),
    )
