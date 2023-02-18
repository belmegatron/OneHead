import pytest

from discord.ext.commands import Bot, errors
import discord.ext.test as dpytest

from onehead.core import Core
from onehead.game import Game

from conftest import add_ihl_role


TEST_USER: str = "TestUser0_0_nick"

@pytest.mark.asyncio
async def test_no_ihl_role(bot: Bot) -> None:

    with pytest.raises(errors.MissingRole):
        await dpytest.message("!commend RBEEZAY")
    
@pytest.mark.asyncio
async def test_no_previous_game(bot: Bot) -> None:

    await add_ihl_role(bot, "IHL")    
    await dpytest.message("!commend RBEEZAY")
    assert dpytest.verify().message().content("Unable to commend as a game is yet to be played.")
    
@pytest.mark.asyncio
async def test_commender_did_not_play(bot: Bot) -> None:
    
    core: Core = bot.get_cog("Core")
    core.previous_game = Game()
    core.previous_game.radiant = []
    core.previous_game.dire = []

    await add_ihl_role(bot, "IHL")    
    await dpytest.message("!commend RBEEZAY")
    assert dpytest.verify().message().content(f"{TEST_USER} did not participate in the previous game and therefore cannot commend another player.")
    
@pytest.mark.asyncio
async def test_commend_self(bot: Bot) -> None:
    
    core: Core = bot.get_cog("Core")
    core.previous_game = Game()
    core.previous_game.radiant = [{"name": TEST_USER}]
    core.previous_game.dire = []

    await add_ihl_role(bot, "IHL")    
    await dpytest.message(f"!commend {TEST_USER}")
    assert dpytest.verify().message().content(f"{TEST_USER} you cannot commend yourself, nice try...")
    
@pytest.mark.asyncio
async def test_commendee_did_not_play(bot: Bot) -> None:
    
    core: Core = bot.get_cog("Core")
    core.previous_game = Game()
    core.previous_game.radiant = [{"name": TEST_USER}]
    core.previous_game.dire = []

    await add_ihl_role(bot, "IHL")    
    await dpytest.message(f"!commend RBEEZAY")
    assert dpytest.verify().message().content(f"RBEEZAY cannot be commended as they did not participate in the previous game.")
    
@pytest.mark.asyncio
async def test_previously_commended(bot: Bot) -> None:
    
    core: Core = bot.get_cog("Core")
    core.previous_game = Game()
    core.previous_game.radiant = [{"name": "RBEEZAY"}, {"name": TEST_USER}]
    core.previous_game.dire = []
    core.previous_game._commends["RBEEZAY"] = [TEST_USER]

    await add_ihl_role(bot, "IHL")    
    await dpytest.message(f"!commend RBEEZAY")
    assert dpytest.verify().message().content(f"RBEEZAY has already been commended by {TEST_USER}.")
    
@pytest.mark.asyncio
async def test_success(bot: Bot) -> None:
    
    core: Core = bot.get_cog("Core")
    core.previous_game = Game()
    core.previous_game.radiant = [{"name": "RBEEZAY"}, {"name": TEST_USER}]
    core.previous_game.dire = []

    await add_ihl_role(bot, "IHL")    
    await dpytest.message(f"!commend RBEEZAY")
    assert dpytest.verify().message().content(f"RBEEZAY has been commended.")