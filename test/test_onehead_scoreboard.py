from unittest import TestCase
from mock import MagicMock
from onehead_scoreboard import OneHeadScoreBoard
from onehead_common import OneHeadException


class OneHeadScoreBoardTest(TestCase):

    def setUp(self):
        self.database = MagicMock()
        self.scoreboard = OneHeadScoreBoard(self.database)

    def test_calculate_win_percentage_loss_0(self):
        scoreboard = [{"name": "RBEEZAY", "win": 10, "loss": 0}]
        self.scoreboard._calculate_win_percentage(scoreboard)
        self.assertEqual(scoreboard[0]["%"], 100)

    def test_calculate_win_percentage_win_0(self):
        scoreboard = [{"name": "RBEEZAY", "win": 0, "loss": 10}]
        self.scoreboard._calculate_win_percentage(scoreboard)
        self.assertEqual(scoreboard[0]["%"], 0)

    def test_calculate_win_percentage_int_result(self):
        scoreboard = [{"name": "RBEEZAY", "win": 5, "loss": 5}]
        self.scoreboard._calculate_win_percentage(scoreboard)
        self.assertEqual(scoreboard[0]["%"], 50)

    def test_calculate_win_loss_ratio_float_result(self):
        scoreboard = [{"name": "RBEEZAY", "win": 10, "loss": 5}]
        self.scoreboard._calculate_win_percentage(scoreboard)
        self.assertEqual(scoreboard[0]["%"], 66.7)

    def test_sort_scoreboard_key_order(self):
        scoreboard = [{"%": 71.4, "win": 10, "name": "RBEEZAY", "loss": 4, "#": 1, "rating": 1650}]
        result = self.scoreboard._sort_scoreboard_key_order(scoreboard)
        self.assertEqual(list(result[0].keys()), ["#", "name", "win", "loss", "%", "rating"])

    def test_calculate_rating_gain(self):
        scoreboard = [{"name": "RBEEZAY", "win": 10, "loss": 5}]
        self.scoreboard._calculate_rating(scoreboard)
        self.assertEqual(scoreboard[0]["rating"], 1625)

    def test_calculate_rating_loss(self):
        scoreboard = [{"name": "RBEEZAY", "win": 5, "loss": 10}]
        self.scoreboard._calculate_rating(scoreboard)
        self.assertEqual(scoreboard[0]["rating"], 1375)

    def test_calculate_positions_single_tie(self):
        scoreboard = [{"name": "RBEEZAY", "win": 10, "loss": 0, "%": 100, "rating": 1750},
                      {"name": "GPP", "win": 10, "loss": 0, "%": 100, "rating": 1750},
                      {"name": "LOZZA", "win": 10, "loss": 0, "%": 100, "rating": 1750},
                      {"name": "JEFFERIES", "win": 9, "loss": 0, "%": 100, "rating": 1725},
                      {"name": "JAMES", "win": 8, "loss": 0, "%": 100, "rating": 1700}]

        result = self.scoreboard._calculate_positions(scoreboard, "rating")
        self.assertEqual(result, [{'name': 'RBEEZAY', 'win': 10, 'loss': 0, "%": 100, "rating": 1750, '#': 1},
                                  {'name': 'GPP', 'win': 10, 'loss': 0, "%": 100, "rating": 1750, '#': 1},
                                  {'name': 'LOZZA', 'win': 10, 'loss': 0, "%": 100, "rating": 1750, '#': 1},
                                  {'name': 'JEFFERIES', 'win': 9, 'loss': 0, "%": 100, "rating": 1725, '#': 4},
                                  {'name': 'JAMES', 'win': 8, 'loss': 0, "%": 100, "rating": 1700, '#': 5}])

    def test_calculate_positions_double_tie(self):
        scoreboard = [{"name": "RBEEZAY", "win": 10, "loss": 0, "%": 100, "rating": 1750},
                      {"name": "GPP", "win": 10, "loss": 0, "%": 100, "rating": 1750},
                      {"name": "LOZZA", "win": 10, "loss": 0, "%": 100, "rating": 1750},
                      {"name": "JEFFERIES", "win": 9, "loss": 0, "%": 100, "rating": 1725},
                      {"name": "JAMES", "win": 9, "loss": 0, "%": 100, "rating": 1725},
                      {"name": "PECRO", "win": 8, "loss": 0, "%": 100, "rating": 1700}]

        result = self.scoreboard._calculate_positions(scoreboard, "rating")
        self.assertEqual(result, [{'name': 'RBEEZAY', 'win': 10, 'loss': 0, "%": 100, "rating": 1750, '#': 1},
                                  {'name': 'GPP', 'win': 10, 'loss': 0, "%": 100, "rating": 1750, '#': 1},
                                  {'name': 'LOZZA', 'win': 10, 'loss': 0, "%": 100, "rating": 1750, '#': 1},
                                  {'name': 'JEFFERIES', 'win': 9, 'loss': 0, "%": 100, "rating": 1725, '#': 4},
                                  {'name': 'JAMES', 'win': 9, 'loss': 0, "%": 100, "rating": 1725, '#': 4},
                                  {"name": "PECRO", "win": 8, "loss": 0, "%": 100, "rating": 1700, '#': 6}])

    def test_calculate_positions_no_tie(self):
        scoreboard = [{"name": "RBEEZAY", "win": 10, "loss": 0, "%": 100, "rating": 1750},
                      {"name": "GPP", "win": 9, "loss": 1, "%": 90, "rating": 1700},
                      {"name": "LOZZA", "win": 8, "loss": 2, "%": 80, "rating": 1650},
                      {"name": "JEFFERIES", "win": 7, "loss": 3, "%": 70, "rating": 1600},
                      {"name": "JAMES", "win": 6, "loss": 4, "%": 60, "rating": 1550}]

        result = self.scoreboard._calculate_positions(scoreboard, "rating")
        self.assertEqual(result, [{"name": "RBEEZAY", "win": 10, "loss": 0, "%": 100, "rating": 1750, "#": 1},
                                  {"name": "GPP", "win": 9, "loss": 1, "%": 90, "rating": 1700, "#": 2},
                                  {"name": "LOZZA", "win": 8, "loss": 2, "%": 80, "rating": 1650, "#": 3},
                                  {"name": "JEFFERIES", "win": 7, "loss": 3, "%": 70, "rating": 1600, "#": 4},
                                  {"name": "JAMES", "win": 6, "loss": 4, "%": 60, "rating": 1550, "#": 5}])

    def test_get_scoreboard_db_empty(self):
        self.database.retrieve_table.return_value = []
        self.assertRaises(OneHeadException, self.scoreboard.get_scoreboard)
