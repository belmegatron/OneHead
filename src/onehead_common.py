

class OneHeadException(BaseException):
    pass


class OneHeadCommon(object):

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

        t1_names = [x['name'] for x in t1]
        t2_names = [x['name'] for x in t2]

        return t1_names, t2_names
