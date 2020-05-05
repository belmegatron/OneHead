from tabulate import tabulate
from discord.ext import commands
from onehead_common import OneHeadException
from onehead_stats import OneHeadStats


class OneHeadScoreBoard(commands.Cog):

    def __init__(self, database):

        self.db = database

    @commands.command(aliases=['sb'])
    async def scoreboard(self, ctx):
        """
        Shows the current rankings for the IGC IHL Leaderboard.
        """

        scoreboard = self.get_scoreboard()
        await ctx.send("**IGC Leaderboard** ```\n{}```".format(scoreboard))

    @staticmethod
    def _sort_scoreboard_key_order(scoreboard):

        key_order = ["#", "name", "win", "loss", "%", "rating"]
        sorted_scoreboard = []

        for record in scoreboard:
            record = {k: record[k] for k in key_order}
            sorted_scoreboard.append(record)

        return sorted_scoreboard

    @staticmethod
    def _calculate_positions(scoreboard, sort_key):

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

    def get_scoreboard(self):

        scoreboard = self.db.retrieve_table()

        if not scoreboard:
            raise OneHeadException("No users found in database.")

        OneHeadStats.calculate_win_percentage(scoreboard)
        OneHeadStats.calculate_rating(scoreboard)
        sorted_scoreboard = self._calculate_positions(scoreboard, "rating")
        sorted_scoreboard = self._sort_scoreboard_key_order(sorted_scoreboard)
        sorted_scoreboard = tabulate(sorted_scoreboard, headers="keys", tablefmt="simple")

        return sorted_scoreboard

