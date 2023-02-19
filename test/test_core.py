import pytest
from unittest.mock import AsyncMock

from discord.ext.commands import Bot, errors
import discord.ext.test as dpytest

from onehead.core import Core
from onehead.common import Player
from onehead.game import Game
from onehead.lobby import Lobby

from conftest import add_ihl_role


class TestStart:
    @pytest.mark.asyncio
    async def test_no_ihl_admin_role(self, bot: Bot) -> None:
        with pytest.raises(errors.MissingRole):
            await dpytest.message("!start")

    @pytest.mark.asyncio
    async def test_game_in_progress(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL Admin")

        core: Core = bot.get_cog("Core")
        core.current_game._in_progress = True

        await dpytest.message("!start")
        assert dpytest.verify().message().content("Game already in progress...")

    @pytest.mark.asyncio
    async def test_game_no_signups(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL Admin")
        await dpytest.message("!start")
        assert dpytest.verify().message().content("There are currently no signups.")

    @pytest.mark.asyncio
    async def test_game_not_enough_signups(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL Admin")

        lobby: Lobby = bot.get_cog("Lobby")
        lobby._signups = ["BOB", "BILL"]

        await dpytest.message("!start")
        assert dpytest.verify().message().content("Only 2 Signup(s), require 8 more.")

    @pytest.mark.asyncio
    async def test_success(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")
        await add_ihl_role(bot, "IHL Admin")

        lobby: Lobby = bot.get_cog("Lobby")
        players: list[Player] = lobby.database.retrieve_table()[:10]
        lobby._signups = [player["name"] for player in players]

        core: Core = bot.get_cog("Core")
        balance: AsyncMock = AsyncMock()
        balance.return_value = [], []
        core.matchmaking.balance = balance
        core.setup_teams = AsyncMock()
        core.current_game.open_transfer_window = AsyncMock()
        core.current_game.open_betting_window = AsyncMock()

        await dpytest.message("!start")
        assert dpytest.verify().message().content("GLHF")


class TestStop:
    @pytest.mark.asyncio
    async def test_no_ihl_admin_role(self, bot: Bot) -> None:
        with pytest.raises(errors.MissingRole):
            await dpytest.message("!stop")

    @pytest.mark.asyncio
    async def test_no_active_game(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL Admin")
        await dpytest.message("!stop")
        assert dpytest.verify().message().content("No currently active game.")

    @pytest.mark.asyncio
    async def test_success(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL Admin")

        core: Core = bot.get_cog("Core")
        core.current_game._in_progress = True
        core.channels.move_back_to_lobby = AsyncMock()

        await dpytest.message("!stop")
        core.channels.move_back_to_lobby.assert_called()
        assert core.current_game.in_progress() is False
        assert core.lobby.get_signups() == []
        assert core.current_game.betting_window_open() is False
        assert core.current_game.transfer_window_open() is False
        assert core.current_game.get_bets() == []
        assert core.current_game.get_player_transfers() == []
        assert core.previous_game is None
        
