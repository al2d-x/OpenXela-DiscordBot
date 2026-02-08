from __future__ import annotations

import discord
from discord.ext import commands

from app.core.logging import bind_event_id, new_event_id
from app.features.temp_voice.repo import TempVoiceRepository


REPO_URL = "https://github.com/al2d-x/OpenXela-DiscordBot"


def register_general_commands(bot: commands.Bot, repo: TempVoiceRepository) -> None:
    @bot.command(name="help")
    async def help_command(ctx: commands.Context) -> None:
        with bind_event_id(new_event_id()):
            await ctx.send(
                "OpenXela Discord Bot help:\n"
                f"Repo: {REPO_URL}\n"
                "Use /room commands in a temp voice room, or admin commands to configure hubs."
            )

    @bot.command(name="setcommandchannel")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def set_command_channel(
        ctx: commands.Context, channel: discord.TextChannel | None = None
    ) -> None:
        with bind_event_id(new_event_id()):
            target = channel
            if target is None:
                if isinstance(ctx.channel, discord.TextChannel):
                    target = ctx.channel
                else:
                    await ctx.send("Provide a text channel in this server.")
                    return

            repo.set_command_channel(ctx.guild.id, target.id)
            await ctx.send(f"Command channel set: {target.mention}")

    @bot.command(name="clearcommandchannel")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def clear_command_channel(ctx: commands.Context) -> None:
        with bind_event_id(new_event_id()):
            repo.set_command_channel(ctx.guild.id, None)
            await ctx.send("Command channel restriction cleared.")

    @bot.command(name="commandchannel")
    @commands.guild_only()
    async def command_channel(ctx: commands.Context) -> None:
        with bind_event_id(new_event_id()):
            channel_id = repo.get_command_channel(ctx.guild.id)
            if channel_id is None:
                await ctx.send("Command channel restriction is not set.")
                return

            channel = ctx.guild.get_channel(channel_id)
            if channel is None:
                await ctx.send(f"Command channel is set to missing channel id `{channel_id}`.")
                return

            await ctx.send(f"Command channel: {channel.mention}")

    @set_command_channel.error
    @clear_command_channel.error
    async def general_admin_command_error(
        ctx: commands.Context, error: commands.CommandError
    ) -> None:
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need Manage Server permission for this command.")
            return
        if isinstance(error, commands.BadArgument):
            await ctx.send("Invalid channel argument.")
            return
        raise error
