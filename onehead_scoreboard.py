from tabulate import tabulate
from discord.ext import commands
from onehead_common import OneHeadException


class OneHeadScoreBoard(commands.Cog):

    def __init__(self, database):

        self.database = database
        self.db = self.database.db
        self.user = self.database.user

    @commands.command(aliases=['sb'])
    async def scoreboard(self, ctx):
        """
        Shows the current rankings for the IGC IHL Leaderboard.
        """

        scoreboard = self.get_scoreboard()
        await ctx.send("**IGC Leaderboard** ```\n{}```".format(scoreboard))

    @staticmethod
    def _calculate_win_percentage(scoreboard):

        for record in scoreboard:
            if record['win'] == 0:
                record["%"] = 0
            else:
                record["%"] = round(record['win'] / (record['win'] + record['loss']) * 100, 1)

    @staticmethod
    def _calculate_rating(scoreboard):

        baseline_rating = 1500
        for record in scoreboard:
            win_modifier = record['win'] * 25
            loss_modifier = record['loss'] * 25
            record['rating'] = baseline_rating + win_modifier - loss_modifier

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

        scoreboard = self.db.search(self.user.name.exists())

        if not scoreboard:
            raise OneHeadException("No users found in database.")

        self._calculate_win_percentage(scoreboard)
        self._calculate_rating(scoreboard)
        sorted_scoreboard = self._calculate_positions(scoreboard, "rating")
        sorted_scoreboard = self._sort_scoreboard_key_order(sorted_scoreboard)
        sorted_scoreboard = tabulate(sorted_scoreboard, headers="keys", tablefmt="simple")

        return sorted_scoreboard

