from asyncio import sleep
from dataclasses import dataclass
from enum import StrEnum
from logging import Logger
from pathlib import Path
from structlog import get_logger
from typing import TypedDict, cast

from discord.channel import VocalGuildChannel
from discord.ext.commands import Context, Cog, Command
from discord.errors import ClientException
from discord.member import Member, VoiceState
from discord.player import FFmpegPCMAudio
from discord.voice_client import VoiceClient


log: Logger = get_logger()


ROOT_DIR: Path = Path(__file__).resolve().parent.parent


Player = TypedDict(
    "Player",
    {
        "#": int,
        "id": int,
        "name": str,
        "mmr": int,
        "win": int,
        "loss": int,
        "rbucks": int,
        "rating": int,
        "adjusted_mmr": int,
        "%": float,
        "commends": int,
        "reports": int,
        "behaviour": int,
    },
)

Team = tuple[Player, Player, Player, Player, Player]
TeamCombination = tuple[Team, Team]

Metadata = TypedDict(
    "Metadata",
    {
        "season": int,
        "game_id": int,
        "max_game_count": int,
        "timestamp": float,
    },
)


class Roles(StrEnum):
    ADMIN = "IHL Admin"
    MEMBER = "IHL"


class Side(StrEnum):
    RADIANT = "radiant"
    DIRE = "dire"


@dataclass
class PlayerTransfer:
    buyer: str
    amount: int


@dataclass
class Bet:
    bettor: str
    selection: str
    stake: int
    price: float = 2.0


class OneHeadException(Exception):
    pass


def get_player_names(t1: "Team", t2: "Team") -> tuple[tuple[str, ...], tuple[str, ...]]:
    """
    Obtain player names from player profiles.

    :param t1: Player Profiles for Team 1.
    :param t2: Player Profiles for Team 2.
    :return: Names of players on each team.
    """
    t1_names: tuple[str, ...] = tuple(sorted([x["name"] for x in t1]))
    t2_names: tuple[str, ...] = tuple(sorted([x["name"] for x in t2]))

    return t1_names, t2_names


def get_discord_member_from_name(ctx: Context, name: str) -> Member | None:
    if ctx.guild is None:
        return None

    if is_mention(name):
        id: int = get_discord_id_from_mention(name)
        return get_discord_member_from_id(ctx, id)
    else:
        for member in ctx.guild.members:
            if member.display_name == name:
                return member

    return None


def get_discord_member_from_id(ctx: Context, id: int) -> Member | None:
    if ctx.guild is None:
        return None

    for member in ctx.guild.members:
        if member.id == id:
            return member

    return None


def is_mention(s: str) -> bool:
    return s[:2] == "<@" and len(s) > 3


def get_discord_id_from_mention(mention: str) -> int:
    try:
        player_id: int = int(mention[2:-1])
    except ValueError:
        raise OneHeadException(f"Failed to extract discord id from mention: {mention}")

    return player_id


async def play_sound(ctx: Context, file_name: str) -> None:
    voice_client: VoiceClient | None = cast(VoiceClient | None, ctx.voice_client)
    if voice_client is None:
        member: Member = cast(Member, ctx.author)
        voice_state: VoiceState | None = cast(VoiceState, member.voice)
        voice_channel: VocalGuildChannel | None = None
        
        if voice_state:
            voice_channel = voice_state.channel
            
        if voice_channel:
            voice_client = await voice_channel.connect()
            
    elif voice_client.channel.name != ctx.author.voice.channel.name:
        await voice_client.move_to(ctx.author.voice.channel)

    try:
        voice_client.play(FFmpegPCMAudio(f"onehead/sounds/{file_name}"))
    except ClientException as ex:
        log.error(f"Failed to play sound '{file_name}' due to {ex}.")


async def voice_client_disconnect(ctx: Context) -> None:
    while True:
        voice_client: VoiceClient | None = cast(VoiceClient | None, ctx.voice_client)
        if voice_client and voice_client.is_playing() is False:
            await voice_client.disconnect()
            break
        else:
            await sleep(5)

def get_command_from_cog(cog: Cog, name: str) -> Command | None:
    for command in cog.get_commands():
        if command.name == name:
            return command
    
    return None