from unittest.mock import AsyncMock

import discord.ext.test as dpytest
import pytest
from conftest import add_ihl_role
from discord.ext.commands import Bot, errors

from onehead.common import OneHeadException, Player, Side
from onehead.core import Core
from onehead.game import Game
from onehead.lobby import Lobby


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
        players: list[Player] = lobby.database.get_all()[:10]
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


class TestResult:
    @pytest.mark.asyncio
    async def test_no_ihl_admin_role(self, bot: Bot) -> None:
        with pytest.raises(errors.MissingRole):
            await dpytest.message(f"!result {Side.RADIANT}")

    @pytest.mark.asyncio
    async def test_no_active_game(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL Admin")
        await dpytest.message(f"!result {Side.RADIANT}")
        assert dpytest.verify().message().content("No currently active game.")

    @pytest.mark.asyncio
    async def test_transfer_window_open(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL Admin")
        core: Core = bot.get_cog("Core")
        core.current_game._in_progress = True
        core.current_game._transfer_window_open = True
        core.current_game._betting_window_open = False

        await dpytest.message(f"!result {Side.RADIANT}")
        assert (
            dpytest.verify()
            .message()
            .content(
                "Cannot enter result as the Transfer window for the game is currently open. Use the !stop command if you wish to abort the game."
            )
        )

    @pytest.mark.asyncio
    async def test_betting_window_open(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL Admin")
        core: Core = bot.get_cog("Core")
        core.current_game._in_progress = True
        core.current_game._transfer_window_open = False
        core.current_game._betting_window_open = True

        await dpytest.message(f"!result {Side.RADIANT}")
        assert (
            dpytest.verify()
            .message()
            .content(
                "Cannot enter result as the Betting window for the game is currently open. Use the !stop command if you wish to abort the game."
            )
        )

    @pytest.mark.asyncio
    async def test_invalid_side(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL Admin")
        core: Core = bot.get_cog("Core")
        core.current_game._in_progress = True
        await dpytest.message("!result derp")
        assert dpytest.verify().message().content(f"Invalid Value - Must be either {Side.RADIANT} or {Side.DIRE}.")

    @pytest.mark.asyncio
    async def test_invalid_team(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL Admin")
        core: Core = bot.get_cog("Core")
        core.current_game._in_progress = True

        with pytest.raises(OneHeadException):
            await dpytest.message(f"!result {Side.RADIANT}")

    @pytest.mark.asyncio
    async def test_success(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")
        await add_ihl_role(bot, "IHL Admin")
        core: Core = bot.get_cog("Core")
        current_game: Game = core.current_game
        current_game._in_progress = True
        current_game.radiant = []
        current_game.dire = []

        core.scoreboard.scoreboard = AsyncMock()
        core.channels.move_back_to_lobby = AsyncMock()

        await dpytest.message(f"!result {Side.RADIANT}")

        core.channels.move_back_to_lobby.assert_called_once()
        assert core.current_game.in_progress() is False
        assert core.lobby.get_signups() == []
        assert core.current_game.betting_window_open() is False
        assert core.current_game.transfer_window_open() is False
        assert core.current_game.get_bets() == []
        assert core.current_game.get_player_transfers() == []
        assert core.previous_game == current_game


class TestStatus:
    @pytest.mark.asyncio
    async def test_no_ihl_role(self, bot: Bot) -> None:
        with pytest.raises(errors.MissingRole):
            await dpytest.message("!status")

    @pytest.mark.asyncio
    async def test_no_active_game(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")
        await dpytest.message("!status")
        assert dpytest.verify().message().content("No currently active game.")

    @pytest.mark.asyncio
    async def test_success(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")
        core: Core = bot.get_cog("Core")
        core.current_game._in_progress = True
        core.current_game.radiant = [
            {"name": "A"},
            {"name": "B"},
            {"name": "C"},
            {"name": "D"},
            {"name": "E"},
        ]
        core.current_game.dire = [
            {"name": "F"},
            {"name": "G"},
            {"name": "H"},
            {"name": "I"},
            {"name": "J"},
        ]

        await dpytest.message("!status")
        assert (
            dpytest.verify()
            .message()
            .content(
                "**Current Game** ```\nradiant    dire\n---------  ------\nA          F\nB          G\nC          H\nD          I\nE          J```"
            )
        )
