from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from app.core.logging import bind_event_id, new_event_id
from app.features.temp_voice.repo import TempVoiceRepository


logger = logging.getLogger(__name__)


def register_room_commands(bot: commands.Bot, repo: TempVoiceRepository) -> None:
    group = app_commands.Group(name="room", description="Manage your temp voice room")

    def _get_member_channel(member: discord.Member) -> discord.VoiceChannel | None:
        if member.voice and isinstance(member.voice.channel, discord.VoiceChannel):
            return member.voice.channel
        return None

    def _get_managed_channel(channel: discord.VoiceChannel) -> dict | None:
        return repo.get_managed_channel(channel.id)

    def _is_owner_or_admin(member: discord.Member, managed: dict) -> bool:
        if member.guild_permissions.manage_channels:
            return True
        try:
            return int(managed["owner_user_id"]) == member.id
        except (KeyError, ValueError, TypeError):
            return False

    async def _require_managed_channel(
        interaction: discord.Interaction,
    ) -> tuple[discord.VoiceChannel | None, dict | None]:
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Run this inside a server.", ephemeral=True)
            return None, None
        channel = _get_member_channel(interaction.user)
        if channel is None:
            await interaction.response.send_message("Join a voice channel first.", ephemeral=True)
            return None, None
        managed = _get_managed_channel(channel)
        if not managed:
            await interaction.response.send_message(
                "That voice channel isn't managed by the temp hub feature.", ephemeral=True
            )
            return None, None
        if not _is_owner_or_admin(interaction.user, managed):
            await interaction.response.send_message(
                "Only the room owner or a server admin can use this.", ephemeral=True
            )
            return None, None
        return channel, managed

    @group.command(name="name", description="Rename your temp voice room")
    @app_commands.describe(new_name="New room name")
    async def room_name(interaction: discord.Interaction, new_name: str) -> None:
        with bind_event_id(new_event_id()):
            channel, _managed = await _require_managed_channel(interaction)
            if channel is None:
                return
            sanitized = " ".join(new_name.split()).strip()
            if not sanitized:
                await interaction.response.send_message("Name can't be empty.", ephemeral=True)
                return
            sanitized = sanitized[:100]
            await channel.edit(name=sanitized, reason=f"Room rename by {interaction.user.id}")
            repo.update_managed_name(channel.id, sanitized)
            await interaction.response.send_message(f"Room renamed to **{sanitized}**.", ephemeral=True)

    @group.command(name="limit", description="Set a user limit for your room (0 = unlock)")
    @app_commands.describe(limit="Max users allowed (0 = unlock)")
    async def room_limit(interaction: discord.Interaction, limit: app_commands.Range[int, 0, 99]) -> None:
        with bind_event_id(new_event_id()):
            channel, _managed = await _require_managed_channel(interaction)
            if channel is None:
                return
            await channel.edit(user_limit=int(limit), reason=f"Room limit by {interaction.user.id}")
            if limit == 0:
                await interaction.response.send_message("Room user limit cleared.", ephemeral=True)
            else:
                await interaction.response.send_message(f"Room user limit set to {limit}.", ephemeral=True)

    @group.command(name="lock", description="Lock your room (deny @everyone from connecting)")
    async def room_lock(interaction: discord.Interaction) -> None:
        with bind_event_id(new_event_id()):
            channel, _managed = await _require_managed_channel(interaction)
            if channel is None:
                return
            overwrite = channel.overwrites_for(channel.guild.default_role)
            overwrite.connect = False
            await channel.set_permissions(channel.guild.default_role, overwrite=overwrite)
            await interaction.response.send_message("Room locked.", ephemeral=True)

    @group.command(name="unlock", description="Unlock your room (restore @everyone connect)")
    async def room_unlock(interaction: discord.Interaction) -> None:
        with bind_event_id(new_event_id()):
            channel, _managed = await _require_managed_channel(interaction)
            if channel is None:
                return
            overwrite = channel.overwrites_for(channel.guild.default_role)
            overwrite.connect = None
            await channel.set_permissions(channel.guild.default_role, overwrite=overwrite)
            await interaction.response.send_message("Room unlocked.", ephemeral=True)

    @group.command(name="transfer", description="Transfer room ownership to another member inside")
    @app_commands.describe(member="Member to transfer ownership to")
    async def room_transfer(interaction: discord.Interaction, member: discord.Member) -> None:
        with bind_event_id(new_event_id()):
            channel, managed = await _require_managed_channel(interaction)
            if channel is None or managed is None:
                return
            if member.bot:
                await interaction.response.send_message("Bots can't own rooms.", ephemeral=True)
                return
            if member.voice is None or member.voice.channel is None or member.voice.channel.id != channel.id:
                await interaction.response.send_message(
                    "That member must be in the same voice channel.", ephemeral=True
                )
                return
            repo.update_managed_owner(channel.id, member.id)
            logger.info(
                "Manual ownership transfer guild=%s channel=%s from=%s to=%s",
                channel.guild.id,
                channel.id,
                interaction.user.id,
                member.id,
            )
            await interaction.response.send_message(
                f"Room ownership transferred to {member.mention}.", ephemeral=True
            )

    bot.tree.add_command(group)
