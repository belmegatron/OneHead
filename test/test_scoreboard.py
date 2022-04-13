from unittest import TestCase
from unittest.mock import MagicMock

from onehead.common import OneHeadException
from onehead.scoreboard import OneHeadScoreBoard


class OneHeadScoreBoardTest(TestCase):

    def setUp(self):
        self.database = MagicMock()
        self.scoreboard = OneHeadScoreBoard(self.database)

    def test_sort_scoreboard_key_order(self):
        scoreboard = [{"%": 71.4, "win": 10, "name": "RBEEZAY", "loss": 4, "#": 1, "rating": 1650, "win streak": 0,
                       "loss streak": 0}]
        result = self.scoreboard._sort_scoreboard_key_order(scoreboard)
        self.assertEqual(list(result[0].keys()),
                         ["#", "name", "win", "loss", "%", "rating", "win streak", "loss streak"])

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
        self.assertRaises(OneHeadException, self.scoreboard._get_scoreboard)
