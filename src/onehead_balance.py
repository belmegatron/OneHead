from itertools import combinations
from random import choice
from discord.ext import commands
from tabulate import tabulate
from asyncio import sleep, wait_for, TimeoutError
import asyncio
import random
from src.onehead_common import OneHeadException
from src.onehead_stats import OneHeadStats


class OneHeadBalance(object):

    def __init__(self, database, pregame, config):

        self.database = database
        self.pre_game = pregame
        self.signups = []
        self.is_adjusted = config["rating"]["is_adjusted"]

    def _get_profiles(self):
        """
        Obtains player profiles for all player names contained within self.signups.

        :return: A list of dicts, each dict corresponds to a player profile.
        """

        profiles = []
        for player in self.signups:
            profile = self.database.lookup_player(player)
            if profile:
                profiles.append(profile)

        return profiles

    @staticmethod
    def _calculate_unique_team_combinations(all_matchups):
        """
        Calculates all 5v5 combinations, where the players on each team are unique to that particular team.

        :param all_matchups: All possible 5v5 combinations, including combinations with the same player on each team.
        :type all_matchups: List of tuples, each tuple contains 2 tuples corresponding to each 5 man lineup.
                            Each tuple contains 5 dicts where each dict contains player data, e.g. name, mmr, win, etc.
        :return: List of tuples, each tuple containing 2 tuples corresponding to each unique 5 man lineup.
                 Each tuple contains 5 unique dicts. These dicts are unique to this team and cannot be present in the
                 other team.
        """

        unique_combinations = []

        for matchup in all_matchups:
            matchup_1, matchup_2 = matchup
            shared_players = False
            for player in matchup_1:
                if player in matchup_2:
                    shared_players = True
                    break
            if shared_players is False:
                unique_combinations.append(matchup)

        return unique_combinations

    @staticmethod
    def _calculate_rating_differences(all_unique_combinations, rating_field):
        """
        Calculates the net rating difference for each unique combination of teams based on a particular rating field.

        :param all_unique_combinations: All 5v5 unique combinations.
        :type all_unique_combinations: List of tuples, each tuple contains 2 tuples, each tuple contains 5 dicts.
        :param rating_field: Specifies which field in the player profile to use for calculating net rating difference.
        :type rating_field: str
        :return: List of int's
        """

        rating_differences = []

        for unique_combination in all_unique_combinations:
            t1, t2 = unique_combination
            t1_rating = sum([player[rating_field] for player in t1])
            t2_rating = sum([player[rating_field] for player in t2])
            rating_difference = abs(t1_rating - t2_rating)
            rating_differences.append(rating_difference)

        return rating_differences

    def _calculate_balance(self, adjusted=False):
        """
        Returns a matchup of two, five-man teams that are evenly(or as close to evenly) matched based on
        a rating value associated with each player.

        :param adjusted: Species whether to use the 'adjusted_mmr' field to balance or just the 'mmr' field.
        :type adjusted: bool
        :return: A tuple of 2 tuples, each tuple contains 5 dicts corresponding to each player profile.
        """

        profiles = self._get_profiles()
        if len(profiles) != 10:
            raise OneHeadException("Error: Only {} profiles could be found in database.".format(len(profiles)))

        if adjusted is False:
            mmr_field_name = "mmr"
        else:
            mmr_field_name = "adjusted_mmr"
            OneHeadStats.calculate_rating(profiles)
            OneHeadStats.calculate_adjusted_mmr(profiles)

        all_5_man_lineups = list(combinations(profiles, 5))  # Calculate all possible 5 man lineups.
        all_5v5_matchups = list(combinations(all_5_man_lineups, 2))  # Calculate all possible 5v5 matchups.

        unique_combinations = self._calculate_unique_team_combinations(
            all_5v5_matchups)  # Calculate all valid 5v5 matchups where players are unique to either Team 1 or Team 2.

        if not unique_combinations:
            raise OneHeadException("Error: No valid matchups could be calculated. Possible Duplicate Player Name.")

        rating_differences = self._calculate_rating_differences(unique_combinations,
                                                                mmr_field_name)  # Calculate the net rating difference between each 5v5 matchup.

        rating_differences_mapping = dict(
            enumerate(rating_differences, start=0))  # Map the net rating differences to a key.
        rating_differences_mapping = {k: v for k, v in
                                      sorted(rating_differences_mapping.items(), key=lambda item: item[
                                          1])}  # Sort by ascending net rating difference.

        indices = list(rating_differences_mapping.keys())[
                  :10]  # Obtain the indices for the top 10 closest net rating matchups.
        balanced_teams = unique_combinations[
            choice(indices)]  # Pick a random matchup from the top 10 closest net rating matchups.

        return balanced_teams

    async def balance(self, ctx):
        """
        Returns two balanced 5 man teams from 10 players in the signup pool.

        :param ctx: Discord context.
        :return: A tuple of 2 tuples, each tuple corresponds to a unique 5 man team and contains 5 dicts corresponding
                 to each player's profile.
        """

        self.signups = self.pre_game.signups
        signup_count = len(self.signups)
        await ctx.send("Balancing teams...")
        if signup_count != 10:
            err = "Only {} Signups, require {} more.".format(signup_count, 10 - signup_count)
            await ctx.send(err)
            raise OneHeadException(err)

        balanced_teams = self._calculate_balance(adjusted=self.is_adjusted)

        return balanced_teams


