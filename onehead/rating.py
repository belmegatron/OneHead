from onehead.common import Player


class Rating:
    BASELINE_RATING: int = 1500
    MMR_DELTA: int = 50

    @staticmethod
    def calculate_win_percentage(profiles: list[Player]) -> None:
        """
        Calculates the win percentage for each profile in profiles.

        :param profiles: List of player profiles.
        """
        for record in profiles:
            if record.win == 0:
                record.win_percentage = 0
            else:
                record.win_percentage = round(record.win / (record.win + record.loss) * 100, 1)

    @staticmethod
    def calculate_duel_win_percentage(profiles: list[Player]) -> None:
        for record in profiles:
            if record.duel_win == 0:
                record.duel_win_percentage = 0
            else:
                record.duel_win_percentage = round(record.duel_win / (record.duel_win + record.duel_loss) * 100, 1)

    @classmethod
    def calculate_rating(cls, profiles: list[Player]) -> None:
        """
        Calculates the IHL rating for each profile in profiles.

        :param profiles: List of player profiles.
        """
        for record in profiles:
            win_modifier: int = record.win * cls.MMR_DELTA
            loss_modifier: int = record.loss * cls.MMR_DELTA
            record.rating = cls.BASELINE_RATING + win_modifier - loss_modifier

    @classmethod
    def calculate_duel_rating(cls, profiles: list[Player]) -> None:
        """
        Calculates the IHL rating for each profile in profiles.

        :param profiles: List of player profiles.
        """
        for record in profiles:
            win_modifier: int = record.duel_win * cls.MMR_DELTA
            loss_modifier: int = record.duel_loss * cls.MMR_DELTA
            record.duel_rating = cls.BASELINE_RATING + win_modifier - loss_modifier

    @classmethod
    def calculate_adjusted_mmr(cls, profiles: list[Player]) -> None:
        """
        Calculates an adjusted mmr to aid balancing. It adds the difference between baseline rating and your IHL
        rating to your MMR that was added when the player registered.

        :param profiles: Scoreboard with added rating field.
        """
        for record in profiles:
            difference: int = record.rating - cls.BASELINE_RATING

            if record.name == "PECRO":
                record.adjusted_mmr = 2000
            elif record.name == "RUGOR":
                record.adjusted_mmr = 2000
            else:
                record.adjusted_mmr = record.mmr + difference
