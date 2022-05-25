import asyncio
from unittest import TestCase
from unittest.mock import MagicMock, patch

from onehead.core import bot_factory


class OneHeadAsyncTest(object):
    @staticmethod
    def _run(coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    @staticmethod
    def async_mock(*args, **kwargs):
        m = MagicMock(*args, **kwargs)

        async def mock_coro(*args, **kwargs):
            return m(*args, **kwargs)

        mock_coro.mock = m
        return mock_coro


class OneHeadCoreTest(TestCase):
    def setUp(self):
        self.bot = bot_factory()
        self.core = self.bot.get_cog("OneHeadCore")
        self.core.radiant = MagicMock()
        self.core.dire = MagicMock()
        self.ctx = MagicMock()
        self.ctx.send = OneHeadAsyncTest.async_mock(return_value=None)

        # Mock out the DB connections
        db = self.bot.get_cog("OneHeadDB")
        db.db = MagicMock()
        db.dynamo = MagicMock()

    @patch("onehead.user.OneHeadPreGame.signup_check")
    def test_start_game_in_progress(self, mock_signup_check):
        self.core.game_in_progress = True
        OneHeadAsyncTest._run(self.core.start(self.ctx))
        self.assertFalse(mock_signup_check.called)

    @patch("onehead.balance.OneHeadBalance.balance")
    def test_start_game_signups_not_full(self, mock_balance):
        self.core.pre_game.signup_check = OneHeadAsyncTest.async_mock(
            return_value=False
        )
        OneHeadAsyncTest._run(self.core.start(self.ctx))
        self.assertFalse(mock_balance.called)

    @patch("onehead.betting.OneHeadBetting.open_betting_window")
    @patch("onehead.core.OneHeadCore._open_player_transfer_window")
    @patch("onehead.core.OneHeadCore._setup_teams")
    @patch(
        "onehead.core.commands.core.Command.invoke", new=OneHeadAsyncTest.async_mock()
    )
    def test_start_game_success(self, _, __, ___):
        self.core.pre_game.signup_check = OneHeadAsyncTest.async_mock(return_value=True)
        self.core.status = OneHeadAsyncTest.async_mock()
        self.core.pre_game.handle_signups = OneHeadAsyncTest.async_mock()
        mock_balanced_teams = MagicMock(), MagicMock()
        self.core.team_balance.balance = OneHeadAsyncTest.async_mock(
            return_value=mock_balanced_teams
        )
        OneHeadAsyncTest._run(self.core.start(self.ctx))

        self.assertEqual(self.core.radiant._id, mock_balanced_teams[0]._id)
        self.assertEqual(self.core.dire._id, mock_balanced_teams[1]._id)

    def test_stop_game_not_in_progress(self):
        self.core.game_in_progress = False
        self.core._reset_state = MagicMock()
        OneHeadAsyncTest._run(self.core.stop(self.ctx))
        self.assertEqual(self.core._reset_state.call_count, 0)

    def test_stop_success(self):
        self.core.game_in_progress = True
        self.core.channels.move_back_to_lobby = OneHeadAsyncTest.async_mock()
        self.core._reset_state = MagicMock()
        OneHeadAsyncTest._run(self.core.stop(self.ctx))
        self.assertEqual(self.core._reset_state.call_count, 1)

    def test_reset_state(self):
        self.core.game_in_progress = True
        self.core.radiant = ["foo" for x in range(5)]
        self.core.dire = ["bar" for x in range(5)]

        self.core._reset_state()
        self.assertFalse(self.core.game_in_progress)
        self.assertIsNone(self.core.radiant)
        self.assertIsNone(self.core.dire)

    def test_result_game_not_in_progress(self):
        self.core.game_in_progress = False
        OneHeadAsyncTest._run(self.core.result(self.ctx, "t1"))
        self.assertEqual(self.ctx.send.mock.call_count, 1)
        self.assertEqual(
            self.ctx.send.mock.call_args_list[0][0][0], "No currently active game."
        )

    def test_result_result_invalid(self):
        self.core.game_in_progress = True
        OneHeadAsyncTest._run(self.core.result(self.ctx, "foo"))
        self.assertEqual(self.ctx.send.mock.call_count, 1)
        self.assertEqual(
            self.ctx.send.mock.call_args_list[0][0][0],
            "Invalid Value - Must be either radiant or dire.",
        )

    @patch(
        "discord.ext.commands.core.Command.invoke", new=OneHeadAsyncTest.async_mock()
    )
    def test_result_victory(self):
        self.core.game_in_progress = True
        self.core._get_player_names = MagicMock()
        self.core.database.update_player = MagicMock()
        self.core.channels.move_back_to_lobby = OneHeadAsyncTest.async_mock()
        self.core.channels.teardown_discord_channels = OneHeadAsyncTest.async_mock()
        self.core._get_player_names.return_value = (
            [x for x in "abcde"],
            [x for x in "fghij"],
        )
        OneHeadAsyncTest._run(self.core.result(self.ctx, "radiant"))

        expected_args = [(x, True) for x in "abcde"] + [(x, False) for x in "fghij"]

        for i, args in enumerate(self.core.database.update_player.call_args_list):
            self.assertEqual(args[0], expected_args[i])

        self.assertEqual(self.core.channels.move_back_to_lobby.mock.call_count, 1)
        self.assertFalse(self.core.game_in_progress)
        self.assertEqual(self.core.radiant, None)
        self.assertEqual(self.core.dire, None)

    def test_status_game_not_in_progress(self):
        self.core.game_in_progress = False
        OneHeadAsyncTest._run(self.core.status(self.ctx))
        self.assertEqual(self.ctx.send.mock.call_count, 1)
        self.assertEqual(
            self.ctx.send.mock.call_args_list[0][0][0], "No currently active game."
        )

    @patch("onehead.core.tabulate")
    def test_status_success(self, mock_tabulate):
        self.core.game_in_progress = True
        self.core._get_player_names = MagicMock()
        self.core._get_player_names.return_value = (
            [x for x in "abcde"],
            [x for x in "fghij"],
        )
        OneHeadAsyncTest._run(self.core.status(self.ctx))
        self.assertEqual(mock_tabulate.call_count, 1)
