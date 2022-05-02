class OneHeadStats:

    BASELINE_RATING = 1500
    MMR_DELTA = 50

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
            win_modifier = record["win"] * cls.MMR_DELTA
            loss_modifier = record["loss"] * cls.MMR_DELTA
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
            record["adjusted_mmr"] = mmr + difference
