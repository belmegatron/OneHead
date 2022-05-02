import json
import os
from typing import Optional, TYPE_CHECKING, Union

from discord.ext.commands import Bot

if TYPE_CHECKING:
    Team = tuple[dict, dict, dict, dict, dict]
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
    def get_player_names(t1: "Team", t2: "Team") -> tuple[tuple[str], tuple[str]]:
        """
        Obtain player names from player profiles.

        :param t1: Player Profiles for Team 1.
        :param t2: Player Profiles for Team 2.
        :return: Names of players on each team.
        """

        t1_names = [x["name"] for x in t1]
        t2_names = [x["name"] for x in t2]

        return t1_names, t2_names

    @classmethod
    def load_config(cls) -> dict:

        try:
            with open(os.path.join(cls.ROOT_DIR, "config.json"), "r") as f:
                config = json.load(f)
        except IOError as e:
            raise OneHeadException(e)

        return config
