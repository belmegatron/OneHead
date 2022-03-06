import json
import os


class OneHeadException(BaseException):
    pass


class OneHeadCommon(object):

    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    @staticmethod
    def get_player_names(t1: list[dict], t2: list[dict]) -> tuple[list, list]:
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
