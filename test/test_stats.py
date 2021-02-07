from unittest import TestCase

from onehead.stats import OneHeadStats


class OneHeadStatsTest(TestCase):

    def setUp(self):
        self.stats = OneHeadStats()

    def test_calculate_win_percentage_loss_0(self):
        scoreboard = [{"name": "RBEEZAY", "win": 10, "loss": 0}]
        self.stats.calculate_win_percentage(scoreboard)
        self.assertEqual(scoreboard[0]["%"], 100)

    def test_calculate_win_percentage_win_0(self):
        scoreboard = [{"name": "RBEEZAY", "win": 0, "loss": 10}]
        self.stats.calculate_win_percentage(scoreboard)
        self.assertEqual(scoreboard[0]["%"], 0)

    def test_calculate_win_percentage_int_result(self):
        scoreboard = [{"name": "RBEEZAY", "win": 5, "loss": 5}]
        self.stats.calculate_win_percentage(scoreboard)
        self.assertEqual(scoreboard[0]["%"], 50)

    def test_calculate_win_loss_ratio_float_result(self):
        scoreboard = [{"name": "RBEEZAY", "win": 10, "loss": 5}]
        self.stats.calculate_win_percentage(scoreboard)
        self.assertEqual(scoreboard[0]["%"], 66.7)

    def test_calculate_rating_gain(self):
        scoreboard = [{"name": "RBEEZAY", "win": 10, "loss": 5}]
        self.stats.calculate_rating(scoreboard)
        self.assertEqual(scoreboard[0]["rating"], 1625)

    def test_calculate_rating_loss(self):
        scoreboard = [{"name": "RBEEZAY", "win": 5, "loss": 10}]
        self.stats.calculate_rating(scoreboard)
        self.assertEqual(scoreboard[0]["rating"], 1375)

    def test_calculate_adjusted_mmr(self):
        scoreboard = [{"name": "RBEEZAY", "win": 5, "loss": 10, "rating": 1375, "mmr": 2000}]
        self.stats.calculate_adjusted_mmr(scoreboard)
        self.assertEqual(scoreboard[0]["adjusted_mmr"], 1875)
