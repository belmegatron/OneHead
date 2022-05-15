import json
import os
from typing import TYPE_CHECKING, Optional, Any, Union, TypedDict

from discord.ext.commands import Bot

if TYPE_CHECKING:

    class Player(TypedDict):
        name: str
        mmr: int
        win: int
        loss: int
        rbucks: int
        rating: int
        adjusted_mmr: int

    Team = tuple[Player, Player, Player, Player, Player]
    TeamCombination = tuple[Team, Team]

# We need a globally accessible reference to the bot instance for event handlers that require Cog functionality.
bot = None  # type: Optional[Bot]

RADIANT = "radiant"
DIRE = "dire"


class OneHeadException(BaseException):
    pass


class OneHeadCommon(object):
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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

        t1_names = tuple([x["name"] for x in t1])  # type: tuple[str, ...]
        t2_names = tuple([x["name"] for x in t2])  # type: tuple[str, ...]

        return t1_names, t2_names

    @classmethod
    def load_config(cls) -> dict:

        try:
            with open(os.path.join(cls.ROOT_DIR, "config.json"), "r") as f:
                config = json.load(f)  # type: dict
        except IOError as e:
            raise OneHeadException(e)

        return config
