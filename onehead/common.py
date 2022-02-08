import os
import json


class OneHeadException(BaseException):
    pass


class OneHeadCommon(object):

    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    @staticmethod
    def get_player_names(t1, t2):
        """
        Obtain player names from player profiles.

        :param t1: Player Profiles for Team 1.
        :type t1: list of dicts.
        :param t2: Player Profiles for Team 2.
        :type t2: list of dicts.
        :return: Names for players on each team.
        :type: tuple of lists, each list item is a str referring to a player name.
        """

        t1_names = [x["name"] for x in t1]
        t2_names = [x["name"] for x in t2]

        return t1_names, t2_names

    @classmethod
    def load_config(cls):

        try:
            with open(os.path.join(cls.ROOT_DIR, "config.json"), "r") as f:
                config = json.load(f)
        except IOError as e:
            raise OneHeadException("{}".format(e))

        return config
