import json
import os
import sys
from logging import Formatter, Logger, StreamHandler, getLogger
from typing import Literal, Optional, TypedDict

from discord.ext.commands import Bot
from strenum import StrEnum


class OneHeadRoles(StrEnum):

    ADMIN: Literal["IHL Admin"] = "IHL Admin"
    MEMBER: Literal["IHL"] = "IHL"


Player = TypedDict("Player", {"#": int, "name": str, "mmr": int, "win": int, "loss": int, "rbucks": int, "rating": int, "adjusted_mmr": int, "%": float})


Team = tuple[Player, Player, Player, Player, Player]
TeamCombination = tuple[Team, Team]

log: Logger = getLogger("onehead")

# We need a globally accessible reference to the bot instance for event handlers that require Cog functionality.
bot: Optional[Bot] = None

RADIANT: Literal["radiant"] = "radiant"
DIRE: Literal["dire"] = "dire"


class OneHeadException(BaseException):
    pass


class OneHeadCommon(object):
    ROOT_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    @staticmethod
    def get_player_names(
        t1: "Team", t2: "Team"
    ) -> tuple[tuple[str, ...], tuple[str, ...]]:
        """
        Obtain player names from player profiles.

        :param t1: Player Profiles for Team 1.
        :param t2: Player Profiles for Team 2.
        :return: Names of players on each team.
        """

        t1_names: tuple[str, ...] = tuple(sorted([x["name"] for x in t1]))
        t2_names: tuple[str, ...] = tuple(sorted([x["name"] for x in t2]))

        return t1_names, t2_names

    @classmethod
    def load_config(cls) -> dict:

        try:
            with open(os.path.join(cls.ROOT_DIR, "secrets/config.json"), "r") as f:
                config: dict = json.load(f)
        except IOError as e:
            raise OneHeadException(e)

        return config


def setup_log() -> None:
    handler: StreamHandler = StreamHandler(stream=sys.stdout)
    formatter: Formatter = Formatter(
        fmt="%(asctime)s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    log.addHandler(handler)
