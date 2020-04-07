from unittest import TestCase
import asyncio
from mock import MagicMock, patch
from onehead_balance import OneHeadBalance
from onehead_db import OneHeadDB
from onehead_user import OneHeadPreGame
from onehead_common import OneHeadException


class OneHeadAsyncTest(object):

    @staticmethod
    def _run(coro):
        """Run the given coroutine."""
        return asyncio.get_event_loop().run_until_complete(coro)

    @staticmethod
    def async_mock(*args, **kwargs):
        """Create an async function mock."""
        m = MagicMock(*args, **kwargs)

        async def mock_coro(*args, **kwargs):
            return m(*args, **kwargs)

        mock_coro.mock = m
        return mock_coro


class OneHeadBalanceTest(TestCase):

    def setUp(self):
        self.pre_game = MagicMock(spec=OneHeadPreGame)
        self.signups = ['RBEEZAY', 'GPP', 'LOZZA', 'JEFFERIES', 'JAMES', 'PECRO', 'ZEE', 'JOSH', 'EDD',
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
        self.team_balance = OneHeadBalance(self.database, self.pre_game)

    def mock_lookup_player(self, *args):
        return [x for x in self.mock_db if x['name'] == args[0]]

    @patch("onehead_balance.combinations")
    def test_calculate_balance_success(self, mock_combinations):
        self.team_balance.signups = self.signups
        self.database.lookup_player.side_effect = self.mock_lookup_player
        mock_combination = [self.mock_db[:5], self.mock_db[5:]]
        mock_combinations.side_effect = [MagicMock(), [mock_combination]]
        result = self.team_balance._calculate_balance()
        self.assertEqual(result[0], [{'name': 'RBEEZAY', 'win': 10, 'loss': 0, 'ratio': 10, 'mmr': 5000},
                                     {'name': 'GPP', 'win': 10, 'loss': 0, 'ratio': 10, 'mmr': 2000},
                                     {'name': 'LOZZA', 'win': 10, 'loss': 0, 'ratio': 10, 'mmr': 5000},
                                     {'name': 'JEFFERIES', 'win': 10, 'loss': 0, 'ratio': 10, 'mmr': 2000},
                                     {'name': 'JAMES', 'win': 10, 'loss': 0, 'ratio': 10, 'mmr': 2000}])

    @patch("onehead_balance.combinations")
    def test_calculate_balance_non_unique(self, mock_combinations):
        self.database.lookup_player.side_effect = self.mock_lookup_player
        mock_combination = [self.mock_db[:5], self.mock_db[5:]]
        mock_combination[0][0] = mock_combination[1][0]
        mock_combinations.side_effect = [MagicMock(), [mock_combination]]
        self.assertRaises(OneHeadException, self.team_balance._calculate_balance)

    @patch("onehead_balance.combinations")
    def test_calculate_balance_incorrect_profile_count(self, mock_combinations):
        self.database.lookup_player.return_value = []
        mock_combination = [self.mock_db[:5], self.mock_db[5:]]
        mock_combination[0][0] = mock_combination[1][0]
        mock_combinations.side_effect = [MagicMock(), [mock_combination]]
        self.assertRaises(OneHeadException, self.team_balance._calculate_balance)

    def test_balance_signups_less_than_10(self):
        mock_signups = ["BOB SAGET"]    # Only 1 signup, therefore should fail.
        self.pre_game.signups = mock_signups
        ctx = MagicMock()
        ctx.send = OneHeadAsyncTest.async_mock(return_value=None)
        self.assertRaises(OneHeadException, OneHeadAsyncTest._run, self.team_balance.balance(ctx))
        self.assertEqual(self.team_balance.signups, mock_signups)

    @patch("onehead_balance.OneHeadBalance._calculate_balance")
    def test_balance_success(self, mock_calculate_balance):

        self.pre_game.signups = self.signups    # Expected list of 10 signups.
        ctx = MagicMock()
        ctx.send = OneHeadAsyncTest.async_mock(return_value=None)
        OneHeadAsyncTest._run(self.team_balance.balance(ctx))
        mock_calculate_balance.assert_called_once()

