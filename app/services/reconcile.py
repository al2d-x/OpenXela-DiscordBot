from __future__ import annotations

import logging

import discord
from discord.ext import commands

from app.db.repo import Repository
from app.services.temp_voice import TempVoiceService


logger = logging.getLogger(__name__)


class ReconcileService:
    def __init__(self, bot: commands.Bot, repo: Repository, temp_voice_service: TempVoiceService) -> None:
        self._bot = bot
        self._repo = repo
        self._temp_voice_service = temp_voice_service

    async def reconcile(self) -> None:
        for row in self._repo.list_managed_channels():
            guild = self._bot.get_guild(int(row["guild_id"]))
            channel_id = int(row["channel_id"])
            if guild is None:
                self._repo.remove_managed_channel(channel_id)
                continue

            channel = guild.get_channel(channel_id)
            if channel is None or not isinstance(channel, discord.VoiceChannel):
                self._repo.remove_managed_channel(channel_id)
                logger.info("Reconcile removed stale managed channel channel=%s", channel_id)
                continue

            non_bot_count = sum(1 for member in channel.members if not member.bot)
            if non_bot_count == 0:
                await self._temp_voice_service.delete_channel_now(channel, reason="Reconcile empty temp channel")
            else:
                self._repo.set_pending_delete_at(channel.id, None)
