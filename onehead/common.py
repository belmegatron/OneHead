import json
import sys
from dataclasses import dataclass, fields
from enum import Enum, EnumMeta, auto
from logging import DEBUG, Formatter, Logger, StreamHandler, getLogger
from pathlib import Path
from typing import Any, Literal, Optional

from discord.ext.commands import Bot
from strenum import LowercaseStrEnum, StrEnum


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
    

class BehaviourConstants(Enum):
    MAX_BEHAVIOUR_SCORE = 10000
    MIN_BEHAVIOUR_SCORE = 0
    COMMEND = 100
    REPORT = -200


class BettingConstants(Enum):
    INITIAL_BALANCE: Literal[100] = 100
    REWARD_ON_WIN: Literal[100] = 100
    REWARD_ON_LOSS: Literal[50] = 50
    
    
@dataclass
class Player:
    name: str = ""
    mmr: int = 1000
    win: int = 0
    loss: int = 0
    rating: int = 0
    commends: int = 0
    reports: int = 0
    rbucks: int = BettingConstants.INITIAL_BALANCE.value
    behaviour: int = BehaviourConstants.MAX_BEHAVIOUR_SCORE.value


def player_from_dict(d: dict) -> Player:
    fieldSet = {f.name for f in fields(Player) if f.init}
    filteredArgDict = {k: v for k, v in d.items() if k in fieldSet}
    return Player(**filteredArgDict)

        
Team = tuple[Player, Player, Player, Player, Player]
TeamCombination = tuple[Team, Team]


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

    t1_names: tuple[str, ...] = tuple(sorted([x.name for x in t1]))
    t2_names: tuple[str, ...] = tuple(sorted([x.name for x in t2]))

    return t1_names, t2_names


def load_config() -> dict:
    try:
        config_path: Path = Path(ROOT_DIR, "secrets/config.json")
        with open(str(config_path), "r") as f:
            config: dict = json.load(f)
    except IOError as e:
        raise OneHeadException(e)

    return config


def set_logger() -> Logger:
    handler: StreamHandler = StreamHandler(stream=sys.stdout)
    formatter: Formatter = Formatter(fmt="%(asctime)s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    log: Logger = getLogger("onehead")
    log.setLevel(DEBUG)
    log.addHandler(handler)
    return log


log: Logger = set_logger()


def get_logger() -> Logger:
    return log
