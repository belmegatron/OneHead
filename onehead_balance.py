from itertools import combinations
from random import choice
from onehead_common import OneHeadException


class OneHeadBalance(object):

    def __init__(self, database, pregame):

        self.database = database
        self.pre_game = pregame
        self.signups = []

    def _calculate_balance(self):

        profiles = []
        for player in self.signups:
            profile = self.database.lookup_player(player)
            if profile:
                profiles.append(profile)

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
            t1_rating = sum([player["mmr"] for player in t1])
            t2_rating = sum([player["mmr"] for player in t2])
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

        balanced_teams = self._calculate_balance()

        return balanced_teams
