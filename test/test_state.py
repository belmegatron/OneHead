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


class OneHeadStateTest(TestCase):
    def setUp(self):
        self.bot = bot_factory()
        self.ctx = MagicMock()
        self.ctx.send = OneHeadAsyncTest.async_mock(return_value=None)

        # Mock out the DB connections
        db = self.bot.get_cog("OneHeadDB")
        db.db = MagicMock()
        db.dynamo = MagicMock()

    @patch("onehead.betting.OneHeadBetting.open_betting_window")
    @patch("onehead.core.OneHeadCore._open_player_transfer_window")
    @patch("onehead.core.OneHeadCore._setup_teams")
    @patch(
        "discord.ext.commands.core.Command.invoke", new=OneHeadAsyncTest.async_mock()
    )
    def test_result_reset_state(self, _, __, ___):
        core = self.bot.get_cog("OneHeadCore")

        # Let's pretend 10 players have signed up
        core.pre_game.signups = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]

        # Mock out how the teams were balanced
        core.team_balance.balance = OneHeadAsyncTest.async_mock(
            return_value=(
                [
                    {"name": "A"},
                    {"name": "B"},
                    {"name": "C"},
                    {"name": "D"},
                    {"name": "E"},
                ],
                [
                    {"name": "F"},
                    {"name": "G"},
                    {"name": "H"},
                    {"name": "I"},
                    {"name": "J"},
                ],
            )
        )

        # Mock out any channel admin
        core.channels.create_discord_channels = OneHeadAsyncTest.async_mock()
        core.channels.move_discord_channels = OneHeadAsyncTest.async_mock()

        # Start the pretend match
        OneHeadAsyncTest._run(core.start(self.ctx))

        core.database.update_player = MagicMock()
        core.channels.move_back_to_lobby = OneHeadAsyncTest.async_mock()

        # The pretend match has finished, enter a result
        OneHeadAsyncTest._run(core.result(self.ctx, "dire"))

        self.assertIsNone(core.radiant)
        self.assertIsNone(core.dire)
        self.assertEqual(core.pre_game.signups, [])

        # Let's pretend 10 different players have signed up
        core.pre_game.signups = [
            "RBEEZAY",
            "GEE",
            "LAURENCE",
            "ZEE",
            "EDD",
            "ERIC",
            "JAQ",
            "PECRO",
            "SPONGE",
            "TOCCO",
        ]

        # Mock out how the teams were balanced
        core.team_balance.balance = OneHeadAsyncTest.async_mock(
            return_value=(
                [
                    {"name": "RBEEZAY"},
                    {"name": "GEE"},
                    {"name": "LAURENCE"},
                    {"name": "ZEE"},
                    {"name": "EDD"},
                ],
                [
                    {"name": "ERIC"},
                    {"name": "JAQ"},
                    {"name": "PECRO"},
                    {"name": "SPONGE"},
                    {"name": "TOCCO"},
                ],
            )
        )

        # Start the pretend match
        OneHeadAsyncTest._run(core.start(self.ctx))

        self.assertEqual(
            core.radiant,
            [
                {"name": "RBEEZAY"},
                {"name": "GEE"},
                {"name": "LAURENCE"},
                {"name": "ZEE"},
                {"name": "EDD"},
            ],
        )
        self.assertEqual(
            core.dire,
            [
                {"name": "ERIC"},
                {"name": "JAQ"},
                {"name": "PECRO"},
                {"name": "SPONGE"},
                {"name": "TOCCO"},
            ],
        )
        self.assertEqual(
            core.pre_game.signups,
            [
                "RBEEZAY",
                "GEE",
                "LAURENCE",
                "ZEE",
                "EDD",
                "ERIC",
                "JAQ",
                "PECRO",
                "SPONGE",
                "TOCCO",
            ],
        )
