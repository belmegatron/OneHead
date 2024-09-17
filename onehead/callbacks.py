from functools import cache
from logging import Logger
from typing import cast

from discord import Status
from discord.ext.commands import Bot
from discord.member import Member
from discord.message import Message
from structlog import get_logger

from onehead.common import OneHeadException
from onehead.game import Game
from onehead.lobby import Lobby
from onehead.store import GameStore


log: Logger = get_logger()

# We need a globally accessible reference to the bot instance in order for our callbacks to work.
bot: Bot | None = None


def set_bot_instance(new_bot_instance: Bot) -> None:
    global bot
    bot = new_bot_instance


def get_bot_instance() -> Bot:
    if bot is None:
        raise OneHeadException("Global bot instance is None")

    return bot


async def on_presence_update(before: Member, after: Member) -> None:
    bot: Bot = get_bot_instance()
    store: GameStore = cast(GameStore, bot.get_cog("GameStore"))
    game: Game | None = store.current_game

    if game and game.in_progress():
        return

    lobby: Lobby = cast(Lobby, bot.get_cog("Lobby"))
    if lobby._context is None:
        return

    signups: list[str] = lobby.get_signups()

    name: str = after.display_name

    if after.status in (Status.offline, Status.idle) and name in signups:
        reason: str = "Offline" if after.status == Status.offline else "Idle"
        log.info(f"{name} is now {reason}.")
        lobby.remove_player_from_signups(name)
        await lobby._context.send(f"{after.mention} has been signed out due to being {reason}.")


@cache
def get_supported_bot_commands(bot: Bot) -> list[str]:
    commands: list[str] = [command.name for command in bot.commands]
    command_aliases: list[str] = []
    for cmd in bot.commands:
        command_aliases += cmd.aliases

    return commands + command_aliases


async def allow_message(message: Message, bot: Bot) -> bool:
    split_message: list[str] = message.content.split()
    user_command: str = split_message[0]

    prefix: str = user_command[0]
    if prefix != bot.command_prefix:
        return True

    supported_commands: list[str] = get_supported_bot_commands(bot)
    user_command = user_command[1:]
    if user_command not in supported_commands:
        return False

    return True


async def on_message(message: Message) -> None:
    bot: Bot = get_bot_instance()

    if message.author.bot:
        return

    allow: bool = await allow_message(message, bot)
    if allow is False:
        await message.delete()
        return

    await bot.process_commands(message)
