from unittest import TestCase
from mock import MagicMock, patch
from onehead_balance import OneHeadBalance
from onehead_db import OneHeadDB
from onehead_user import OneHeadPreGame
from onehead_common import OneHeadException


@patch("onehead_balance.combinations")
class OneHeadBalanceTest(TestCase):

    def setUp(self):
        self.pre_game = MagicMock(spec=OneHeadPreGame)
        self.pre_game.signups = ['RBEEZAY', 'GPP', 'LOZZA', 'JEFFERIES', 'JAMES', 'PECRO', 'ZEE', 'JOSH', 'EDD',
                                 'ARRECOOLAST']

        self.mock_db = [{"name": "RBEEZAY", "win": 10, "loss": 0, "ratio": 10, "mmr": 5000},
                        {"name": "GPP", "win": 10, "loss": 0, "ratio": 10, "mmr": 2000},
                        {"name": "LOZZA", "win": 10, "loss": 0, "ratio": 10, "mmr": 5000},
                        {"name": "JEFFERIES", "win": 10, "loss": 0, "ratio": 10, "mmr": 2000},
                        {"name": "JAMES", "win": 10, "loss": 0, "ratio": 10, "mmr": 2000},
                        {"name": "PECRO", "win": 0, "loss": 10, "ratio": 0, "mmr": 2500},
                        {"name": "ZEE", "win": 10, "loss": 0, "ratio": 10, "mmr": 3500},
                        {"name": "JOSH", "win": 10, "loss": 0, "ratio": 10, "mmr": 3500},
                        {"name": "EDD", "win": 10, "loss": 0, "ratio": 10, "mmr": 4000},
                        {"name": "ARRECOOLAST", "win": 10, "loss": 0, "ratio": 10, "mmr": 3500}]

        self.database = MagicMock(spec=OneHeadDB)
        self.t1 = None
        self.t2 = None
        self.team_balance = OneHeadBalance(self.database, self.pre_game, self.t1, self.t2)

    def mock_lookup_player(self, *args):
        return [x for x in self.mock_db if x['name'] == args[0]]

    def test_calculate_balance_success(self, mock_combinations):
        self.database.lookup_player.side_effect = self.mock_lookup_player
        mock_combination = [self.mock_db[:5], self.mock_db[5:]]
        mock_combinations.side_effect = [MagicMock(), [mock_combination]]
        result = self.team_balance.calculate_balance()
        self.assertEqual(result[0], [{'name': 'RBEEZAY', 'win': 10, 'loss': 0, 'ratio': 10, 'mmr': 5000},
                                     {'name': 'GPP', 'win': 10, 'loss': 0, 'ratio': 10, 'mmr': 2000},
                                     {'name': 'LOZZA', 'win': 10, 'loss': 0, 'ratio': 10, 'mmr': 5000},
                                     {'name': 'JEFFERIES', 'win': 10, 'loss': 0, 'ratio': 10, 'mmr': 2000},
                                     {'name': 'JAMES', 'win': 10, 'loss': 0, 'ratio': 10, 'mmr': 2000}])

    def test_calculate_balance_non_unique(self, mock_combinations):
        self.database.lookup_player.side_effect = self.mock_lookup_player
        mock_combination = [self.mock_db[:5], self.mock_db[5:]]
        mock_combination[0][0] = mock_combination[1][0]
        mock_combinations.side_effect = [MagicMock(), [mock_combination]]
        self.assertRaises(OneHeadException, self.team_balance.calculate_balance)

    def test_calculate_balance_incorrect_profile_count(self, mock_combinations):
        self.database.lookup_player.return_value = []
        mock_combination = [self.mock_db[:5], self.mock_db[5:]]
        mock_combination[0][0] = mock_combination[1][0]
        mock_combinations.side_effect = [MagicMock(), [mock_combination]]
        self.assertRaises(OneHeadException, self.team_balance.calculate_balance)
