from unittest import TestCase
from mock import MagicMock, patch
from onehead_scoreboard import OneHeadScoreBoard
from onehead_common import OneHeadException


class OneHeadScoreBoardTest(TestCase):

    def setUp(self):
        self.database = MagicMock()
        self.scoreboard = OneHeadScoreBoard(self.database)

    def test_calculate_win_loss_ratio_loss_0(self):
        scoreboard = [{"name": "RBEEZAY", "win": 10, "loss": 0}]
        self.scoreboard._calculate_win_percentage(scoreboard)
        self.assertEqual(scoreboard[0]["ratio"], 10)

    def test_calculate_win_loss_ratio_win_0(self):
        scoreboard = [{"name": "RBEEZAY", "win": 0, "loss": 10}]
        self.scoreboard._calculate_win_percentage(scoreboard)
        self.assertEqual(scoreboard[0]["ratio"], 0)

    def test_calculate_win_loss_ratio_int_result(self):
        scoreboard = [{"name": "RBEEZAY", "win": 10, "loss": 5}]
        self.scoreboard._calculate_win_percentage(scoreboard)
        self.assertEqual(scoreboard[0]["ratio"], 2)

    def test_calculate_win_loss_ratio_float_result(self):
        scoreboard = [{"name": "RBEEZAY", "win": 10, "loss": 4}]
        self.scoreboard._calculate_win_percentage(scoreboard)
        self.assertEqual(scoreboard[0]["ratio"], 2.5)

    def test_sort_scoreboard_key_order(self):
        scoreboard = [{"ratio": 0, "win": 10, "name": "RBEEZAY", "loss": 4, "#": 1}]
        result = self.scoreboard._sort_scoreboard_key_order(scoreboard)
        self.assertEqual(list(result[0].keys()), ["#", "name", "win", "loss", "ratio"])

    def test_calculate_positions_single_tie(self):
        scoreboard = [{"name": "RBEEZAY", "win": 10, "loss": 0, "ratio": 10},
                      {"name": "GPP", "win": 10, "loss": 0, "ratio": 10},
                      {"name": "LOZZA", "win": 10, "loss": 0, "ratio": 10},
                      {"name": "JEFFERIES", "win": 9, "loss": 0, "ratio": 9},
                      {"name": "JAMES", "win": 8, "loss": 0, "ratio": 8}]

        result = self.scoreboard._calculate_positions(scoreboard, "ratio")
        self.assertEqual(result, [{'name': 'RBEEZAY', 'win': 10, 'loss': 0, 'ratio': 10, '#': 1},
                                  {'name': 'GPP', 'win': 10, 'loss': 0, 'ratio': 10, '#': 1},
                                  {'name': 'LOZZA', 'win': 10, 'loss': 0, 'ratio': 10, '#': 1},
                                  {'name': 'JEFFERIES', 'win': 9, 'loss': 0, 'ratio': 9, '#': 4},
                                  {'name': 'JAMES', 'win': 8, 'loss': 0, 'ratio': 8, '#': 5}])

    def test_calculate_positions_double_tie(self):
        scoreboard = [{"name": "RBEEZAY", "win": 10, "loss": 0, "ratio": 10},
                      {"name": "GPP", "win": 10, "loss": 0, "ratio": 10},
                      {"name": "LOZZA", "win": 10, "loss": 0, "ratio": 10},
                      {"name": "JEFFERIES", "win": 9, "loss": 0, "ratio": 9},
                      {"name": "JAMES", "win": 9, "loss": 0, "ratio": 9},
                      {"name": "PECRO", "win": 2, "loss": 0, "ratio": 2}]

        result = self.scoreboard._calculate_positions(scoreboard, "ratio")
        self.assertEqual(result, [{'name': 'RBEEZAY', 'win': 10, 'loss': 0, 'ratio': 10, '#': 1},
                                  {'name': 'GPP', 'win': 10, 'loss': 0, 'ratio': 10, '#': 1},
                                  {'name': 'LOZZA', 'win': 10, 'loss': 0, 'ratio': 10, '#': 1},
                                  {'name': 'JEFFERIES', 'win': 9, 'loss': 0, 'ratio': 9, '#': 4},
                                  {'name': 'JAMES', 'win': 9, 'loss': 0, 'ratio': 9, '#': 4},
                                  {"name": "PECRO", "win": 2, "loss": 0, "ratio": 2, '#': 6}])

    def test_calculate_positions_no_tie(self):
        scoreboard = [{"name": "RBEEZAY", "win": 10, "loss": 0, "ratio": 10},
                      {"name": "GPP", "win": 9, "loss": 1, "ratio": 9},
                      {"name": "LOZZA", "win": 8, "loss": 2, "ratio": 8},
                      {"name": "JEFFERIES", "win": 7, "loss": 3, "ratio": 7},
                      {"name": "JAMES", "win": 6, "loss": 4, "ratio": 6}]

        result = self.scoreboard._calculate_positions(scoreboard, "ratio")
        self.assertEqual(result, [{"name": "RBEEZAY", "win": 10, "loss": 0, "ratio": 10, "#": 1},
                                  {"name": "GPP", "win": 9, "loss": 1, "ratio": 9, "#": 2},
                                  {"name": "LOZZA", "win": 8, "loss": 2, "ratio": 8, "#": 3},
                                  {"name": "JEFFERIES", "win": 7, "loss": 3, "ratio": 7, "#": 4},
                                  {"name": "JAMES", "win": 6, "loss": 4, "ratio": 6, "#": 5}])

    def test_get_scoreboard_db_empty(self):
        self.database.db.search.return_value = []
        self.assertRaises(OneHeadException, self.scoreboard.get_scoreboard)
