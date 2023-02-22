import pytest
from unittest.mock import Mock

from discord.ext.commands import Bot, errors
import discord.ext.test as dpytest

from onehead.common import OneHeadException
from onehead.registration import Registration

from conftest import add_ihl_role, TEST_USER


class TestRegister:
    @pytest.mark.asyncio
    async def test_no_ihl_role(self, bot: Bot) -> None:
        with pytest.raises(errors.MissingRole):
            await dpytest.message("!register 9001")
    
    @pytest.mark.asyncio
    async def test_invalid_mmr(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")
        
        with pytest.raises(OneHeadException):
            await dpytest.message("!register derp")

    @pytest.mark.asyncio
    async def test_mmr_less_than_min(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")
        await dpytest.message(f"!register {Registration.MIN_MMR - 100}")
        assert dpytest.verify().message().content(f"{Registration.MIN_MMR - 100} MMR is too low, must be greater or equal to {Registration.MIN_MMR}.")
    
    @pytest.mark.asyncio
    async def test_already_registered(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")
        registration: Registration = bot.get_cog("Registration")
        
        registration.database.player_exists = Mock()
        registration.database.player_exists.return_value = True, 0
        
        await dpytest.message(f"!register {Registration.MIN_MMR + 100}")
        assert dpytest.verify().message().content(f"{TEST_USER} is already registered.")

    @pytest.mark.asyncio
    async def test_success(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")
        registration: Registration = bot.get_cog("Registration")
        
        registration.database.player_exists = Mock()
        registration.database.player_exists.return_value = False, 0
        registration.database.add_player = Mock()
        
        await dpytest.message(f"!register {Registration.MIN_MMR + 100}")
        assert dpytest.verify().message().content(f"{TEST_USER} successfully registered.")


class TestDeregister:
    @pytest.mark.asyncio
    async def test_no_ihl_admin_role(self, bot: Bot) -> None:
        with pytest.raises(errors.MissingRole):
            await dpytest.message("!deregister RBEEZAY")
    
    @pytest.mark.asyncio
    async def test_user_not_in_database(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL Admin")
        registration: Registration = bot.get_cog("Registration")
        
        registration.database.player_exists = Mock()
        registration.database.player_exists.return_value = False, 0
        
        await dpytest.message("!deregister RBEEZAY")
        assert dpytest.verify().message().content("RBEEZAY could not be found in the database.")
    
    @pytest.mark.asyncio
    async def test_success(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL Admin")
        registration: Registration = bot.get_cog("Registration")
        
        registration.database.player_exists = Mock()
        registration.database.player_exists.return_value = True, 0
        registration.database.remove_player = Mock()
        
        await dpytest.message("!deregister RBEEZAY")
        assert dpytest.verify().message().content("RBEEZAY has been successfully removed from the database.")
