from unittest.mock import MagicMock, patch
from datetime import datetime
from discord.member import Member
import discord.ext.test as dpytest
from discord.ext.commands import Bot

import pytest

from onehead.challenge import ChallengeMode, Challenge
from onehead.database import Database
from onehead.common import Player

class TestCalculateOdds:
    @pytest.mark.asyncio
    async def test_challenger_favoured(self, bot: Bot):
        db = MagicMock(spec=Database)
        cm: ChallengeMode = ChallengeMode(db)
        challenger: Member = await dpytest.member_join(name="RBEEZAY")
        opponent: Member = await dpytest.member_join(name="GEE")
        
        challenger_record: Player = {"adjusted_mmr": 3000}
        opponent_record: Player = {"adjusted_mmr": 2000}
        
        db.get.side_effect = [challenger_record, opponent_record]
        
        challenge: Challenge = Challenge(0, datetime.now(), challenger, opponent)
        
        challenger_odds, opponent_odds = cm.calculate_odds(challenge)
        assert challenger_odds == 1.5
        assert opponent_odds == 3.0
        
    @pytest.mark.asyncio
    async def test_opponent_favoured(self, bot: Bot):
        db = MagicMock(spec=Database)
        cm: ChallengeMode = ChallengeMode(db)
        challenger: Member = await dpytest.member_join(name="RBEEZAY")
        opponent: Member = await dpytest.member_join(name="GEE")
        
        challenger_record: Player = {"adjusted_mmr": 2000}
        opponent_record: Player = {"adjusted_mmr": 3000}
        
        db.get.side_effect = [challenger_record, opponent_record]
        
        challenge: Challenge = Challenge(0, datetime.now(), challenger, opponent)
        
        challenger_odds, opponent_odds = cm.calculate_odds(challenge)
        assert challenger_odds == 3.0
        assert opponent_odds == 1.5
        
    @pytest.mark.asyncio
    async def test_equal_odds(self, bot: Bot):
        db = MagicMock(spec=Database)
        cm: ChallengeMode = ChallengeMode(db)
        challenger: Member = await dpytest.member_join(name="RBEEZAY")
        opponent: Member = await dpytest.member_join(name="GEE")
        
        challenger_record: Player = {"adjusted_mmr": 3000}
        opponent_record: Player = {"adjusted_mmr": 3000}
        
        db.get.side_effect = [challenger_record, opponent_record]
        
        challenge: Challenge = Challenge(0, datetime.now(), challenger, opponent)
        
        challenger_odds, opponent_odds = cm.calculate_odds(challenge)
        assert challenger_odds == 2.0
        assert opponent_odds == 2.0