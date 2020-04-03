from unittest import TestCase
from mock import MagicMock, patch
from onehead_core import Database, OneHeadBalance


class DataBaseTest(TestCase):

    def setUp(self):
        self.scoreboard = [{"name": "RBEEZAY", "win": 10, "loss": 0, "ratio": 10},
                           {"name": "GPP", "win": 10, "loss": 0, "ratio": 10},
                           {"name": "LOZZA", "win": 10, "loss": 0, "ratio": 10},
                           {"name": "JEFFERIES", "win": 10, "loss": 0, "ratio": 10},
                           {"name": "JAMES", "win": 10, "loss": 0, "ratio": 10},
                           {"name": "PECRO", "win": 0, "loss": 10, "ratio": 0}]

    def test_calculate_positions_tie(self):
        foo = Database._calculate_positions(self.scoreboard, "ratio")


class TeamBalanceTest(TestCase):

    def setUp(self):
        self.signups = [{"name": "RBEEZAY", "win": 10, "loss": 0, "ratio": 10, "mmr": 5000},
                        {"name": "GPP", "win": 10, "loss": 0, "ratio": 10, "mmr": 2000},
                        {"name": "LOZZA", "win": 10, "loss": 0, "ratio": 10, "mmr": 5000},
                        {"name": "JEFFERIES", "win": 10, "loss": 0, "ratio": 10, "mmr": 2000},
                        {"name": "JAMES", "win": 10, "loss": 0, "ratio": 10, "mmr": 2000},
                        {"name": "PECRO", "win": 0, "loss": 10, "ratio": 0, "mmr": 2500},
                        {"name": "ZEE", "win": 10, "loss": 0, "ratio": 10, "mmr": 3500},
                        {"name": "JOSH", "win": 10, "loss": 0, "ratio": 10, "mmr": 3500},
                        {"name": "EDD", "win": 10, "loss": 0, "ratio": 10, "mmr": 4000},
                        {"name": "ARRECOOLAST", "win": 10, "loss": 0, "ratio": 10, "mmr": 3500}]

    def pass_arg_back(*args):
        return args[1]

    @patch("bot.Database.lookup_player")
    def test_balance(self, _):
        onehead = MagicMock()
        tb = OneHeadBalance(onehead)
        onehead.signups = self.signups
        onehead.database.db.lookup_player.side_effect = self.pass_arg_back
        tb.calculate_balance()
