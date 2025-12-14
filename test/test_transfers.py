from typing import cast
from unittest.mock import AsyncMock, Mock, patch

import discord.ext.test as dpytest
import pytest
from conftest import TEST_USER, add_ihl_role, create_fake_team
from discord.ext.commands import Bot, CommandInvokeError, errors

from onehead.common import Player
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
        store.current_game.radiant = create_fake_team()
        store.current_game.dire = create_fake_team()

        await dpytest.message("!shuffle")
        assert (
            dpytest.verify()
            .message()
            .content("is unable to shuffle as they are not participating in the current game.")
            .contains()
        )

    @pytest.mark.asyncio
    async def test_insufficient_rbucks(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")

        store: GameStore = cast(GameStore, bot.get_cog("GameStore"))
        store.current_game = ClassicGame()
        store.current_game._transfer_window_open = True
        store.current_game.radiant = create_fake_team()
        store.current_game.dire = create_fake_team()

        transfers: Transfers = cast(Transfers, bot.get_cog("Transfers"))
        transfers.lobby.get_signups = Mock()
        transfers.lobby.get_signups.return_value = [TEST_USER]

        transfers.database.get = Mock()
        transfers.database.get.return_value = Player(
            id=262570465212497920,
            name="HARRY",
            mmr=4750,
            rbucks=0,
        )

        await dpytest.message("!shuffle")
        assert dpytest.verify().message().content("cannot shuffle as they only have 0 RBUCKS").contains()

    @pytest.mark.asyncio
    async def test_success(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")

        store: GameStore = cast(GameStore, bot.get_cog("GameStore"))
        store.current_game = ClassicGame()
        store.current_game._transfer_window_open = True
        store.current_game.radiant = create_fake_team()
        store.current_game.dire = create_fake_team()

        transfers: Transfers = cast(Transfers, bot.get_cog("Transfers"))
        transfers.lobby.get_signups = Mock()
        transfers.lobby.get_signups.return_value = [TEST_USER]

        transfers.database.get = Mock()
        transfers.database.get.return_value = Player(
            id=262570465212497920,
            name="HARRY",
            mmr=4750,
            rbucks=Transfers.SHUFFLE_COST + 100,
        )
        transfers.database.update = Mock()

        transfers.matchmaking.balance = AsyncMock()
        transfers.matchmaking.balance.return_value = (
            create_fake_team(),
            create_fake_team(),
        )

        with patch("onehead.transfers.play_sound"):
            await dpytest.message("!shuffle")
            assert (
                dpytest.verify()
                .message()
                .content(f"has spent **{Transfers.SHUFFLE_COST}** RBUCKS to **shuffle** the teams!")
                .contains()
            )
