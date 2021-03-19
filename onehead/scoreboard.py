from tabulate import tabulate
from discord.ext import commands

from onehead.common import OneHeadException
from onehead.stats import OneHeadStats


class OneHeadScoreBoard(commands.Cog):

    def __init__(self, database):

        self.db = database

    @commands.has_role("IHL")
    @commands.command(aliases=['sb'])
    async def scoreboard(self, ctx):
        """
        Shows the current rankings for the IGC IHL Leaderboard.
        """

        scoreboard = self._get_scoreboard()
        await ctx.send("**IGC Leaderboard** ```\n{}```".format(scoreboard))

    @staticmethod
    def _sort_scoreboard_key_order(scoreboard):
        """
        Sets the column order for the scoreboard by ordering the keys for each row.

        :param scoreboard: Unsorted scoreboard
        :type scoreboard: list of dicts
        :return: Sorted scoreboard
        :type: list of dicts
        """

        key_order = ["#", "name", "win", "loss", "%", "rating"]
        sorted_scoreboard = []

        for record in scoreboard:
            record = {k: record[k] for k in key_order}
            sorted_scoreboard.append(record)

        return sorted_scoreboard

    @staticmethod
    def _calculate_positions(scoreboard, sort_key):
        """
        Calculates the position for each player on the scoreboard based on a particular sort key.

        :param scoreboard: Scoreboard containing all IHL players.
        :type scoreboard: list of dicts
        :param sort_key: The key by which to sort the scoreboard.
        :type sort_key: str
        :return: Scoreboard sorted in descending order with additional '#' field.
        :type: list of dicts
        """

        scoreboard = sorted(scoreboard, key=lambda k: k[sort_key], reverse=True)
        scoreboard_positions = []

        pos = 1
        modifier = 1

        for i, record in enumerate(scoreboard):
            if i != 0:
                if scoreboard[i - 1][sort_key] > scoreboard[i][sort_key]:
                    pos += modifier
                    modifier = 1
                else:
                    modifier += 1

            record["#"] = pos
            scoreboard_positions.append(record)

        return scoreboard_positions

    def _get_scoreboard(self):
        """
        Returns current scoreboard for the IHL.

        :return: Scoreboard string to be displayed in Discord chat.
        :type: str
        """

        scoreboard = self.db.retrieve_table()

        if not scoreboard:
            raise OneHeadException("No users found in database.")

        OneHeadStats.calculate_win_percentage(scoreboard)
        OneHeadStats.calculate_rating(scoreboard)
        sorted_scoreboard = self._calculate_positions(scoreboard, "rating")
        sorted_scoreboard = self._sort_scoreboard_key_order(sorted_scoreboard)
        sorted_scoreboard = tabulate(sorted_scoreboard, headers="keys", tablefmt="simple")

        return sorted_scoreboard


