from unittest import TestCase
from mock import MagicMock
from decimal import Decimal
import asyncio

from onehead.db import OneHeadDB


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
        self.rt_response = {
            'Items': [{'win': Decimal('10'), 'mmr': Decimal('2500'), 'loss': Decimal('4'), 'name': 'JAMES'},
                      {'win': Decimal('5'), 'mmr': Decimal('2500'), 'loss': Decimal('3'), 'name': 'PECRO'},
                      {'win': Decimal('0'), 'mmr': Decimal('2000'), 'loss': Decimal('4'), 'name': 'JAQ'},
                      {'win': Decimal('3'), 'mmr': Decimal('2000'), 'loss': Decimal('9'), 'name': 'GEE'},
                      {'win': Decimal('3'), 'mmr': Decimal('3000'), 'loss': Decimal('0'), 'name': 'ARRE'},
                      {'win': Decimal('0'), 'mmr': Decimal('3400'), 'loss': Decimal('0'), 'name': 'PATRIK'},
                      {'win': Decimal('5'), 'mmr': Decimal('1000'), 'loss': Decimal('4'), 'name': 'SPONGE'},
                      {'win': Decimal('1'), 'mmr': Decimal('3000'), 'loss': Decimal('1'), 'name': 'SCOUT'},
                      {'win': Decimal('1'), 'mmr': Decimal('2000'), 'loss': Decimal('4'),
                       'name': 'JEFFERIES'},
                      {'win': Decimal('0'), 'mmr': Decimal('2000'), 'loss': Decimal('2'), 'name': 'RUGOR'},
                      {'win': Decimal('3'), 'mmr': Decimal('4000'), 'loss': Decimal('4'), 'name': 'RICH'},
                      {'win': Decimal('7'), 'mmr': Decimal('3000'), 'loss': Decimal('5'), 'name': 'JOSH'},
                      {'win': Decimal('6'), 'mmr': Decimal('4500'), 'loss': Decimal('5'), 'name': 'ERIC'},
                      {'win': Decimal('1'), 'mmr': Decimal('4500'), 'loss': Decimal('4'),
                       'name': 'RBEEZAY'},
                      {'win': Decimal('3'), 'mmr': Decimal('3500'), 'loss': Decimal('10'), 'name': 'EDD'},
                      {'win': Decimal('0'), 'mmr': Decimal('2000'), 'loss': Decimal('0'), 'name': 'NYLE'},
                      {'win': Decimal('3'), 'mmr': Decimal('1000'), 'loss': Decimal('2'), 'name': 'RAYMEZ'},
                      {'win': Decimal('2'), 'mmr': Decimal('1000'), 'loss': Decimal('0'), 'name': 'TOCCO'},
                      {'win': Decimal('7'), 'mmr': Decimal('3500'), 'loss': Decimal('5'), 'name': 'ZEE'},
                      {'win': Decimal('10'), 'mmr': Decimal('5000'), 'loss': Decimal('3'),
                       'name': 'LAURENCE'}], 'Count': 20, 'ScannedCount': 20,
            'ResponseMetadata': {'RequestId': 'OK50L9TCALP71OKO4T45TTEINNVV4KQNSO5AEMVJF66Q9ASUAAJG',
                                 'HTTPStatusCode': 200, 'HTTPHeaders': {'server': 'Server',
                                                                        'date': 'Thu, 09 Apr 2020 21:19:07 GMT',
                                                                        'content-type': 'application/x-amz-json-1.0',
                                                                        'content-length': '1542',
                                                                        'connection': 'keep-alive',
                                                                        'x-amzn-requestid': 'OK50L9TCALP71OKO4T45TTEINNVV4KQNSO5AEMVJF66Q9ASUAAJG',
                                                                        'x-amz-crc32': '2637118863'},
                                 'RetryAttempts': 0}}

        self.lp_response = {
            'Item': {'win': Decimal('1'), 'mmr': Decimal('4500'), 'loss': Decimal('4'), 'name': 'RBEEZAY'},
            'ResponseMetadata': {'RequestId': 'BJ5U2L36NDUFDBPIGR91J59NNFVV4KQNSO5AEMVJF66Q9ASUAAJG',
                                 'HTTPStatusCode': 200,
                                 'HTTPHeaders': {'server': 'Server', 'date': 'Thu, 09 Apr 2020 21:46:29 GMT',
                                                 'content-type': 'application/x-amz-json-1.0', 'content-length': '85',
                                                 'connection': 'keep-alive',
                                                 'x-amzn-requestid': 'BJ5U2L36NDUFDBPIGR91J59NNFVV4KQNSO5AEMVJF66Q9ASUAAJG',
                                                 'x-amz-crc32': '27472350'}, 'RetryAttempts': 0}}

        self.config = {
            "aws": {
                "dynamodb": {
                    "region": "eu-west-2",
                    "tables": {
                        "dota": "example-table"
                    }
                }
            },
            "discord": {
                "token": "",
                "channels": {
                    "lobby": "DOTA 2",
                    "match": "IGC IHL"
                }
            },
            "rating": {
                "is_adjusted": True
            }
        }
        self.database = OneHeadDB(self.config)

    def test_retrieve_table_success(self):
        self.database.db.scan = MagicMock()
        self.database.db.scan.return_value = self.rt_response
        table = self.database.retrieve_table()
        self.assertIsInstance(table, list)

    def test_retrieve_table_not_found(self):
        self.database.db.scan = MagicMock()
        self.database.db.scan.return_value = {}
        table = self.database.retrieve_table()
        self.assertIsNone(table)

    def test_lookup_player_success(self):
        self.database.db.get_item = MagicMock()
        self.database.db.get_item.return_value = self.lp_response
        player = self.database.lookup_player("RBEEZAY")
        self.assertIsInstance(player, dict)

    def test_lookup_player_not_found(self):
        self.database.db.get_item = MagicMock()
        self.database.db.get_item.return_value = {}
        player = self.database.lookup_player("RBEEZAY")
        self.assertIsNone(player)
