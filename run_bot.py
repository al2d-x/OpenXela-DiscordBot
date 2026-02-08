from app.core.config import get_settings, require_discord_token
from app.core.logging import setup_logging
from app.db.connect import init_db
from app.discord.bot import build_bot
from app.features.temp_voice.events import register_event_handlers
from app.features.temp_voice.reconcile import ReconcileService
from app.features.temp_voice.repo import TempVoiceRepository
from app.features.temp_voice.service import TempVoiceService


def main() -> None:
    settings = get_settings()
    token = require_discord_token(settings)
    setup_logging(settings.log_level)
    init_db(settings.sqlite_path)

    temp_voice_repo = TempVoiceRepository(settings.sqlite_path)
    bot = build_bot(settings, temp_voice_repo)
    temp_voice_service = TempVoiceService(bot, temp_voice_repo, settings.delete_delay_seconds)
    reconcile_service = ReconcileService(bot, temp_voice_repo, temp_voice_service)
    register_event_handlers(
        bot, temp_voice_repo, temp_voice_service, reconcile_service, settings.dev_guild_id
    )

    bot.run(token)


if __name__ == "__main__":
    main()
