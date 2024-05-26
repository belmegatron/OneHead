from datetime import datetime
from typing import Sequence
from unittest.mock import AsyncMock, Mock, patch

import discord.ext.test as dpytest
import pytest
from conftest import TEST_USER, add_ihl_role
from discord.ext.commands import Bot, errors
from discord.guild import Guild
from discord.role import Role

import onehead.lobby
from onehead.lobby import Lobby


class TestSummon:
    @pytest.mark.asyncio
    async def test_no_ihl_admin_role(self, bot: Bot) -> None:
        with pytest.raises(errors.MissingRole):
            await dpytest.message("!summon")

    @pytest.mark.asyncio
    async def test_no_active_game(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL Admin")

        guilds: Sequence[Guild] = bot.guilds
        guild: Guild = guilds[0]
        roles: Sequence[Role] = guild.roles
        ihl_role: Role = [x for x in roles if x.name == "IHL"][0]

        await dpytest.message("!summon")
        assert dpytest.verify().message().content(f"IHL DOTA - LET'S GO! {ihl_role.mention}")


class TestSignup:
    @pytest.mark.asyncio
    async def test_no_ihl_role(self, bot: Bot) -> None:
        with pytest.raises(errors.MissingRole):
            await dpytest.message("!su")

    @pytest.mark.asyncio
    async def test_signups_disabled(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")

        lobby: Lobby = bot.get_cog("Lobby")
        lobby._signups_disabled = True

        await dpytest.message("!su")
        assert dpytest.verify().message().content("Game in progress").contains()

    @pytest.mark.asyncio
    async def test_player_not_registered(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")

        lobby: Lobby = bot.get_cog("Lobby")
        lobby._signups_disabled = False

        await dpytest.message("!su")
        assert dpytest.verify().message().content("Please register first using the `!register` command.")

    @pytest.mark.asyncio
    async def test_player_already_signed_up(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")

        lobby: Lobby = bot.get_cog("Lobby")
        lobby._signups_disabled = False
        lobby._signups[TEST_USER] = datetime.now()

        lobby.database.get = Mock()
        lobby.database.get.return_value = {"name": TEST_USER}

        await dpytest.message("!su")
        assert dpytest.verify().message().content(f"is already signed up.").contains()

    @pytest.mark.asyncio
    async def test_success(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")

        lobby: Lobby = bot.get_cog("Lobby")
        lobby._signups_disabled = False

        lobby.database.get = Mock()
        lobby.database.get.return_value = {"name": TEST_USER}

        await dpytest.message("!su")
        assert len(lobby.get_signups()) == 1


class TestSignout:
    @pytest.mark.asyncio
    async def test_no_ihl_role(self, bot: Bot) -> None:
        with pytest.raises(errors.MissingRole):
            await dpytest.message("!so")

    @pytest.mark.asyncio
    async def test_game_in_progress(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")
        lobby: Lobby = bot.get_cog("Lobby")
        lobby._signups_disabled = True
        await dpytest.message("!so")
        assert dpytest.verify().message().content("Game in progress").contains()

    @pytest.mark.asyncio
    async def test_not_signed_in(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")
        await dpytest.message("!so")
        assert dpytest.verify().message().content(f"is not currently signed up.").contains()

    @pytest.mark.asyncio
    async def test_success(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")
        lobby: Lobby = bot.get_cog("Lobby")
        lobby._signups[TEST_USER] = datetime.now()
        await dpytest.message("!so")
        assert len(lobby.get_signups()) == 0


class TestRemove:
    @pytest.mark.asyncio
    async def test_no_ihl_role(self, bot: Bot) -> None:
        with pytest.raises(errors.MissingRole):
            await dpytest.message("!rm RBEEZAY")

    @pytest.mark.asyncio
    async def test_not_signed_in(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL Admin")
        await dpytest.message("!rm RBEEZAY")
        assert dpytest.verify().message().content("RBEEZAY is not currently signed up.")

    @pytest.mark.asyncio
    async def test_success(self, bot: Bot) -> None:
        await dpytest.member_join(name="RBEEZAY")
        await add_ihl_role(bot, "IHL Admin")
        lobby: Lobby = bot.get_cog("Lobby")
        lobby._signups["RBEEZAY"] = datetime.now()
        await dpytest.message("!rm RBEEZAY")
        assert dpytest.verify().message().content("has been removed from the signup pool.").contains()


class TestReady:
    @pytest.mark.asyncio
    async def test_no_ihl_role(self, bot: Bot) -> None:
        with pytest.raises(errors.MissingRole):
            await dpytest.message("!ready")

    @pytest.mark.asyncio
    async def test_not_signed_in(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")
        await dpytest.message("!ready")
        assert dpytest.verify().message().content(f"needs to sign in first.").contains()

    @pytest.mark.asyncio
    async def test_ready_check_not_in_progress(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")
        lobby: Lobby = bot.get_cog("Lobby")
        lobby._signups[TEST_USER] = datetime.now()
        await dpytest.message("!ready")
        assert dpytest.verify().message().content("No ready check initiated.")

    @pytest.mark.asyncio
    async def test_success(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")
        lobby: Lobby = bot.get_cog("Lobby")
        lobby._signups[TEST_USER] = datetime.now()
        lobby._ready_check_in_progress = True
        await dpytest.message("!ready")
        assert dpytest.verify().message().content(f"is ready.").contains()


class TestReadyCheck:
    @pytest.mark.asyncio
    async def test_no_ihl_role(self, bot: Bot) -> None:
        with pytest.raises(errors.MissingRole):
            await dpytest.message("!ready_check")

    @pytest.mark.asyncio
    async def test_not_enough_signups(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")
        lobby: Lobby = bot.get_cog("Lobby")
        lobby._signups[TEST_USER] = datetime.now()
        await dpytest.message("!ready_check")
        assert dpytest.verify().message().content("Only `1` signup(s), require `9` more.")

    @pytest.mark.asyncio
    async def test_waiting_on_players(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")
        lobby: Lobby = bot.get_cog("Lobby")
        lobby._signups = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K"]
        lobby._players_ready = ["A", "B", "C", "D"]
        onehead.lobby.sleep = AsyncMock()

        for signup in lobby._signups:
            await dpytest.member_join(name=signup)

        with patch("onehead.lobby.play_sound"):
            await dpytest.message("!ready_check")

        assert dpytest.verify().message().content("Ready check started").contains()
        assert dpytest.verify().message().content("Still waiting on `7` players").contains()
        assert lobby._ready_check_in_progress is False
        assert lobby._players_ready == []

    @pytest.mark.asyncio
    async def test_success(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")
        lobby: Lobby = bot.get_cog("Lobby")
        lobby._signups = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
        lobby._players_ready = lobby._signups
        onehead.lobby.sleep = AsyncMock()

        for signup in lobby._signups:
            await dpytest.member_join(name=signup)

        with patch("onehead.lobby.play_sound"):
            await dpytest.message("!ready_check")

        assert dpytest.verify().message().content("Ready check started").contains()
        assert dpytest.verify().message().content("Ready check complete.").contains()
        assert lobby._ready_check_in_progress is False
        assert lobby._players_ready == []
