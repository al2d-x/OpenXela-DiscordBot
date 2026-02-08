from __future__ import annotations

import discord
from discord.ext import commands

from app.core.config import Settings
from app.db.repo import Repository
from app.discord.commands import register_admin_commands


def build_bot(settings: Settings, repo: Repository) -> commands.Bot:
    intents = discord.Intents.default()
    intents.guilds = True
    intents.voice_states = True
    intents.members = True

    bot = commands.Bot(command_prefix=settings.discord_command_prefix, intents=intents)
    register_admin_commands(bot, repo)
    return bot
