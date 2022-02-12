class OneHeadStats(object):

    BASELINE_RATING = 1500

    @staticmethod
    def calculate_win_percentage(profiles: list[dict]):
        """
        Calculates the win percentage for each profile in profiles.

        :param profiles: List of player profiles.
        """

        for record in profiles:
            if record["win"] == 0:
                record["%"] = 0
            else:
                record["%"] = round(
                    record["win"] / (record["win"] + record["loss"]) * 100, 1
                )

    @classmethod
    def calculate_rating(cls, profiles: list[dict]):
        """
        Calculates the IHL rating for each profile in profiles.

        :param profiles: List of player profiles.
        """

        for record in profiles:
            win_modifier = record["win"] * 25
            loss_modifier = record["loss"] * 25
            record["rating"] = cls.BASELINE_RATING + win_modifier - loss_modifier

    @classmethod
    def calculate_adjusted_mmr(cls, profiles: list[dict]):
        """
        Calculates an adjusted mmr to aid balancing. It adds the difference between baseline rating and your IHL
        rating to your MMR that was added when the player registered.

        :param profiles: Scoreboard with added rating field.
        """

        for record in profiles:
            rating = record["rating"]
            mmr = record["mmr"]
            difference = rating - cls.BASELINE_RATING
            hidden_mmr = mmr + difference
            record["adjusted_mmr"] = hidden_mmr
