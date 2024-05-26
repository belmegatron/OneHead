from unittest.mock import Mock

import discord.ext.test as dpytest
import pytest
from conftest import TEST_USER, add_ihl_role
from discord.ext.commands import Bot, errors

from onehead.registration import Registration


class TestRegister:
    @pytest.mark.asyncio
    async def test_no_ihl_role(self, bot: Bot) -> None:
        with pytest.raises(errors.MissingRole):
            await dpytest.message("!register 9001")

    @pytest.mark.asyncio
    async def test_invalid_mmr(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")

        await dpytest.message("!register derp")
        assert (
            dpytest.verify()
            .message()
            .content(
                f"the command you are looking for is"
            ).contains()
        )

    @pytest.mark.asyncio
    async def test_mmr_less_than_min(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")
        await dpytest.message(f"!register {Registration.MIN_MMR - 100}")
        assert (
            dpytest.verify()
            .message()
            .content(
                "MMR is too low"
            ).contains()
        )

    @pytest.mark.asyncio
    async def test_mmr_greater_than_max(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")
        await dpytest.message(f"!register {Registration.MAX_MMR + 100}")
        assert (
            dpytest.verify()
            .message()
            .content(
                "MMR is too high"
            ).contains()
        )

    @pytest.mark.asyncio
    async def test_already_registered(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")
        registration: Registration = bot.get_cog("Registration")

        registration.database.get = Mock()
        registration.database.get.return_value = {"name": TEST_USER}

        await dpytest.message(f"!register {Registration.MIN_MMR + 100}")
        assert dpytest.verify().message().content("is already registered.").contains()

    @pytest.mark.asyncio
    async def test_success(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")
        registration: Registration = bot.get_cog("Registration")

        registration.database.get = Mock()
        registration.database.get.return_value = None
        registration.database.add = Mock()

        await dpytest.message(f"!register {Registration.MIN_MMR + 100}")
        assert (
            dpytest.verify().message().content("successfully registered.").contains()
        )


class TestDeregister:
    @pytest.mark.asyncio
    async def test_no_ihl_admin_role(self, bot: Bot) -> None:
        with pytest.raises(errors.MissingRole):
            await dpytest.message("!deregister RBEEZAY")
            
    @pytest.mark.asyncio
    async def test_user_not_in_guild(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL Admin")
        registration: Registration = bot.get_cog("Registration")

        registration.database.get = Mock()
        registration.database.get.return_value = None

        await dpytest.message("!deregister RBEEZAY")
        assert (
            dpytest.verify()
            .message()
            .content("could not be found").contains()
        )

    @pytest.mark.asyncio
    async def test_user_not_in_database(self, bot: Bot) -> None:
        await dpytest.member_join(name="RBEEZAY")
        await add_ihl_role(bot, "IHL Admin")
        registration: Registration = bot.get_cog("Registration")

        registration.database.get = Mock()
        registration.database.get.return_value = None

        await dpytest.message("!deregister RBEEZAY")
        assert (
            dpytest.verify()
            .message()
            .content("could not be found in the database.").contains()
        )

    @pytest.mark.asyncio
    async def test_success(self, bot: Bot) -> None:
        await dpytest.member_join(name="RBEEZAY")
        await add_ihl_role(bot, "IHL Admin")
        registration: Registration = bot.get_cog("Registration")

        registration.database.get = Mock()
        registration.database.get.return_value = {"name": "RBEEZAY"}
        registration.database.remove = Mock()

        await dpytest.message("!deregister RBEEZAY")
        assert (
            dpytest.verify()
            .message()
            .content("has been deregistered").contains()
        )
