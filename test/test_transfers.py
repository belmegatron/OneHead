from unittest.mock import AsyncMock, Mock

import discord.ext.test as dpytest
import pytest
from conftest import TEST_USER, add_ihl_role
from discord.ext.commands import Bot, Cog, errors

from onehead.common import OneHeadException
from onehead.game import Game
from onehead.transfers import Transfers


class TestShuffle:
    @pytest.mark.asyncio
    async def test_no_ihl_role(self, bot: Bot) -> None:
        with pytest.raises(errors.MissingRole):
            await dpytest.message("!shuffle")

    @pytest.mark.asyncio
    async def test_transfer_window_closed(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")

        core: Cog = bot.get_cog("Core")
        current_game: Game = core.current_game
        current_game._transfer_window_open = False

        await dpytest.message("!shuffle")
        assert (
            dpytest.verify()
            .message()
            .content("Unable to shuffle as player transfer window is closed.")
        )

    @pytest.mark.asyncio
    async def test_invalid_teams(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")

        core: Cog = bot.get_cog("Core")
        current_game: Game = core.current_game
        current_game._transfer_window_open = True

        with pytest.raises(OneHeadException):
            await dpytest.message("!shuffle")

    @pytest.mark.asyncio
    async def test_not_signed_up(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")

        core: Cog = bot.get_cog("Core")
        current_game: Game = core.current_game
        current_game._transfer_window_open = True
        current_game.radiant = []
        current_game.dire = []

        await dpytest.message("!shuffle")
        assert (
            dpytest.verify()
            .message()
            .content(f"{TEST_USER} is unable to shuffle as they did not sign up.")
        )

    @pytest.mark.asyncio
    async def test_insufficient_rbucks(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")

        core: Cog = bot.get_cog("Core")

        current_game: Game = core.current_game
        current_game._transfer_window_open = True
        current_game.radiant = []
        current_game.dire = []

        core.lobby.get_signups = Mock()
        core.lobby.get_signups.return_value = [TEST_USER]

        core.database.lookup_player = Mock()
        core.database.lookup_player.return_value = {"rbucks": 0}

        await dpytest.message("!shuffle")
        assert (
            dpytest.verify()
            .message()
            .content(
                f"{TEST_USER} cannot shuffle as they only have 0 "
                f"RBUCKS. A shuffle costs {Transfers.SHUFFLE_COST} RBUCKS"
            )
        )

    @pytest.mark.asyncio
    async def test_success(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")

        core: Cog = bot.get_cog("Core")
        current_game: Game = core.current_game
        current_game._transfer_window_open = True
        current_game.radiant = []
        current_game.dire = []

        core.lobby.get_signups = Mock()
        core.lobby.get_signups.return_value = [TEST_USER]

        core.database.lookup_player = Mock()
        core.database.lookup_player.return_value = {
            "rbucks": Transfers.SHUFFLE_COST + 100
        }
        core.database.update_rbucks = Mock()

        core.matchmaking.balance = AsyncMock()
        core.matchmaking.balance.return_value = [{"name": "A"}], [{"name": "B"}]
        core.setup_teams = AsyncMock()

        await dpytest.message("!shuffle")
        assert (
            dpytest.verify()
            .message()
            .content(
                f"{TEST_USER} has spent **{Transfers.SHUFFLE_COST}** RBUCKS to **shuffle** the teams!"
            )
        )
