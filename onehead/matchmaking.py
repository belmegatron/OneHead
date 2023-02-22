import itertools
import random
from logging import Logger
from typing import Any

from discord.ext.commands import Cog, Context, command, has_role
from tabulate import tabulate

from onehead.common import (
    OneHeadException,
    Player,
    Roles,
    Side,
    Team,
    TeamCombination,
    get_logger,
)
from onehead.database import Database
from onehead.lobby import Lobby
from onehead.statistics import Statistics

log: Logger = get_logger()


class Matchmaking(Cog):
    def __init__(self, database: Database, pre_game: Lobby) -> None:
        self.database: Database = database
        self.pre_game: Lobby = pre_game

    def _get_profiles(self) -> list[Player]:
        """
        Obtains player profiles for all players that have signed up to play.

        :return: Player profiles for all signed up players.
        """

        profiles: list[Player] = []
        for player in self.pre_game._signups:
            profile: Player = self.database.lookup_player(player)
            if profile:
                profiles.append(profile)

        return profiles

    @staticmethod
    def _calculate_unique_team_combinations(
        all_matchups: list[TeamCombination],
    ) -> list[TeamCombination]:
        """
        Calculates all 5v5 combinations, where the players on each team are unique to that particular team.

        :param all_matchups: All possible 5v5 combinations, including combinations with the same player on each team.

        :return: Unique team combinations.
        """

        unique_combinations: list[TeamCombination] = []

        for matchup in all_matchups:
            shared_players: bool = False
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
            t1_rating: int = sum(
                [player["adjusted_mmr"] for player in unique_combination[Side.RADIANT]]
            )
            t2_rating: int = sum(
                [player["adjusted_mmr"] for player in unique_combination[Side.DIRE]]
            )

            unique_combination["rating_difference"] = abs(t1_rating - t2_rating)

    def _calculate_balance(self) -> dict:
        """
        Calculate balanced lineups for Radiant/Dire.

        :return: Returns a matchup of two, five-man teams that are evenly (or as close to evenly) matched based on
        a rating value associated with each player.
        """

        profiles: list[Player] = self._get_profiles()
        profile_count: int = len(profiles)
        if profile_count != 10:
            raise OneHeadException(
                f"Error: Only {profile_count} profiles could be found in database."
            )

        Statistics.calculate_rating(profiles)
        Statistics.calculate_adjusted_mmr(profiles)

        team_combinations: list[Team] = list(itertools.combinations(profiles, 5))

        matchup_combinations: list[TeamCombination] = list(
            itertools.combinations(team_combinations, 2)
        )

        unique_combinations: list[
            TeamCombination
        ] = self._calculate_unique_team_combinations(matchup_combinations)

        if not unique_combinations:
            raise OneHeadException(
                "No valid matchups could be calculated. Possible Duplicate Player Name."
            )

        unique_combinations_dict: list[dict[str, Team]] = [
            {Side.RADIANT: combination[0], Side.DIRE: combination[1]}
            for combination in unique_combinations
        ]

        self._calculate_rating_differences(unique_combinations_dict)

        # Sort by ascending rating difference
        sorted_unique_combinations_dict: list[dict[str, Team]] = sorted(
            unique_combinations_dict, key=lambda d: d["rating_difference"]
        )

        # Take the top 5 that are closest in terms of rating and pick one at random.
        balanced_teams: dict[str, Team] = random.choice(
            sorted_unique_combinations_dict[:5]
        )

        return balanced_teams

    async def balance(self, ctx: Context) -> tuple[Team, Team]:
        """
        Returns two balanced 5-man teams from 10 players in the signup pool.

        :param ctx: Discord context.
        :return: Balanced teams.
        """

        signup_count: int = len(self.pre_game._signups)
        await ctx.send("Balancing teams...")
        if signup_count != 10:
            err: str = f"Only {signup_count} Signups, require {10 - signup_count} more."
            await ctx.send(err)

        balanced_teams: dict = self._calculate_balance()

        radiant: Team = balanced_teams[Side.RADIANT]
        dire: Team = balanced_teams[Side.DIRE]

        radiant_mmr: int = sum([x["adjusted_mmr"] for x in radiant])
        dire_mmr: int = sum([x["adjusted_mmr"] for x in dire])

        log.debug(f"Radiant MMR: {radiant_mmr}, Dire MMR: {dire_mmr}")

        return radiant, dire

    @has_role(Roles.MEMBER)
    @command()
    async def mmr(self, ctx: Context) -> None:
        """
        Shows the internal MMR used for balancing teams.
        """

        scoreboard: list[Player] = self.database.retrieve_table()
        Statistics.calculate_rating(scoreboard)
        Statistics.calculate_adjusted_mmr(scoreboard)

        ratings: list[dict[str, Any]] = [
            {
                "name": profile["name"],
                "base": profile["mmr"],
                "adjusted": profile["adjusted_mmr"],
            }
            for profile in scoreboard
        ]
        sorted_ratings: list[dict[str, Any]] = sorted(ratings, key=lambda k: k["adjusted"], reverse=True)  # type: ignore
        tabulated_ratings: str = tabulate(
            sorted_ratings, headers="keys", tablefmt="simple"
        )
        await ctx.send(f"**Internal MMR** ```\n{tabulated_ratings}```")
