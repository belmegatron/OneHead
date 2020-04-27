from unittest import TestCase
from mock import MagicMock, patch
import asyncio
from onehead_core import OneHeadCore


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
        self.bot = MagicMock()
        self.core = OneHeadCore(self.bot)

        self.ctx = MagicMock()
        self.ctx.send = OneHeadAsyncTest.async_mock(return_value=None)

    @patch("onehead_user.OneHeadPreGame.signup_check")
    def test_start_game_in_progress(self, mock_signup_check):
        self.core.game_in_progress = True
        OneHeadAsyncTest._run(self.core.start(self.core, self.ctx))
        self.assertFalse(mock_signup_check.called)

    @patch("onehead_balance.OneHeadBalance.balance")
    def test_start_game_signups_not_full(self, mock_balance):
        self.core.pre_game.signup_check = OneHeadAsyncTest.async_mock(return_value=False)
        OneHeadAsyncTest._run(self.core.start(self.core, self.ctx))
        self.assertFalse(mock_balance.called)

    @patch("onehead_common.OneHeadChannels.move_discord_channels")
    @patch("onehead_common.OneHeadChannels.set_teams")
    @patch("onehead_common.OneHeadChannels.create_discord_channels")
    @patch("discord.ext.commands.core.Command.invoke", new=OneHeadAsyncTest.async_mock())
    @patch("onehead_balance.OneHeadBalance.balance")
    def test_start_game_success(self, mock_balance, mock_create_discord_channels, mock_set_teams, mock_move_discord_channels):
        self.core.pre_game.signup_check = OneHeadAsyncTest.async_mock(return_value=True)
        self.core.status = OneHeadAsyncTest.async_mock()
        mock_balanced_teams = MagicMock(), MagicMock()
        mock_balance.return_value = mock_balanced_teams
        OneHeadAsyncTest._run(self.core.start(self.core, self.ctx))
        mock_create_discord_channels.is_called_once()
        mock_set_teams.is_called_once()
        mock_move_discord_channels.is_called_once()
        self.assertEqual(self.core.t1._id, mock_balanced_teams[0]._id)
        self.assertEqual(self.core.t2._id, mock_balanced_teams[1]._id)

    def test_stop_game_not_in_progress(self):
        self.core.game_in_progress = False
        self.core.reset_state = MagicMock()
        OneHeadAsyncTest._run(self.core.stop(self.core, self.ctx))
        self.assertEqual(self.core.reset_state.call_count, 0)

    def test_stop_success(self):
        self.core.game_in_progress = True
        self.core.channels.move_back_to_lobby = OneHeadAsyncTest.async_mock()
        self.core.reset_state = MagicMock()
        OneHeadAsyncTest._run(self.core.stop(self.core, self.ctx))
        self.assertEqual(self.core.reset_state.call_count, 1)

    def test_reset_state(self):

        self.core.game_in_progress = True
        self.core.t1 = ["foo" for x in range(5)]
        self.core.t2 = ["bar" for x in range(5)]

        self.core.reset_state()
        self.assertFalse(self.core.game_in_progress)
        self.assertEqual(self.core.t1, [])
        self.assertEqual(self.core.t2, [])

    def test_result_game_not_in_progress(self):
        self.core.game_in_progress = False
        OneHeadAsyncTest._run(self.core.result(self.core, self.ctx, "t1"))
        self.assertEqual(self.ctx.send.mock.call_count, 1)
        self.assertEqual(self.ctx.send.mock.call_args_list[0][0][0], "No currently active game.")

    def test_result_result_invalid(self):
        self.core.game_in_progress = True
        OneHeadAsyncTest._run(self.core.result(self.core, self.ctx, "foo"))
        self.assertEqual(self.ctx.send.mock.call_count, 1)
        self.assertEqual(self.ctx.send.mock.call_args_list[0][0][0],
                         "Invalid Value - Must be either 't1' or 't2' or 'void' if appropriate.")

    @patch("discord.ext.commands.core.Command.invoke", new=OneHeadAsyncTest.async_mock())
    def test_result_victory(self):

        self.core.game_in_progress = True
        self.core.get_player_names = MagicMock()
        self.core.database.update_player = MagicMock()
        self.core.channels.move_back_to_lobby = OneHeadAsyncTest.async_mock()
        self.core.channels.teardown_discord_channels = OneHeadAsyncTest.async_mock()
        self.core.get_player_names.return_value = ([x for x in "abcde"], [x for x in "fghij"])
        OneHeadAsyncTest._run(self.core.result(self.core, self.ctx, "t1"))

        expected_args = [(x, True) for x in "abcde"] + [(x, False) for x in "fghij"]

        for i, args in enumerate(self.core.database.update_player.call_args_list):
            self.assertEqual(args[0], expected_args[i])

        self.assertEqual(self.core.channels.move_back_to_lobby.mock.call_count, 1)
        self.assertFalse(self.core.game_in_progress)
        self.assertEqual(self.core.t1, [])
        self.assertEqual(self.core.t2, [])

    @patch("discord.ext.commands.core.Command.invoke", new=OneHeadAsyncTest.async_mock())
    def test_result_void(self):

        self.core.game_in_progress = True
        self.core.get_player_names = MagicMock()
        self.core.database.update_player = MagicMock()
        self.core.channels.move_back_to_lobby = OneHeadAsyncTest.async_mock()
        self.core.channels.teardown_discord_channels = OneHeadAsyncTest.async_mock()
        self.core.get_player_names.return_value = ([x for x in "abcde"], [x for x in "fghij"])
        OneHeadAsyncTest._run(self.core.result(self.core, self.ctx, "void"))
        self.assertEqual(self.core.database.update_player.call_count, 0)
        self.assertEqual(self.core.channels.move_back_to_lobby.mock.call_count, 1)
        self.assertFalse(self.core.game_in_progress)
        self.assertEqual(self.core.t1, [])
        self.assertEqual(self.core.t2, [])

    def test_status_game_not_in_progress(self):

        self.core.game_in_progress = False
        OneHeadAsyncTest._run(self.core.status(self.core, self.ctx))
        self.assertEqual(self.ctx.send.mock.call_count, 1)
        self.assertEqual(self.ctx.send.mock.call_args_list[0][0][0], "No currently active game.")

    @patch("onehead_core.tabulate")
    def test_status_success(self, mock_tabulate):

        self.core.game_in_progress = True
        self.core.get_player_names = MagicMock()
        self.core.get_player_names.return_value = ([x for x in "abcde"], [x for x in "fghij"])
        OneHeadAsyncTest._run(self.core.status(self.core, self.ctx))
        self.assertEqual(mock_tabulate.call_count, 1)
