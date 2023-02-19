import pytest
from typing import Sequence

from discord.ext.commands import Bot, errors
import discord.ext.test as dpytest
from discord.guild import Guild
from discord.role import Role

from conftest import add_ihl_role


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
