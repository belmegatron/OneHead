from unittest.mock import AsyncMock, Mock, patch
from typing import cast

import discord.ext.test as dpytest
import pytest
from conftest import TEST_USER, add_ihl_role
from discord.ext.commands import Bot, errors, CommandInvokeError

from onehead.game import ClassicGame
from onehead.store import GameStore
from onehead.transfers import Transfers


class TestShuffle:
    @pytest.mark.asyncio
    async def test_no_ihl_role(self, bot: Bot) -> None:
        with pytest.raises(errors.MissingRole):
            await dpytest.message("!shuffle")

    @pytest.mark.asyncio
    async def test_transfer_window_closed(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")

        store: GameStore = cast(GameStore, bot.get_cog("GameStore"))
        store.current_game = ClassicGame()
        store.current_game._transfer_window_open = False

        await dpytest.message("!shuffle")
        assert dpytest.verify().message().content("Unable to shuffle as player transfer window is closed.")

    @pytest.mark.asyncio
    async def test_invalid_teams(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")

        store: GameStore = cast(GameStore, bot.get_cog("GameStore"))
        store.current_game = ClassicGame()
        store.current_game._transfer_window_open = True

        with pytest.raises(CommandInvokeError):
            await dpytest.message("!shuffle")

    @pytest.mark.asyncio
    async def test_not_signed_up(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")

        store: GameStore = cast(GameStore, bot.get_cog("GameStore"))
        store.current_game = ClassicGame()
        store.current_game._transfer_window_open = True
        store.current_game.radiant = []
        store.current_game.dire = []

        await dpytest.message("!shuffle")
        assert (
            dpytest.verify()
            .message()
            .content(f"is unable to shuffle as they are not participating in the current game.")
            .contains()
        )

    @pytest.mark.asyncio
    async def test_insufficient_rbucks(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")

        store: GameStore = cast(GameStore, bot.get_cog("GameStore"))
        store.current_game = ClassicGame()
        store.current_game._transfer_window_open = True
        store.current_game.radiant = []
        store.current_game.dire = []

        transfers: Transfers = cast(Transfers, bot.get_cog("Transfers"))
        transfers.lobby.get_signups = Mock()
        transfers.lobby.get_signups.return_value = [TEST_USER]

        transfers.database.get = Mock()
        transfers.database.get.return_value = {"rbucks": 0}

        await dpytest.message("!shuffle")
        assert dpytest.verify().message().content("cannot shuffle as they only have 0 RBUCKS").contains()

    @pytest.mark.asyncio
    async def test_success(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")

        store: GameStore = cast(GameStore, bot.get_cog("GameStore"))
        store.current_game = ClassicGame()
        store.current_game._transfer_window_open = True
        store.current_game.radiant = []
        store.current_game.dire = []

        transfers: Transfers = cast(Transfers, bot.get_cog("Transfers"))
        transfers.lobby.get_signups = Mock()
        transfers.lobby.get_signups.return_value = [TEST_USER]

        transfers.database.get = Mock()
        transfers.database.get.return_value = {"rbucks": Transfers.SHUFFLE_COST + 100}
        transfers.database.modify = Mock()

        transfers.matchmaking.balance = AsyncMock()
        transfers.matchmaking.balance.return_value = [{"name": "A"}], [{"name": "B"}]

        with patch("onehead.transfers.play_sound"):
            await dpytest.message("!shuffle")
            assert (
                dpytest.verify()
                .message()
                .content(f"has spent **{Transfers.SHUFFLE_COST}** RBUCKS to **shuffle** the teams!")
                .contains()
            )
