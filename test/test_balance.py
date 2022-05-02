import asyncio
from unittest import TestCase
from unittest.mock import MagicMock, patch

from onehead.balance import OneHeadBalance, OneHeadCaptainsMode
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
            ({"t1": self.mock_profiles_adjusted_mmr[5:], "t2": self.mock_profiles_adjusted_mmr[:5]})
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


class OneHeadCaptainsModeTest(TestCase):
    def setUp(self):
        self.database = MagicMock(spec=OneHeadDB)
        self.pre_game = MagicMock(spec=OneHeadPreGame)
        self.cm = OneHeadCaptainsMode(self.database, self.pre_game)
        self.cm.pre_game.signups = [
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
        self.cm.votes = {x: 0 for x in self.cm.pre_game.signups}
        self.cm.has_voted = {x: False for x in self.cm.pre_game.signups}
        self.ctx = MagicMock()
        self.ctx.send = OneHeadAsyncTest.async_mock(return_value=None)

    def test_nominate_success(self):
        self.cm.nomination_phase_in_progress = True
        self.ctx.author.display_name = "RBEEZAY"
        OneHeadAsyncTest._run(self.cm.nominate(self.cm, self.ctx, "GEE"))
        self.assertEqual(self.cm.votes["GEE"], 1)

    def test_nominate_lowercase(self):
        self.cm.nomination_phase_in_progress = True
        self.ctx.author.display_name = "RBEEZAY"
        OneHeadAsyncTest._run(self.cm.nominate(self.cm, self.ctx, "GEE"))
        self.assertEqual(self.cm.votes["GEE"], 1)

    def test_nominate_nominator_not_signed_up(self):
        self.cm.nomination_phase_in_progress = True
        self.ctx.author.display_name = "JLESCH"
        OneHeadAsyncTest._run(self.cm.nominate(self.cm, self.ctx, "GEE"))
        self.assertEqual(
            self.ctx.send.mock.call_args_list[0][0][0],
            f"{self.ctx.author.display_name} is not currently signed up and therefore cannot nominate.",
        )

    def test_nominate_nominations_not_open(self):
        self.cm.nomination_phase_in_progress = False
        self.ctx.author.display_name = "RBEEZAY"
        OneHeadAsyncTest._run(self.cm.nominate(self.cm, self.ctx, "GEE"))
        self.assertEqual(
            self.ctx.send.mock.call_args_list[0][0][0], "Nominations are closed."
        )

    def test_nominate_nominatee_not_signed_up(self):
        self.cm.nomination_phase_in_progress = True
        self.ctx.author.display_name = "RBEEZAY"
        OneHeadAsyncTest._run(self.cm.nominate(self.cm, self.ctx, "JLESCH"))
        self.assertEqual(
            self.ctx.send.mock.call_args_list[0][0][0],
            "JLESCH is not currently signed up and therefore cannot be nominated.",
        )

    def test_nominate_already_voted(self):
        self.cm.nomination_phase_in_progress = True
        self.ctx.author.display_name = "RBEEZAY"
        self.cm.has_voted["RBEEZAY"] = True
        OneHeadAsyncTest._run(self.cm.nominate(self.cm, self.ctx, "GEE"))
        self.assertEqual(
            self.ctx.send.mock.call_args_list[0][0][0],
            f"{self.ctx.author.display_name} has already voted.",
        )

    def test_nominate_self_vote(self):
        self.cm.nomination_phase_in_progress = True
        self.ctx.author.display_name = "RBEEZAY"
        OneHeadAsyncTest._run(self.cm.nominate(self.cm, self.ctx, "RBEEZAY"))
        self.assertEqual(
            self.ctx.send.mock.call_args_list[0][0][0],
            f"{self.ctx.author.display_name}, you cannot vote for yourself.",
        )

    def test_calculate_top_nominations_no_tie(self):
        self.cm.votes = {
            "RBEEZAY": 3,
            "GEE": 2,
            "LOZZA": 1,
            "JEFFERIES": 0,
            "JAMES": 0,
            "PECRO": 0,
            "ZEE": 0,
            "JOSH": 0,
            "EDD": 0,
            "ARRECOOLAST": 0,
        }

        c1, c2 = self.cm.calculate_top_nominations()
        self.assertEqual(c1, "RBEEZAY")
        self.assertEqual(c2, "GEE")

    def test_calculate_top_nominations_two_way_tie(self):
        self.cm.votes = {
            "RBEEZAY": 3,
            "GEE": 2,
            "LOZZA": 3,
            "JEFFERIES": 1,
            "JAMES": 0,
            "PECRO": 0,
            "ZEE": 0,
            "JOSH": 0,
            "EDD": 0,
            "ARRECOOLAST": 0,
        }

        c1, c2 = self.cm.calculate_top_nominations()
        self.assertEqual(c1, "RBEEZAY")
        self.assertEqual(c2, "LOZZA")

    def test_calculate_top_nominations_three_way_tie(self):
        self.cm.votes = {
            "RBEEZAY": 3,
            "GEE": 3,
            "LOZZA": 3,
            "JEFFERIES": 2,
            "JAMES": 1,
            "PECRO": 0,
            "ZEE": 0,
            "JOSH": 0,
            "EDD": 0,
            "ARRECOOLAST": 0,
        }

        expected_captain_pool = ["RBEEZAY", "GEE", "LOZZA"]
        c1, c2 = self.cm.calculate_top_nominations()
        self.assertIn(c1, expected_captain_pool)
        self.assertIn(c2, expected_captain_pool)

    def test_calculate_top_nominations_second_place_tie(self):
        self.cm.votes = {
            "RBEEZAY": 3,
            "GEE": 2,
            "LOZZA": 2,
            "JEFFERIES": 2,
            "JAMES": 1,
            "PECRO": 0,
            "ZEE": 0,
            "JOSH": 0,
            "EDD": 0,
            "ARRECOOLAST": 0,
        }
        c1, c2 = self.cm.calculate_top_nominations()
        expected_second_place_captain_pool = ["GEE", "LOZZA", "JEFFERIES"]
        self.assertEqual(c1, "RBEEZAY")
        self.assertIn(c2, expected_second_place_captain_pool)

    def test_pick_phase_not_in_progress(self):
        self.cm.pick_phase_in_progress = False
        OneHeadAsyncTest._run(self.cm.pick(self.cm, self.ctx, "RBEEZAY"))
        self.assertEqual(
            self.ctx.send.mock.call_args_list[0][0][0],
            "Pick phase is not currently in progress.",
        )

    def test_pick_not_captain(self):
        self.ctx.author.display_name = "PECRO"
        self.cm.captain_1 = "RBEEZAY"
        self.cm.captain_2 = "GEE"
        self.cm.pick_phase_in_progress = True

        OneHeadAsyncTest._run(self.cm.pick(self.cm, self.ctx, "ARRE"))
        self.assertEqual(
            self.ctx.send.mock.call_args_list[0][0][0],
            "PECRO is not a captain and therefore cannot pick.",
        )

    def test_pick_not_captains_turn(self):
        self.ctx.author.display_name = "RBEEZAY"
        self.cm.captain_1 = "RBEEZAY"
        self.cm.captain_2 = "GEE"

        self.cm.pick_phase_in_progress = True
        self.cm.radiant_captain_turn = False
        self.cm.dire_captain_turn = True

        OneHeadAsyncTest._run(self.cm.pick(self.cm, self.ctx, "ARRE"))
        self.assertEqual(
            self.ctx.send.mock.call_args_list[0][0][0],
            "It is currently GEE's turn to pick.",
        )

    def test_pick_lowercase_name(self):
        self.cm.add_pick = OneHeadAsyncTest.async_mock(return_value=True)

        self.ctx.author.display_name = "RBEEZAY"
        self.cm.captain_1 = "RBEEZAY"
        self.cm.captain_2 = "GEE"

        self.cm.pick_phase_in_progress = True
        self.cm.radiant_captain_turn = True
        self.cm.dire_captain_turn = False

        OneHeadAsyncTest._run(self.cm.pick(self.cm, self.ctx, "arre"))
        self.cm.add_pick.mock.is_called_once()
        self.assertEqual(
            self.ctx.send.mock.call_args_list[0][0][0],
            "RBEEZAY has selected ARRE to join Team 1.",
        )

    def test_pick_success(self):
        self.cm.add_pick = OneHeadAsyncTest.async_mock(return_value=True)

        self.ctx.author.display_name = "RBEEZAY"
        self.cm.captain_1 = "RBEEZAY"
        self.cm.captain_2 = "GEE"

        self.cm.pick_phase_in_progress = True
        self.cm.radiant_captain_turn = True
        self.cm.dire_captain_turn = False

        OneHeadAsyncTest._run(self.cm.pick(self.cm, self.ctx, "ARRE"))
        self.cm.add_pick.mock.is_called_once()
        self.assertEqual(
            self.ctx.send.mock.call_args_list[0][0][0],
            "RBEEZAY has selected ARRE to join Team 1.",
        )

    def test_picking_phase_captain_not_assigned(self):
        self.cm.captain_1 = "RBEEZAY"
        self.cm.captain_2 = None
        self.assertRaises(
            OneHeadException, OneHeadAsyncTest._run, self.cm.picking_phase(self.ctx)
        )
