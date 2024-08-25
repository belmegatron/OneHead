from datetime import datetime
from unittest.mock import AsyncMock, patch, Mock

import discord.ext.test as dpytest
import pytest
from conftest import add_ihl_role
from discord.ext.commands import Bot, errors

from onehead.betting import Bet
from onehead.common import OneHeadException, Player, Side, Team
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
        lobby._signups = {"BOB": datetime.now(), "BILL": datetime.now()}

        await dpytest.message("!start")
        assert dpytest.verify().message().content("Only `2` signup(s), require `8` more.")
    
    @pytest.mark.asyncio
    async def test_success(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")
        await add_ihl_role(bot, "IHL Admin")

        lobby: Lobby = bot.get_cog("Lobby")
        players: list[Player] = lobby.database.get_all()[:10]
        lobby._signups = {player["name"]: datetime.now() for player in players}

        core: Core = bot.get_cog("Core")
        balance: AsyncMock = AsyncMock()
        balance.return_value = [{"name": "foo"}, {"name": "foo"}, {"name": "foo"}, {"name": "foo"}, {"name": "foo"}], [
            {"name": "foo"},
            {"name": "foo"},
            {"name": "foo"},
            {"name": "foo"},
            {"name": "foo"},
        ]
        core.matchmaking.balance = balance
        core.setup_team_channels = AsyncMock()
        core.current_game.open_transfer_window = AsyncMock()
        core.current_game.open_betting_window = AsyncMock()

        with patch("onehead.core.play_sound"):
            await dpytest.message("!start")

        assert dpytest.verify().message().content("Starting game:").contains()
        assert dpytest.verify().message().content("**Current Game**").contains()
        assert dpytest.verify().message().content("Create Dota 2 Lobby and join with the above teams.")
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
        core.betting.refund_all_bets = AsyncMock()
        core.transfers.refund_transfers = AsyncMock()
        core.channels.move_back_to_lobby = AsyncMock()
        core.reset = AsyncMock()

        await dpytest.message("!stop")
        core.betting.refund_all_bets.assert_called()
        core.transfers.refund_transfers.assert_called()
        core.channels.move_back_to_lobby.assert_called()
        core.reset.assert_called()


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
            .content("Cannot enter result as the transfer window for the game is currently open")
            .contains()
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
            .content("Cannot enter result as the betting window for the game is currently open")
            .contains()
        )

    @pytest.mark.asyncio
    async def test_invalid_side(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL Admin")
        core: Core = bot.get_cog("Core")
        core.current_game._in_progress = True
        await dpytest.message("!result derp")
        assert dpytest.verify().message().content(f"Must be either {Side.RADIANT} or {Side.DIRE}.")

    @pytest.mark.asyncio
    async def test_invalid_team(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL Admin")
        core: Core = bot.get_cog("Core")
        core.current_game._in_progress = True

        core.channels.move_back_to_lobby = AsyncMock()

        with pytest.raises(OneHeadException):
            await dpytest.message(f"!result {Side.RADIANT}")

    @pytest.mark.asyncio
    async def test_success(self, bot: Bot) -> None:
        await dpytest.member_join(name="RBEEZAY")
        await add_ihl_role(bot, "IHL")
        await add_ihl_role(bot, "IHL Admin")
        core: Core = bot.get_cog("Core")
        current_game: Game = core.current_game
        current_game._in_progress = True
        current_game.radiant = [Player(name="RBEEZAY")]
        current_game.dire = []
        current_game._bets = [
            Bet(Side.RADIANT, 100, "RBEEZAY"),
            Bet(Side.DIRE, 500, "RBEEZAY"),
        ]

        core.scoreboard.scoreboard = AsyncMock()
        core.channels.move_back_to_lobby = AsyncMock()
        core.reset = AsyncMock()
        core.database.modify = Mock()

        with patch("onehead.core.play_sound"):
            await dpytest.message(f"!result {Side.RADIANT}")

        core.channels.move_back_to_lobby.assert_called_once()
        core.reset.assert_called_once()


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
        assert dpytest.verify().message().content("**Current Game**").contains()
