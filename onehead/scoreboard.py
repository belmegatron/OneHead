from typing import Any, Literal

from discord.ext import commands
from tabulate import tabulate

from onehead.common import OneHeadException, OneHeadRoles, Player
from onehead.db import OneHeadDB
from onehead.stats import OneHeadStats


class OneHeadScoreBoard(commands.Cog):
    # It's actually 2000, but we prepend a small number of characters before our scoreboard so need to take
    # this into account.
    DISCORD_MAX_MESSAGE_LENGTH: Literal[1950] = 1950

    def __init__(self, database: OneHeadDB) -> None:

        self.db: OneHeadDB = database

    def _chunk_scoreboard(self, scoreboard: str) -> tuple[str, ...]:

        if len(scoreboard) < self.DISCORD_MAX_MESSAGE_LENGTH:
            return tuple([scoreboard])

        offset: int = 0
        chunks: list[str] = []

        while offset < len(scoreboard):
            remaining_size: int = len(scoreboard) - offset
            if remaining_size <= self.DISCORD_MAX_MESSAGE_LENGTH:
                chunk: str = scoreboard[offset:]
            else:
                max_chunk: str = scoreboard[
                    offset : offset + self.DISCORD_MAX_MESSAGE_LENGTH
                ]
                eol: int = max_chunk.rfind("\n")
                chunk = max_chunk[:eol]

            chunks.append(chunk)
            offset += len(chunk)

        return tuple(chunks)

    @commands.has_role(OneHeadRoles.MEMBER)
    @commands.command(aliases=["sb"])
    async def scoreboard(self, ctx: commands.Context) -> None:
        """
        Shows the current rankings for the IGC IHL Leaderboard.
        """

        scoreboard: str = self._get_scoreboard()
        chunked_scoreboard: tuple[str, ...] = self._chunk_scoreboard(scoreboard)

        for chunk in chunked_scoreboard:
            await ctx.send(f"**IGC Leaderboard** ```\n{chunk}```")

    @staticmethod
    def _sort_scoreboard_key_order(scoreboard: list[dict]) -> list[dict]:
        """
        Sets the column order for the scoreboard by ordering the keys for each row.

        :param scoreboard: Unsorted scoreboard
        :return: Sorted scoreboard
        """

        key_order: list[str] = [
            "#",
            "name",
            "win",
            "loss",
            "win_percentage",
            "rating",
            "win_streak",
            "loss_streak",
        ]
        sorted_scoreboard: list[dict[str, Any]] = []

        for record in scoreboard:
            record = {k: record[k] for k in key_order}
            sorted_scoreboard.append(record)

        return sorted_scoreboard

    @staticmethod
    def _calculate_positions(scoreboard: list[Player], sort_key: str) -> list[Player]:
        """
        Calculates the position for each player on the scoreboard based on a particular sort key.

        :param scoreboard: Scoreboard containing all IHL players.
        :param sort_key: The key by which to sort the scoreboard.
        :return: Scoreboard sorted in descending order with additional '#' field.
        """

        sorted_scoreboard: list[Player] = sorted(scoreboard, key=lambda k: k[sort_key], reverse=True)  # type: ignore
        scoreboard_positions: list[Player] = []

        pos: int = 1
        modifier: int = 1

        for i, record in enumerate(sorted_scoreboard):
            if i != 0:
                if sorted_scoreboard[i - 1][sort_key] > sorted_scoreboard[i][sort_key]:
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

        scoreboard: list[Player] = self.db.retrieve_table()

        if not scoreboard:
            raise OneHeadException("No users found in database.")

        OneHeadStats.calculate_win_percentage(scoreboard)
        OneHeadStats.calculate_rating(scoreboard)

        scoreboard_sorted_rows: list[Player] = self._calculate_positions(
            scoreboard, "rating"
        )
        scoreboard_sorted_rows_and_columns: list[
            Player
        ] = self._sort_scoreboard_key_order(scoreboard_sorted_rows)
        sorted_scoreboard: str = tabulate(
            scoreboard_sorted_rows_and_columns, headers="keys", tablefmt="simple"
        )

        return sorted_scoreboard
