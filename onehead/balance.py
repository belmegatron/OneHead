import itertools
import random
from typing import TYPE_CHECKING

from discord.ext import commands
from tabulate import tabulate

from onehead.common import OneHeadException
from onehead.stats import OneHeadStats

if TYPE_CHECKING:
    from onehead.common import Player, Team, TeamCombination
    from onehead.db import OneHeadDB
    from onehead.user import OneHeadPreGame


class OneHeadBalance(commands.Cog):
    def __init__(self, database: "OneHeadDB", pre_game: "OneHeadPreGame"):

        self.database = database
        self.pre_game = pre_game

    def _get_profiles(self) -> list["Player"]:
        """
        Obtains player profiles for all players that have signed up to play.

        :return: Player profiles for all signed up players.
        """

        profiles = []
        for player in self.pre_game.signups:
            profile = self.database.lookup_player(player)
            if profile:
                profiles.append(profile)

        return profiles

    @staticmethod
    def _calculate_unique_team_combinations(
        all_matchups: list["TeamCombination"],
    ) -> list["TeamCombination"]:
        """
        Calculates all 5v5 combinations, where the players on each team are unique to that particular team.

        :param all_matchups: All possible 5v5 combinations, including combinations with the same player on each team.

        :return: Unique team combinations.
        """

        unique_combinations = []

        for matchup in all_matchups:
            shared_players = False
            for player in matchup[0]:
                if player in matchup[1]:
                    shared_players = True
                    break
            if shared_players is False:
                unique_combinations.append(matchup)

        return unique_combinations

    @staticmethod
    def _calculate_rating_differences(all_unique_combinations: list) -> None:
        """
        Calculates the net rating difference for each unique combination of teams based on their adjusted mmr.

        :param all_unique_combinations: All 5v5 unique combinations.
        """

        for unique_combination in all_unique_combinations:
            t1_rating = sum(
                [player["adjusted_mmr"] for player in unique_combination["t1"]]
            )
            t2_rating = sum(
                [player["adjusted_mmr"] for player in unique_combination["t2"]]
            )

            unique_combination["rating_difference"] = abs(t1_rating - t2_rating)

    def _calculate_balance(self) -> dict:
        """
        Calculate balanced lineups for Radiant/Dire.

        :return: Returns a matchup of two, five-man teams that are evenly (or as close to evenly) matched based on
        a rating value associated with each player.
        """

        profiles = self._get_profiles()
        profile_count = len(profiles)
        if profile_count != 10:
            raise OneHeadException(
                f"Error: Only {profile_count} profiles could be found in database."
            )

        OneHeadStats.calculate_rating(profiles)
        OneHeadStats.calculate_adjusted_mmr(profiles)

        team_combinations = list(
            itertools.combinations(profiles, 5)
        )  # type: list[Team]

        matchup_combinations = list(
            itertools.combinations(team_combinations, 2)
        )  # type: list[TeamCombination]

        unique_combinations = self._calculate_unique_team_combinations(
            matchup_combinations
        )  # type: list[TeamCombination]

        if not unique_combinations:
            raise OneHeadException(
                "No valid matchups could be calculated. Possible Duplicate Player Name."
            )

        unique_combinations_dict = [
            {"t1": combination[0], "t2": combination[1]}
            for combination in unique_combinations
        ]

        self._calculate_rating_differences(unique_combinations_dict)

        # Sort by ascending rating difference
        unique_combinations_dict = sorted(
            unique_combinations_dict, key=lambda d: d["rating_difference"]
        )  # type: ignore

        # Take the top 5 that are closest in terms of rating and pick one at random.
        balanced_teams = random.choice(unique_combinations_dict[:5])

        return balanced_teams

    async def balance(self, ctx: commands.Context) -> tuple["Team", "Team"]:
        """
        Returns two balanced 5-man teams from 10 players in the signup pool.

        :param ctx: Discord context.
        :return: Balanced teams.
        """

        signup_count = len(self.pre_game.signups)
        await ctx.send("Balancing teams...")
        if signup_count != 10:
            err = f"Only {signup_count} Signups, require {10 - signup_count} more."
            await ctx.send(err)

        balanced_teams = self._calculate_balance()

        return balanced_teams["t1"], balanced_teams["t2"]

    @commands.has_role("IHL")
    @commands.command(aliases=["mmr"])
    async def show_internal_mmr(self, ctx: commands.Context):
        """
        Shows the internal MMR used for balancing teams.
        """

        scoreboard = self.database.retrieve_table()
        OneHeadStats.calculate_rating(scoreboard)
        OneHeadStats.calculate_adjusted_mmr(scoreboard)

        ratings = [
            {
                "name": profile["name"],
                "base": profile["mmr"],
                "adjusted": profile["adjusted_mmr"],
            }
            for profile in scoreboard
        ]
        sorted_ratings = sorted(ratings, key=lambda k: k["adjusted"], reverse=True)  # type: ignore
        tabulated_ratings = tabulate(sorted_ratings, headers="keys", tablefmt="simple")
        await ctx.send(f"**Internal MMR** ```\n{tabulated_ratings}```")
