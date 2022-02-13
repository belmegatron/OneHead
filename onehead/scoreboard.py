from discord.ext import commands
from tabulate import tabulate

from onehead.common import OneHeadException
from onehead.stats import OneHeadStats


class OneHeadScoreBoard(commands.Cog):
    def __init__(self, database):

        self.db = database

    @commands.has_role("IHL")
    @commands.command(aliases=["sb"])
    async def scoreboard(self, ctx: commands.Context):
        """
        Shows the current rankings for the IGC IHL Leaderboard.
        """

        scoreboard = self._get_scoreboard()
        await ctx.send(f"**IGC Leaderboard** ```\n{scoreboard}```")

    @staticmethod
    def _sort_scoreboard_key_order(scoreboard: list[dict]) -> list[dict]:
        """
        Sets the column order for the scoreboard by ordering the keys for each row.

        :param scoreboard: Unsorted scoreboard
        :return: Sorted scoreboard
        """

        key_order = ["#", "name", "win", "loss", "%", "rating"]
        sorted_scoreboard = []

        for record in scoreboard:
            record = {k: record[k] for k in key_order}
            sorted_scoreboard.append(record)

        return sorted_scoreboard

    @staticmethod
    def _calculate_positions(scoreboard: list[dict], sort_key: str) -> list[dict]:
        """
        Calculates the position for each player on the scoreboard based on a particular sort key.

        :param scoreboard: Scoreboard containing all IHL players.
        :param sort_key: The key by which to sort the scoreboard.
        :return: Scoreboard sorted in descending order with additional '#' field.
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

    def _get_scoreboard(self) -> str:
        """
        Returns current scoreboard for the IHL.

        :return: Scoreboard string to be displayed in Discord chat.
        """

        scoreboard = self.db.retrieve_table()

        if not scoreboard:
            raise OneHeadException("No users found in database.")

        OneHeadStats.calculate_win_percentage(scoreboard)
        OneHeadStats.calculate_rating(scoreboard)

        scoreboard_sorted_rows = self._calculate_positions(scoreboard, "rating")
        scoreboard_sorted_rows_and_columns = self._sort_scoreboard_key_order(scoreboard_sorted_rows)
        sorted_scoreboard = tabulate(
            scoreboard_sorted_rows_and_columns, headers="keys", tablefmt="simple"
        )

        return sorted_scoreboard
