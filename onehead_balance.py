from itertools import combinations
from random import choice
from discord.ext import commands
from tabulate import tabulate
from asyncio import sleep, wait_for, TimeoutError
import asyncio
import random
from onehead_common import OneHeadException
from onehead_stats import OneHeadStats


class OneHeadBalance(object):

    def __init__(self, database, pregame):

        self.database = database
        self.pre_game = pregame
        self.signups = []

    def _get_profiles(self):

        profiles = []
        for player in self.signups:
            profile = self.database.lookup_player(player)
            if profile:
                profiles.append(profile)

        return profiles

    def _calculate_balance(self, adjusted=False):

        profiles = self._get_profiles()

        if adjusted is False:
            mmr_field_name = "mmr"
        else:
            mmr_field_name = "adjusted_mmr"
            OneHeadStats.calculate_rating(profiles)
            OneHeadStats.calculate_adjusted_mmr(profiles)

        if len(profiles) != 10:
            raise OneHeadException("Error: Only {} profiles could be found in database.".format(len(profiles)))

        all_five_man_lineups = list(combinations(profiles, 5))
        all_matchups = list(combinations(all_five_man_lineups, 2))
        valid_combinations = []

        for matchup in all_matchups:
            matchup_1, matchup_2 = matchup
            shared_players = False
            for player in list(matchup_1):
                if player in list(matchup_2):
                    shared_players = True
                    break
            if shared_players is False:
                valid_combinations.append(matchup)

        if not valid_combinations:
            raise OneHeadException("Error: No valid matchups could be calculated. Possible Duplicate Player Name.")

        rating_differences = []
        for vc in valid_combinations:
            t1, t2 = vc
            t1_rating = sum([player[mmr_field_name] for player in t1])
            t2_rating = sum([player[mmr_field_name] for player in t2])
            rating_difference = abs(t1_rating - t2_rating)
            rating_differences.append(rating_difference)

        rating_differences_mapping = dict(enumerate(rating_differences, start=0))
        rating_differences_mapping = {k: v for k, v in
                                      sorted(rating_differences_mapping.items(), key=lambda item: item[1])}

        indices = list(rating_differences_mapping.keys())[:10]
        balanced_teams = valid_combinations[choice(indices)]

        return balanced_teams

    async def balance(self, ctx):

        self.signups = self.pre_game.signups
        signup_count = len(self.signups)
        await ctx.send("Balancing teams...")
        if len(self.signups) != 10:
            err = "Only {} Signups, require {} more.".format(signup_count, 10 - signup_count)
            await ctx.send(err)
            raise OneHeadException(err)

        balanced_teams = self._calculate_balance(adjusted=True)

        return balanced_teams


class OneHeadCaptainsMode(commands.Cog):

    def __init__(self, database, pregame):

        self.database = database
        self.pre_game = pregame

        self.signups = []
        self.pool = []
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

    def reset_state(self):

        self.signups = []
        self.pool = []
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

        self.future = None

    def calculate_top_nominations(self):

        sorted_votes = sorted(set(self.votes.values()), reverse=True)

        most_voted = {k: v for k, v in self.votes.items() if v == sorted_votes[0]}
        second_most_voted = {k: v for k, v in self.votes.items() if v == sorted_votes[1]}

        captain_1 = None
        captain_2 = None

        if not captain_1:
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

        self.pool = self.signups.copy()

        if not self.captain_1 or not self.captain_2:
            raise OneHeadException("Captains have not been selected.")

        for captain in (self.captain_1, self.captain_2):
            idx = self.pool.index(captain)
            player = self.pool.pop(idx)
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

        while self.pool:
            for round_number, captain in enumerate(captain_round_order):
                if captain == self.captain_1:
                    self.captain_1_turn = True
                    self.captain_2_turn = False
                else:
                    self.captain_2_turn = True
                    self.captain_1_turn = False
                await ctx.send("{}'s turn to pick.".format(captain))
                await ctx.send("**Remaining Player Pool** : ```{}```".format(self.pool))
                self.future = self.event_loop.create_future()

                if round_number == 7:
                    last_player = self.pool.pop(0)
                    self.team_1.append(last_player)
                    await ctx.send(
                        "{} has been automatically added to Team 2 as {} was the last remaining player.".format(
                            last_player, last_player))
                else:
                    try:
                        await wait_for(self.future, timeout=30)
                    except TimeoutError:
                        idx = self.pool.index(random.choice(self.pool))
                        pick = self.pool.pop(idx)
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

        if pick in self.pool:
            idx = self.pool.index(pick)
            player = self.pool.pop(idx)
            team.append(player)
            self.future.set_result(True)
            return True
        else:
            await ctx.send("{} is not in the remaining player pool.".format(pick))
            return False

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
