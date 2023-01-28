import asyncio
from unittest import TestCase
from unittest.mock import MagicMock

from tinydb import Query, TinyDB

from onehead.common import OneHeadException
from onehead.database import Database


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


class OneHeadDBTest(TestCase):
    def setUp(self):
   
        self.config = {
    "tinydb": {
        "path": "secrets/db.json"
    },
    "discord": {
        "token": "ABCDEFGH",
        "channels": {
            "lobby": "INTERNAL WAITING ROOM",
            "match": "IGC IHL"
        }
    }
}
        self.database = Database(self.config)

    def test_retrieve_table_success(self):
        table = self.database.retrieve_table()
        self.assertIsInstance(table, list)

    def test_lookup_player_success(self):
        player = self.database.lookup_player("RBEEZAY")
        self.assertIsInstance(player, dict)

    def test_lookup_player_not_found(self):
        with self.assertRaises(OneHeadException):
            player = self.database.lookup_player("PLAYERDOESNOTEXIST")
