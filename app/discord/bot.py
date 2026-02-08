from __future__ import annotations

import discord
from discord.ext import commands

from app.core.config import Settings
from app.discord.general_commands import register_general_commands
from app.features.temp_voice.admin_commands import register_admin_commands
from app.features.temp_voice.room_commands import register_room_commands
from app.features.temp_voice.repo import TempVoiceRepository


def build_bot(settings: Settings, repo: TempVoiceRepository) -> commands.Bot:
    intents = discord.Intents.default()
    intents.guilds = True
    intents.voice_states = True
    intents.members = True

    bot = commands.Bot(command_prefix=settings.discord_command_prefix, intents=intents)
    bot.remove_command("help")
    register_general_commands(bot)
    register_admin_commands(bot, repo)
    register_room_commands(bot, repo)
    return bot
