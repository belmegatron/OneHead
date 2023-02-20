import pytest
from typing import Sequence
from unittest.mock import Mock

from discord.ext.commands import Bot, errors
import discord.ext.test as dpytest
from discord.guild import Guild
from discord.role import Role

from onehead.lobby import Lobby

from conftest import add_ihl_role, TEST_USER


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
        assert dpytest.verify().message().content("Game in Progress - Signup command unavailable.")
    
    @pytest.mark.asyncio
    async def test_player_not_registered(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")
        
        lobby: Lobby = bot.get_cog("Lobby")
        lobby._signups_disabled = False

        await dpytest.message("!su")
        assert dpytest.verify().message().content("Please register first using the !reg command.")
    
    @pytest.mark.asyncio
    async def test_player_already_signed_up(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")
        
        lobby: Lobby = bot.get_cog("Lobby")
        lobby._signups_disabled = False
        lobby._signups.append(TEST_USER)
        
        lobby.database.player_exists = Mock()
        lobby.database.player_exists.return_value = True, 0

        await dpytest.message("!su")
        assert dpytest.verify().message().content(f"{TEST_USER} is already signed up.")
        
    @pytest.mark.asyncio
    async def test_success(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")
        
        lobby: Lobby = bot.get_cog("Lobby")
        lobby._signups_disabled = False
        
        lobby.database.player_exists = Mock()
        lobby.database.player_exists.return_value = True, 0

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
        assert dpytest.verify().message().content("Game in Progress - Signout command unavailable.")
    
    @pytest.mark.asyncio
    async def test_not_signed_in(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")
        await dpytest.message("!so")
        assert dpytest.verify().message().content(f"{TEST_USER} is not currently signed up.")
    
    @pytest.mark.asyncio
    async def test_success(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")
        lobby: Lobby = bot.get_cog("Lobby")
        lobby._signups.append(TEST_USER)
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
        await add_ihl_role(bot, "IHL Admin")
        lobby: Lobby = bot.get_cog("Lobby")
        lobby._signups.append("RBEEZAY")
        await dpytest.message("!rm RBEEZAY")
        assert dpytest.verify().message().content("RBEEZAY has been removed from the signup pool.")


class TestReady:
    @pytest.mark.asyncio
    async def test_no_ihl_role(self, bot: Bot) -> None:
        with pytest.raises(errors.MissingRole):
            await dpytest.message("!ready")
    
    @pytest.mark.asyncio
    async def test_not_signed_in(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")
        await dpytest.message("!ready")
        assert dpytest.verify().message().content(f"{TEST_USER} needs to sign in first.")
    
    @pytest.mark.asyncio
    async def test_ready_check_not_in_progress(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")
        lobby: Lobby = bot.get_cog("Lobby")
        lobby._signups.append(TEST_USER)
        await dpytest.message("!ready")
        assert dpytest.verify().message().content("No ready check initiated.")
    
    @pytest.mark.asyncio
    async def test_success(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")
        lobby: Lobby = bot.get_cog("Lobby")
        lobby._signups.append(TEST_USER)
        lobby.ready_check_in_progress = True
        await dpytest.message("!ready")
        assert dpytest.verify().message().content(f"{TEST_USER} is ready.")


class TestReadyCheck:
    @pytest.mark.asyncio
    async def test_no_ihl_role(self, bot: Bot) -> None:
        with pytest.raises(errors.MissingRole):
            await dpytest.message("!ready_check")
