from __future__ import annotations

from discord.ext import commands
import discord

from app.db.repo import Repository
from app.services.reconcile import ReconcileService
from app.services.temp_voice import TempVoiceService


def register_event_handlers(
    bot: commands.Bot,
    repo: Repository,
    temp_voice_service: TempVoiceService,
    reconcile_service: ReconcileService,
) -> None:
    @bot.event
    async def on_ready() -> None:
        if getattr(bot, "_reconciled", False):
            return
        setattr(bot, "_reconciled", True)
        await reconcile_service.reconcile()

    @bot.event
    async def on_voice_state_update(
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        if member.bot:
            return

        if after.channel and isinstance(after.channel, discord.VoiceChannel):
            if repo.is_hub_channel(member.guild.id, after.channel.id):
                await temp_voice_service.handle_join_hub(member, after.channel)
                return

            if repo.get_managed_channel(after.channel.id):
                temp_voice_service.cancel_deletion(after.channel.id)

        if before.channel and isinstance(before.channel, discord.VoiceChannel):
            if repo.get_managed_channel(before.channel.id):
                await temp_voice_service.handle_managed_channel_activity(before.channel)
