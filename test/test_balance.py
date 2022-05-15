import asyncio
from unittest import TestCase
from unittest.mock import MagicMock, patch

from onehead.balance import OneHeadBalance
from onehead.common import OneHeadException
from onehead.db import OneHeadDB
from onehead.user import OneHeadPreGame


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
        self.signups = [
            "RBEEZAY",
            "GEE",
            "LOZZA",
            "JEFFERIES",
            "JAMES",
            "PECRO",
            "ZEE",
            "JOSH",
            "EDD",
            "ARRECOOLAST",
        ]

        self.mock_profiles = (
            {"name": "RBEEZAY", "win": 10, "loss": 0, "ratio": 10, "mmr": 5000},
            {"name": "GEE", "win": 10, "loss": 0, "ratio": 10, "mmr": 2000},
            {"name": "LOZZA", "win": 10, "loss": 0, "ratio": 10, "mmr": 5000},
            {"name": "JEFFERIES", "win": 10, "loss": 0, "ratio": 10, "mmr": 2000},
            {"name": "JAMES", "win": 10, "loss": 0, "ratio": 10, "mmr": 2000},
            {"name": "PECRO", "win": 0, "loss": 10, "ratio": 0, "mmr": 2500},
            {"name": "ZEE", "win": 10, "loss": 0, "ratio": 10, "mmr": 3500},
            {"name": "JOSH", "win": 10, "loss": 0, "ratio": 10, "mmr": 3500},
            {"name": "EDD", "win": 10, "loss": 0, "ratio": 10, "mmr": 4000},
            {"name": "ARRECOOLAST", "win": 10, "loss": 0, "ratio": 10, "mmr": 3500},
        )

        self.mock_profiles_adjusted_mmr = (
            {
                "name": "RBEEZAY",
                "win": 10,
                "loss": 0,
                "ratio": 10,
                "mmr": 5000,
                "rating": 1750,
                "adjusted_mmr": 5250,
            },
            {
                "name": "GEE",
                "win": 10,
                "loss": 0,
                "ratio": 10,
                "mmr": 2000,
                "rating": 1750,
                "adjusted_mmr": 2250,
            },
            {
                "name": "LOZZA",
                "win": 10,
                "loss": 0,
                "ratio": 10,
                "mmr": 5000,
                "rating": 1750,
                "adjusted_mmr": 5250,
            },
            {
                "name": "JEFFERIES",
                "win": 10,
                "loss": 0,
                "ratio": 10,
                "mmr": 2000,
                "rating": 1750,
                "adjusted_mmr": 2250,
            },
            {
                "name": "JAMES",
                "win": 10,
                "loss": 0,
                "ratio": 10,
                "mmr": 2000,
                "rating": 1750,
                "adjusted_mmr": 2250,
            },
            {
                "name": "PECRO",
                "win": 0,
                "loss": 10,
                "ratio": 0,
                "mmr": 2500,
                "rating": 1250,
                "adjusted_mmr": 2250,
            },
            {
                "name": "ZEE",
                "win": 10,
                "loss": 0,
                "ratio": 10,
                "mmr": 3500,
                "rating": 1750,
                "adjusted_mmr": 3750,
            },
            {
                "name": "JOSH",
                "win": 10,
                "loss": 0,
                "ratio": 10,
                "mmr": 3500,
                "rating": 1750,
                "adjusted_mmr": 3750,
            },
            {
                "name": "EDD",
                "win": 10,
                "loss": 0,
                "ratio": 10,
                "mmr": 4000,
                "rating": 1750,
                "adjusted_mmr": 4250,
            },
            {
                "name": "ARRECOOLAST",
                "win": 10,
                "loss": 0,
                "ratio": 10,
                "mmr": 3500,
                "rating": 1750,
                "adjusted_mmr": 3750,
            },
        )

        self.database = MagicMock(spec=OneHeadDB)
        self.t1 = None
        self.t2 = None
        self.config = {
            "aws": {
                "dynamodb": {"region": "eu-west-2", "tables": {"dota": "example-table"}}
            },
            "discord": {
                "token": "",
                "channels": {"lobby": "DOTA 2", "match": "IGC IHL"},
            },
            "rating": {"save": ["RBEEZAY"], "avoid": ["GEE", "LOZZA"]},
        }
        self.team_balance = OneHeadBalance(self.database, self.pre_game, self.config)

    def test_calculate_balance_success(self):
        self.team_balance.signups = self.signups
        self.pre_game.signups = self.signups
        self.team_balance._get_profiles = MagicMock()
        self.team_balance._get_profiles.return_value = self.mock_profiles_adjusted_mmr

        result = self.team_balance._calculate_balance()

        self.assertEqual(result["rating_difference"], 0)

    def test_calculate_balance_non_unique(self):
        self.team_balance._get_profiles = MagicMock()
        self.team_balance._get_profiles.return_value = self.mock_profiles
        self.team_balance._calculate_unique_team_combinations = MagicMock()
        self.team_balance._calculate_unique_team_combinations.return_value = []
        self.assertRaises(OneHeadException, self.team_balance._calculate_balance)

    def test_calculate_balance_incorrect_profile_count(self):
        self.team_balance._get_profiles = MagicMock()
        self.team_balance._get_profiles.return_value = []
        self.assertRaises(OneHeadException, self.team_balance._calculate_balance)

    def test_calculate_unique_team_combinations_duplicate_name(self):
        mock_all_matchups = [
            (self.mock_profiles_adjusted_mmr[5:], self.mock_profiles_adjusted_mmr[5:])
        ]
        result = self.team_balance._calculate_unique_team_combinations(
            mock_all_matchups
        )
        self.assertEqual(result, [])

    def test_calculate_unique_team_combinations_success(self):
        mock_all_matchups = [
            (self.mock_profiles_adjusted_mmr[5:], self.mock_profiles_adjusted_mmr[:5])
        ]
        result = self.team_balance._calculate_unique_team_combinations(
            mock_all_matchups
        )
        self.assertEqual(result, mock_all_matchups)

    def test_calculate_rating_difference(self):
        mock_unique_combinations = [
            (
                {
                    "t1": self.mock_profiles_adjusted_mmr[5:],
                    "t2": self.mock_profiles_adjusted_mmr[:5],
                }
            )
        ]
        self.team_balance._calculate_rating_differences(mock_unique_combinations)

        self.assertEqual(mock_unique_combinations[0]["rating_difference"], 500)

    def test_balance_signups_less_than_10(self):
        mock_signups = ["BOB SAGET"]  # Only 1 signup, therefore should fail.
        self.pre_game.signups = mock_signups
        ctx = MagicMock()
        ctx.send = OneHeadAsyncTest.async_mock(return_value=None)
        self.assertRaises(
            OneHeadException, OneHeadAsyncTest._run, self.team_balance.balance(ctx)
        )
        self.assertEqual(self.team_balance.pre_game.signups, mock_signups)

    @patch("onehead.balance.OneHeadBalance._calculate_balance")
    def test_balance_success(self, mock_calculate_balance):
        self.pre_game.signups = self.signups  # Expected list of 10 signups.
        ctx = MagicMock()
        ctx.send = OneHeadAsyncTest.async_mock(return_value=None)
        OneHeadAsyncTest._run(self.team_balance.balance(ctx))
        mock_calculate_balance.assert_called_once()
