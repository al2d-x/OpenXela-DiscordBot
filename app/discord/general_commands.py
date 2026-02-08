from __future__ import annotations

from discord.ext import commands

from app.core.logging import bind_event_id, new_event_id


REPO_URL = "https://github.com/al2d-x/OpenXela-DiscordBot"


def register_general_commands(bot: commands.Bot) -> None:
    @bot.command(name="help")
    async def help_command(ctx: commands.Context) -> None:
        with bind_event_id(new_event_id()):
            await ctx.send(
                "OpenXela Discord Bot help:\n"
                f"Repo: {REPO_URL}\n"
                "Use /room commands in a temp voice room, or admin commands to configure hubs."
            )
