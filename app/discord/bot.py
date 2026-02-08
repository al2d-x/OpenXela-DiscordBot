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
    intents.message_content = True

    bot = commands.Bot(command_prefix=settings.discord_command_prefix, intents=intents)
    bot.remove_command("help")
    register_general_commands(bot, repo)
    register_admin_commands(bot, repo)
    register_room_commands(bot, repo)

    @bot.check
    async def command_channel_check(ctx: commands.Context) -> bool:
        if ctx.guild is None:
            return True

        if isinstance(ctx.author, discord.Member):
            if ctx.author.guild_permissions.manage_guild or ctx.author.id == ctx.guild.owner_id:
                return True

        command_channel_id = repo.get_command_channel(ctx.guild.id)
        if command_channel_id is None:
            return True

        return ctx.channel.id == command_channel_id

    @bot.event
    async def on_command_error(ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.CheckFailure) and ctx.guild is not None:
            command_channel_id = repo.get_command_channel(ctx.guild.id)
            if command_channel_id is not None:
                channel = ctx.guild.get_channel(command_channel_id)
                if channel is not None:
                    await ctx.send(f"Use commands in {channel.mention}.")
                else:
                    await ctx.send(f"Use commands in configured channel id `{command_channel_id}`.")
                return
        raise error

    return bot