class OneHeadCaptainsMode(commands.Cog):

    def __init__(self, database, pregame):

        self.database = database
        self.pre_game = pregame

        self.signups = []
        self.remaining_players = []
        self.votes = {}
        self.has_voted = {}

        self.captain_1 = None
        self.captain_2 = None
        self.team_1 = []
        self.team_2 = []

        self.nomination_phase_in_progress = False
        self.pick_phase_in_progress = False
        self.captain_1_turn = False
        self.captain_2_turn = False

        self.event_loop = asyncio.get_event_loop()
        self.future = None

    def calculate_top_nominations(self):
        """
        Calculates which two players had the most nominations. If there is a two-way tie for the player
        with the most votes, then these two players will both be selected as captains. If there is a
        three-way tie or greater, then a captain will be randomly selected from the tied players.

        :return: The names of the two captains.
        :type: tuple of str
        """

        sorted_votes = sorted(set(self.votes.values()), reverse=True)

        most_voted = {k: v for k, v in self.votes.items() if v == sorted_votes[0]}
        second_most_voted = {k: v for k, v in self.votes.items() if v == sorted_votes[1]}

        captain_1 = None
        captain_2 = None

        names = list(most_voted.keys())
        if len(most_voted) == 1:
            captain_1, = names
        elif len(most_voted) == 2:
            captain_1, captain_2 = names
        else:
            while not captain_1:
                idx = names.index(random.choice(names))
                captain_1 = names.pop(idx)
            while not captain_2:
                idx = names.index(random.choice(names))
                captain_2 = names.pop(idx)

        if not captain_2:
            names = list(second_most_voted.keys())
            if len(second_most_voted) == 1:
                captain_2, = names
            else:
                captain_2 = random.choice(names)

        return captain_1, captain_2

    async def nomination_phase(self, ctx):
        """
        Initiates the nomination phase and allows the '!vote' command to be used by players who have been
        selected to play in the game. This phase lasts for approximately 30 seconds, after which the
        '!vote' command can no longer be used.

        :param ctx: Discord context.
        """

        self.nomination_phase_in_progress = True
        self.signups = self.pre_game.signups
        self.votes = {x: 0 for x in self.signups}
        self.has_voted = {x: False for x in self.signups}
        await ctx.send("You have 30 seconds to nominate a captain. Type !nom <name> to nominate a captain.")
        await sleep(30)
        self.nomination_phase_in_progress = False
        self.captain_1, self.captain_2 = self.calculate_top_nominations()
        nominations = [(k, v) for k, v in self.votes.items()]
        nominations = tabulate(nominations, headers=["Name", "Votes"], tablefmt="simple")
        await ctx.send("```{}```".format(nominations))
        await ctx.send(
            "The nominations are in! Your selected captains are {} and {}.".format(self.captain_1, self.captain_2))

    async def picking_phase(self, ctx):
        """
        Initiates the picking phase where Captains can select which players they want to join their team
        using the '!pick' command. Each Captain has 30 seconds to select a player, if they fail to do this,
        a player will be randomly chosen for them.

        :param ctx: Discord context.
        :return: The teams selected by each Captain.
        :type: tuple of lists, each list contains 5 dicts corresponding to each player profile.
        """

        self.remaining_players = self.signups.copy()

        if not self.captain_1 or not self.captain_2:
            raise OneHeadException("Captains have not been selected.")

        for captain in (self.captain_1, self.captain_2):
            idx = self.remaining_players.index(captain)
            player = self.remaining_players.pop(idx)
            if captain == self.captain_1:
                self.team_1.append(player)
            else:
                self.team_2.append(player)

        self.pick_phase_in_progress = True
        await ctx.send("You have 30 seconds to pick a player each turn.")

        captain_round_order = (
            self.captain_1,
            self.captain_2, self.captain_2,
            self.captain_1, self.captain_1,
            self.captain_2, self.captain_2,
            self.captain_1
        )

        while self.remaining_players:
            for round_number, captain in enumerate(captain_round_order):
                if captain == self.captain_1:
                    self.captain_1_turn = True
                    self.captain_2_turn = False
                else:
                    self.captain_2_turn = True
                    self.captain_1_turn = False
                await ctx.send("{}'s turn to pick.".format(captain))
                await ctx.send("**Remaining Player Pool** : ```{}```".format(self.remaining_players))
                self.future = self.event_loop.create_future()

                if round_number == 7:
                    last_player = self.remaining_players.pop(0)
                    self.team_1.append(last_player)
                    await ctx.send(
                        "{} has been automatically added to Team 2 as {} was the last remaining player.".format(
                            last_player, last_player))
                else:
                    try:
                        await wait_for(self.future, timeout=30)
                    except TimeoutError:
                        idx = self.remaining_players.index(random.choice(self.remaining_players))
                        pick = self.remaining_players.pop(idx)
                        if captain == self.captain_1:
                            self.team_1.append(pick)
                        else:
                            self.team_2.append(pick)
                        await ctx.send("{} has randomed {} to join their team.".format(captain, pick))

        self.pick_phase_in_progress = False
        self.captain_1_turn = False
        self.captain_2_turn = False

        t1 = []
        t2 = []

        for team in (self.team_1, self.team_2):
            for player in team:
                profile = self.database.lookup_player(player)
                if team == self.team_1:
                    t1.append(profile)
                else:
                    t2.append(profile)

        return t1, t2

    @commands.has_role("IHL")
    @commands.command(aliases=['nom'])
    async def nominate(self, ctx, nomination):
        """
        Nominate a player to become captain. This command can only be used during the nomination phase of a captain's mode game.
        """

        name = ctx.author.display_name
        nomination = nomination.upper()

        if self.nomination_phase_in_progress is False:
            await ctx.send("Nominations are closed.")
            return

        if name not in self.signups:
            await ctx.send("{} is not currently signed up and therefore cannot nominate.".format(name))
            return

        if self.has_voted[name] is False:
            if nomination != name:
                record = self.votes.get(nomination, None)
                if record is not None:
                    self.votes[nomination] += 1
                    self.has_voted[name] = True
                    await ctx.send("{} has nominated {} to be captain.".format(name, nomination))
                else:
                    await ctx.send(
                        "{} is not currently signed up and therefore cannot be nominated.".format(nomination))
            else:
                await ctx.send("{}, you cannot vote for yourself.".format(name))
        else:
            await ctx.send("{} has already voted.".format(name))

    async def add_pick(self, ctx, pick, team):

        if pick in self.remaining_players:
            idx = self.remaining_players.index(pick)
            player = self.remaining_players.pop(idx)
            team.append(player)
            self.future.set_result(True)
            return True
        else:
            await ctx.send("{} is not in the remaining player pool.".format(pick))
            return False

    @commands.has_role("IHL")
    @commands.command(aliases=['p'])
    async def pick(self, ctx, pick):
        """
        This command allows a captain to select a player to join their team during the pick phase of a captain's mode game.
        """

        name = ctx.author.display_name
        pick = pick.upper()

        if self.pick_phase_in_progress is False:
            await ctx.send("Pick phase is not currently in progress.")
            return

        if name == self.captain_1:
            if self.captain_1_turn:
                if await self.add_pick(ctx, pick, self.team_1):
                    await ctx.send("{} has selected {} to join Team 1.".format(name, pick))
            else:
                await ctx.send("It is currently {}'s turn to pick.".format(self.captain_2))
        elif name == self.captain_2:
            if self.captain_2_turn:
                if await self.add_pick(ctx, pick, self.team_2):
                    await ctx.send("{} has selected {} to join Team 2.".format(name, pick))
            else:
                await ctx.send("It is currently {}'s turn to pick.".format(self.captain_1))
        else:
            await ctx.send("{} is not a captain and therefore cannot pick.".format(name))
