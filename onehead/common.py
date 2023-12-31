import json
from dataclasses import dataclass
from enum import EnumMeta, auto
from pathlib import Path
from typing import Any, Literal, Optional, TypedDict

from discord.ext.commands import Bot, Context
from strenum import LowercaseStrEnum, StrEnum

Player = TypedDict(
    "Player",
    {
        "#": int,
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
        "current_game_count": int,
        "max_game_count": int,
        "timestamp": float,
    },
)

# We need a globally accessible reference to the bot instance for event handlers that require Cog functionality.
bot: Optional[Bot] = None

ROOT_DIR: Path = Path(__file__).resolve().parent.parent


class EnumeratorMeta(EnumMeta):
    def __contains__(cls, member: Any) -> bool:
        if type(member) == cls:
            return EnumMeta.__contains__(cls, member)
        else:
            try:
                cls(member)
            except ValueError:
                return False
            return True


class Roles(StrEnum):
    ADMIN: Literal["IHL Admin"] = "IHL Admin"
    MEMBER: Literal["IHL"] = "IHL"


class Side(LowercaseStrEnum, metaclass=EnumeratorMeta):
    RADIANT = auto()
    DIRE = auto()


@dataclass
class PlayerTransfer:
    buyer: str
    amount: int


@dataclass
class Bet:
    side: str
    stake: int
    player: str


class OneHeadException(BaseException):
    pass


def get_bot_instance() -> Bot:
    if bot is None:
        raise OneHeadException("Global bot instance is None")

    return bot


def set_bot_instance(new_bot_instance: Bot) -> None:
    global bot
    bot = new_bot_instance


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


def load_config() -> dict:
    try:
        config_path: Path = Path(ROOT_DIR, "secrets/config.json")
        with open(str(config_path), "r") as f:
            config: dict = json.load(f)
    except IOError as e:
        raise OneHeadException(e)

    return config


def update_config(updated_config: dict) -> None:
    try:
        config_path: Path = Path(ROOT_DIR, "secrets/config.json")
        with open(str(config_path), "w") as f:
            json.dump(updated_config, f)
    except IOError as e:
        raise OneHeadException(e)


def get_discord_id_from_name(ctx: Context, name: str) -> int:
    for member in ctx.guild.members:
        if member.display_name == name:
            return member.id

    return 0
