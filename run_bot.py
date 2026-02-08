from app.core.config import get_settings, require_discord_token
from app.core.logging import setup_logging
from app.db.connect import init_db
from app.db.repo import Repository
from app.discord.bot import build_bot
from app.discord.events import register_event_handlers
from app.services.reconcile import ReconcileService
from app.services.temp_voice import TempVoiceService


def main() -> None:
    settings = get_settings()
    token = require_discord_token(settings)
    setup_logging(settings.log_level)
    init_db(settings.sqlite_path)

    repo = Repository(settings.sqlite_path)
    bot = build_bot(settings, repo)
    temp_voice_service = TempVoiceService(bot, repo, settings.delete_delay_seconds)
    reconcile_service = ReconcileService(bot, repo, temp_voice_service)
    register_event_handlers(bot, repo, temp_voice_service, reconcile_service)

    bot.run(token)


if __name__ == "__main__":
    main()
