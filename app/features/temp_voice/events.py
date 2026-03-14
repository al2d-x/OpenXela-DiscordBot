from __future__ import annotations

import asyncio
import logging

from discord.ext import commands
import discord

from app.features.temp_voice.repo import TempVoiceRepository
from app.core.logging import bind_event_id, new_event_id
from app.discord.sync import sync_commands
from app.features.temp_voice.reconcile import ReconcileService
from app.features.temp_voice.service import TempVoiceService


logger = logging.getLogger(__name__)


def register_event_handlers(
    bot: commands.Bot,
    repo: TempVoiceRepository,
    temp_voice_service: TempVoiceService,
    reconcile_service: ReconcileService,
    dev_guild_id: int | None,
) -> None:
    @bot.event
    async def on_ready() -> None:
        if bot.user is None:
            logger.info("Bot is ready.")
        else:
            logger.info(
                "Bot is ready as %s (%s) in %s guild(s).",
                bot.user.name,
                bot.user.id,
                len(bot.guilds),
            )
        if not getattr(bot, "_synced", False):
            try:
                await sync_commands(bot, dev_guild_id)
                setattr(bot, "_synced", True)
            except discord.DiscordException:
                pass
        await reconcile_service.reconcile()

    @bot.event
    async def on_guild_channel_delete(channel: discord.abc.GuildChannel) -> None:
        if not isinstance(channel, discord.VoiceChannel):
            return
        if repo.get_managed_channel(channel.id):
            temp_voice_service.cancel_deletion(channel.id)
            repo.remove_managed_channel(channel.id)
            logger.info(
                "Cleaned managed channel after manual deletion guild=%s channel=%s",
                channel.guild.id,
                channel.id,
            )

    @bot.event
    async def on_voice_state_update(
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        if member.bot:
            return
        with bind_event_id(new_event_id()):

            before_channel_id = before.channel.id if before.channel else None
            after_channel_id = after.channel.id if after.channel else None

            if after.channel and isinstance(after.channel, discord.VoiceChannel) and after_channel_id != before_channel_id:
                if repo.is_hub_channel(member.guild.id, after.channel.id):
                    await temp_voice_service.handle_join_hub(member, after.channel)
                    return

                if repo.get_managed_channel(after.channel.id):
                    temp_voice_service.record_member_join(after.channel, member)
                    temp_voice_service.cancel_deletion(after.channel.id)

            if before.channel and isinstance(before.channel, discord.VoiceChannel) and before_channel_id != after_channel_id:
                if repo.get_managed_channel(before.channel.id):
                    channel_id = before.channel.id
                    temp_voice_service.record_member_leave(before.channel, member)
                    # Discord member lists can be briefly stale during voice-state transitions.
                    # Re-fetch after a short delay so empty-channel cleanup is accurate.
                    await asyncio.sleep(1)
                    refreshed_channel = member.guild.get_channel(channel_id)
                    if isinstance(refreshed_channel, discord.VoiceChannel):
                        await temp_voice_service.handle_owner_left(refreshed_channel, member.id)
                        await temp_voice_service.handle_managed_channel_activity(refreshed_channel)
                    else:
                        repo.remove_managed_channel(channel_id)
