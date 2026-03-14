from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

import discord
from discord.ext import commands

from app.features.temp_voice.repo import TempVoiceRepository
from app.features.temp_voice.naming import owner_room_name


logger = logging.getLogger(__name__)


class TempVoiceService:
    def __init__(self, bot: commands.Bot, repo: TempVoiceRepository, delete_delay_seconds: int = 30) -> None:
        self._bot = bot
        self._repo = repo
        self._delete_delay_seconds = delete_delay_seconds
        self._delete_tasks: dict[int, asyncio.Task[None]] = {}
        self._join_times: dict[int, dict[int, datetime]] = {}

    async def handle_join_hub(self, member: discord.Member, hub_channel: discord.VoiceChannel) -> None:
        if member.bot:
            return

        guild = hub_channel.guild
        configured_category_id = self._repo.get_temp_category(guild.id)
        category = guild.get_channel(configured_category_id) if configured_category_id else hub_channel.category
        if configured_category_id and not isinstance(category, discord.CategoryChannel):
            category = hub_channel.category

        room_name = owner_room_name(member.display_name)

        new_channel = await guild.create_voice_channel(
            name=room_name,
            category=category,
            reason=f"Temporary voice room for {member.id}",
        )

        self._repo.upsert_managed_channel(
            guild_id=guild.id,
            channel_id=new_channel.id,
            owner_user_id=member.id,
            hub_channel_id=hub_channel.id,
            name=new_channel.name,
        )

        logger.info("Created temp channel guild=%s channel=%s owner=%s", guild.id, new_channel.id, member.id)

        try:
            await member.move_to(new_channel, reason="Move member into temp voice room")
        except discord.DiscordException:
            logger.exception("Failed to move member; deleting created temp channel channel=%s", new_channel.id)
            await self.delete_channel_now(new_channel, reason="Cleanup after failed move")

    async def handle_managed_channel_activity(self, channel: discord.VoiceChannel) -> None:
        managed = self._repo.get_managed_channel(channel.id)
        if not managed:
            return

        non_bot_count = sum(1 for member in channel.members if not member.bot)
        if non_bot_count == 0:
            await self.schedule_deletion(channel)
            return

        self.cancel_deletion(channel.id)

    def record_member_join(self, channel: discord.VoiceChannel, member: discord.Member) -> None:
        if member.bot:
            return
        joined_at = datetime.now(UTC)
        per_channel = self._join_times.setdefault(channel.id, {})
        per_channel[member.id] = joined_at

    def record_member_leave(self, channel: discord.VoiceChannel, member: discord.Member) -> None:
        per_channel = self._join_times.get(channel.id)
        if not per_channel:
            return
        per_channel.pop(member.id, None)
        if not per_channel:
            self._join_times.pop(channel.id, None)

    async def handle_owner_left(self, channel: discord.VoiceChannel, owner_id: int) -> None:
        managed = self._repo.get_managed_channel(channel.id)
        if not managed:
            return
        try:
            current_owner_id = int(managed["owner_user_id"])
        except (KeyError, ValueError, TypeError):
            return
        if current_owner_id != owner_id:
            return

        remaining = [member for member in channel.members if not member.bot]
        if not remaining:
            return

        new_owner = self._pick_oldest_member(channel.id, remaining)
        if new_owner is None:
            return

        self._repo.update_managed_owner(channel.id, new_owner.id)
        logger.info(
            "Transferred temp channel ownership guild=%s channel=%s from=%s to=%s",
            channel.guild.id,
            channel.id,
            owner_id,
            new_owner.id,
        )

    def _pick_oldest_member(
        self, channel_id: int, members: list[discord.Member]
    ) -> discord.Member | None:
        per_channel = self._join_times.get(channel_id, {})

        def sort_key(member: discord.Member) -> tuple[bool, datetime]:
            joined_at = per_channel.get(member.id)
            if joined_at is None:
                fallback = member.joined_at or datetime.now(UTC)
                return (True, fallback)
            return (False, joined_at)

        return min(members, key=sort_key) if members else None

    async def schedule_deletion(self, channel: discord.VoiceChannel) -> None:
        if channel.id in self._delete_tasks:
            return

        pending_delete_at = (datetime.now(UTC) + timedelta(seconds=self._delete_delay_seconds)).isoformat()
        self._repo.set_pending_delete_at(channel.id, pending_delete_at)

        task = asyncio.create_task(self._delete_after_delay(channel.guild.id, channel.id))
        self._delete_tasks[channel.id] = task
        logger.info("Scheduled delete guild=%s channel=%s at=%s", channel.guild.id, channel.id, pending_delete_at)

    def cancel_deletion(self, channel_id: int) -> None:
        task = self._delete_tasks.pop(channel_id, None)
        if task:
            task.cancel()
            logger.info("Canceled scheduled delete channel=%s", channel_id)
        self._repo.set_pending_delete_at(channel_id, None)

    async def _delete_after_delay(self, guild_id: int, channel_id: int) -> None:
        try:
            await asyncio.sleep(self._delete_delay_seconds)

            guild = self._bot.get_guild(guild_id)
            if guild is None:
                self._repo.remove_managed_channel(channel_id)
                return

            raw_channel = guild.get_channel(channel_id)
            if raw_channel is None or not isinstance(raw_channel, discord.VoiceChannel):
                self._repo.remove_managed_channel(channel_id)
                return

            non_bot_count = sum(1 for member in raw_channel.members if not member.bot)
            if non_bot_count == 0:
                await self.delete_channel_now(
                    raw_channel,
                    reason="Temporary channel empty",
                    cancel_pending=False,
                )
            else:
                self._repo.set_pending_delete_at(channel_id, None)
        except asyncio.CancelledError:
            pass
        finally:
            self._delete_tasks.pop(channel_id, None)

    async def delete_channel_now(
        self, channel: discord.VoiceChannel, reason: str, cancel_pending: bool = True
    ) -> None:
        channel_id = channel.id
        if cancel_pending:
            self.cancel_deletion(channel_id)
        else:
            self._repo.set_pending_delete_at(channel_id, None)
        try:
            await channel.delete(reason=reason)
            logger.info("Deleted temp channel guild=%s channel=%s", channel.guild.id, channel_id)
        except discord.NotFound:
            logger.info("Temp channel already missing channel=%s", channel_id)
        except discord.DiscordException:
            logger.exception("Failed deleting temp channel channel=%s", channel_id)
        finally:
            self._repo.remove_managed_channel(channel_id)
