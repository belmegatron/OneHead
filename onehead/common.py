from asyncio import sleep
from dataclasses import dataclass
from enum import StrEnum
from logging import Logger
from pathlib import Path
from typing import cast

from discord.channel import VocalGuildChannel
from discord.errors import ClientException
from discord.ext.commands import Cog, Command, Context
from discord.member import Member, VoiceState
from discord.player import FFmpegPCMAudio
from discord.user import User
from discord.voice_client import VoiceClient
from structlog import get_logger

log: Logger = get_logger()


ROOT_DIR: Path = Path(__file__).resolve().parent.parent


@dataclass
class Player:
    id: int
    name: str
    mmr: int
    win: int = 0
    loss: int = 0
    win_streak: int = 0
    loss_streak: int = 0
    rbucks: int = 0
    rating: int = 1500
    commends: int = 0
    reports: int = 0
    behaviour: int = 10000
    pos: int | None = None
    adjusted_mmr: int | None = None
    win_percentage: float | None = None
    duel_win: int = 0
    duel_loss: int = 0
    duel_win_percentage: float | None = None
    duel_rating: int = 0
    
    def __lt__(self, other) -> bool:
        return self.rating < other.rating
    
    def __le__(self, other) -> bool:
        return self.rating <= other.rating
    
    def __gt__(self, other) -> bool:
        return self.rating > other.rating
    
    def __ge__(self, other) -> bool:
        return self.rating >= other.rating
    
    def __eq__(self, other) -> bool:
        return self.id == other.id
    
    def __ne__(self, other) -> bool:
        return self.id != other.id
 
 
Team = tuple[Player, Player, Player, Player, Player]
TeamCombination = tuple[Team, Team]


@dataclass
class Metadata:
    timestamp: float
    season: int = 1
    game_id: int = 1
    max_game_count: int = 50


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
    t1_names: tuple[str, ...] = tuple(sorted([x.name for x in t1]))
    t2_names: tuple[str, ...] = tuple(sorted([x.name for x in t2]))

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
    voice_channel: VocalGuildChannel | None = None
    member: User | Member = cast(Member, ctx.author)
    voice_state: VoiceState | None = cast(VoiceState, member.voice)
    
    try:
        if voice_client is None:
            if voice_state:
                voice_channel = voice_state.channel
                if voice_channel:
                    voice_client = await voice_channel.connect()
        else:
            if voice_state:
                voice_channel = voice_state.channel
            
            if voice_channel and voice_client.channel.name != voice_channel.name:
                await voice_client.move_to(voice_channel)

        if voice_client is None:
            log.warning(f"Skipping playing {file_name} as {member.display_name} is not in a voice channel.")
            return

        voice_client.play(FFmpegPCMAudio(f"onehead/sounds/{file_name}"))
    
    except Exception as ex:
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
