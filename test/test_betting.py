import pytest

from discord import Embed, colour
from discord.ext.commands import Bot, errors
import discord.ext.test as dpytest

from onehead.betting import Bet
from onehead.core import Core
from onehead.game import Game

from conftest import add_ihl_role


TEST_USER: str = "TestUser0_0_nick"


class TestBets:
    
    @pytest.mark.asyncio
    async def test_no_ihl_role(self, bot: Bot) -> None:

        with pytest.raises(errors.MissingRole):
            await dpytest.message("!bets")
    
    @pytest.mark.asyncio
    async def test_no_bets(self, bot: Bot) -> None:

        await add_ihl_role(bot, "IHL")    
        
        embed: Embed = Embed(colour=colour.Colour.green())
        embed.add_field(name="Active Bets", value="``````")
        
        await dpytest.message("!bets")
        assert dpytest.verify().message().embed(embed)
    
    @pytest.mark.asyncio
    async def test_success(self, bot: Bot) -> None:

        await add_ihl_role(bot, "IHL")    
        
        core: Core = bot.get_cog("Core")
        core.current_game._bets.append(Bet("dire", 1000, "RBEEZAY"))
        
        embed: Embed = Embed(colour=colour.Colour.green())
        embed.add_field(name="Active Bets", value='```side      stake  player\n------  -------  --------\ndire       1000  RBEEZAY```')
        await dpytest.message("!bets")
        assert dpytest.verify().message().embed(embed)