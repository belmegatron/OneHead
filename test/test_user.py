from unittest import TestCase
from unittest.mock import MagicMock, call
import asyncio

from onehead.user import OneHeadPreGame


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


class OneHeadPreGameTest(TestCase):

    def setUp(self):
        self.db = MagicMock()
        self.pregame = OneHeadPreGame(self.db)
        self.ctx = MagicMock()
        self.ctx.send = OneHeadAsyncTest.async_mock(return_value=None)

    def test_handle_signups_only_10(self):
        self.pregame.signups = [x for x in range(10)]
        OneHeadAsyncTest._run(self.pregame.handle_signups(self.ctx))
        self.assertEqual(self.ctx.send.mock.call_count, 0)

    def test_handle_signups_greater_than_10(self):
        self.pregame.signups = [x for x in range(15)]
        OneHeadAsyncTest._run(self.pregame.handle_signups(self.ctx))
        self.assertEqual(len(self.pregame.signups), 10)
        self.assertEqual(self.ctx.send.mock.call_count, 3)

    def test_signup_check_threshold_met(self):
        self.pregame.signups = [x for x in range(10)]
        result = OneHeadAsyncTest._run(self.pregame.signup_check(self.ctx))
        self.assertTrue(result)

    def test_signup_check_zero_signups(self):
        self.pregame.signups = []
        result = OneHeadAsyncTest._run(self.pregame.signup_check(self.ctx))
        self.assertEqual(self.ctx.method_calls[0], call.send('There are currently no signups.'))
        self.assertFalse(result)

    def test_signup_check_single_signup(self):
        self.pregame.signups = [1]
        result = OneHeadAsyncTest._run(self.pregame.signup_check(self.ctx))
        self.assertEqual(self.ctx.method_calls[0], call.send('Only 1 Signup, require 9 more.'))
        self.assertFalse(result)

    def test_signup_check_less_than_10_signups(self):
        self.pregame.signups = [x for x in range(8)]
        result = OneHeadAsyncTest._run(self.pregame.signup_check(self.ctx))
        self.assertEqual(self.ctx.method_calls[0], call.send('Only 8 Signups, require 2 more.'))
        self.assertFalse(result)
