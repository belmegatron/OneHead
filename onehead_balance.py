from itertools import combinations
from random import choice
from onehead_common import OneHeadException


class OneHeadBalance(object):

    def __init__(self, database, pregame, t1, t2):

        self.database = database
        self.pre_game = pregame
        self.signups = self.pre_game.signups
        self.t1 = t1
        self.t2 = t2

        self.is_balanced = False

    def calculate_balance(self):

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
            share_players = False
            for player in list(matchup[0]):
                if player in list(matchup[1]):
                    share_players = True
                    break
            if share_players is False:
                valid_combinations.append(matchup)

        if not valid_combinations:
            raise OneHeadException("Error: No valid matchups could be calculated. Possible Duplicate Player Name.")

        rating_differences = []
        for vc in valid_combinations:
            t1_rating = sum([player["mmr"] for player in vc[0]])
            t2_rating = sum([player["mmr"] for player in vc[1]])
            rating_difference = abs(t1_rating - t2_rating)
            rating_differences.append(rating_difference)

        rating_differences_mapping = dict(enumerate(rating_differences, start=0))
        rating_differences_mapping = {k: v for k, v in
                                      sorted(rating_differences_mapping.items(), key=lambda item: item[1])}

        indices = list(rating_differences_mapping.keys())[:10]
        balanced_teams = valid_combinations[choice(indices)]

        return balanced_teams

    async def balance(self, ctx):

        signup_count = len(self.signups)
        await ctx.send("Balancing teams...")
        if len(self.signups) != 10:
            await ctx.send("Only {} Signups, require {} more.".format(signup_count, 10 - signup_count))

        balanced_teams = self.calculate_balance()
        self.t1 = balanced_teams[0]
        self.t2 = balanced_teams[1]
        self.is_balanced = True
