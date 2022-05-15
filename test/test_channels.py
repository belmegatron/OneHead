import asyncio
from unittest import TestCase
from unittest.mock import MagicMock, call, patch

from onehead.channels import OneHeadChannels
from onehead.common import OneHeadException


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


class OneHeadChannelsTest(TestCase):
    def setUp(self):
        self.config = {
            "aws": {
                "dynamodb": {"region": "eu-west-2", "tables": {"dota": "example-table"}}
            },
            "discord": {
                "token": "",
                "channels": {"lobby": "DOTA 2", "match": "IGC IHL"},
            },
            "rating": {"is_adjusted": True},
        }
        self.oh_channels = OneHeadChannels(self.config)
        self.ctx = MagicMock()
        self.ctx.send = OneHeadAsyncTest.async_mock(return_value=None)

    def test_create_discord_channels_already_exist(self):
        ihl_1 = MagicMock()
        ihl_1.name = "IGC IHL #1"
        ihl_2 = MagicMock()
        ihl_2.name = "IGC IHL #2"

        self.ctx.guild.voice_channels = [ihl_1, ihl_2, MagicMock()]
        OneHeadAsyncTest._run(self.oh_channels.create_discord_channels(self.ctx))
        self.assertEqual(self.ctx.send.mock.call_count, 0)
        self.assertEqual(self.oh_channels.ihl_discord_channels, [ihl_1, ihl_2])

    def test_create_discord_channels_missing(self):
        lobby = MagicMock()
        lobby.name = "LOBBY"
        csgo = MagicMock()
        csgo.name = "CSGO"

        self.ctx.guild.voice_channels = [lobby, csgo]
        self.ctx.guild.create_voice_channel = OneHeadAsyncTest.async_mock()

        OneHeadAsyncTest._run(self.oh_channels.create_discord_channels(self.ctx))
        self.assertEqual(self.ctx.send.mock.call_count, 2)
        self.assertEqual(self.ctx.guild.create_voice_channel.mock.call_count, 2)

    def test_move_back_to_lobby(self):
        lobby = MagicMock()
        lobby.name = "LOBBY"
        csgo = MagicMock()
        csgo.name = "CSGO"

        self.oh_channels.lobby_name = lobby.name
        self.ctx.guild.voice_channels = [lobby, csgo]

        member = MagicMock()
        member.move_to = OneHeadAsyncTest.async_mock()
        self.oh_channels.t1_discord_members = [member for x in range(5)]
        self.oh_channels.t2_discord_members = [member for x in range(5)]

        OneHeadAsyncTest._run(self.oh_channels.move_back_to_lobby(self.ctx))
        self.assertEqual(member.move_to.mock.call_count, 10)

    def test_move_discord_channels_exception(self):
        self.oh_channels.ihl_discord_channels = []
        self.assertRaises(
            OneHeadException,
            OneHeadAsyncTest._run,
            self.oh_channels.move_discord_channels(self.ctx),
        )

    @patch("onehead.channels.OneHeadChannels._get_discord_members")
    @patch(
        "onehead.common.OneHeadCommon.get_player_names",
        return_value=(MagicMock(), MagicMock()),
    )
    def test_move_discord_channels_success(
        self, mock_get_player_names, mock_get_discord_members
    ):
        ihl_1 = MagicMock()
        ihl_1.name = "IGC IHL #1"
        ihl_2 = MagicMock()
        ihl_2.name = "IGC IHL #2"

        self.oh_channels.ihl_discord_channels = [ihl_1, ihl_2]
        self.t1, self.t2 = MagicMock(), MagicMock()

        member = MagicMock()
        member.move_to = OneHeadAsyncTest.async_mock()
        self.oh_channels.t1_discord_members = [member for x in range(5)]
        self.oh_channels.t2_discord_members = [member for x in range(5)]
        self.oh_channels.t1 = MagicMock()
        self.oh_channels.t2 = MagicMock()

        OneHeadAsyncTest._run(self.oh_channels.move_discord_channels(self.ctx))
        mock_get_player_names.is_called_once()
        mock_get_discord_members.is_called_once()
        self.ctx.send.mock.is_called_once()
        member.move_to.mock.assert_has_calls(
            [call(ihl_1) for x in range(5)] + [call(ihl_2) for x in range(5)]
        )
