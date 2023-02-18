import pytest_asyncio
from typing import Generator, Sequence

from discord.ext.commands import Bot
import discord.ext.test as dpytest
from discord.guild import Guild
from discord.member import Member
from discord.role import Role


from onehead.core import bot_factory


@pytest_asyncio.fixture
async def bot() -> Bot:
    bot: Bot = await bot_factory()
    await bot._async_setup_hook()
    dpytest.configure(bot)
    
    # Create the roles that are used by OneHead.
    guilds: Sequence[Guild] = bot.guilds
    guild: Guild = guilds[0]
    await guild.create_role(name="IHL")
    await guild.create_role(name="IHL Admin")
    return bot
    

@pytest_asyncio.fixture(autouse=True)
async def cleanup() -> Generator[None, None, None]:
    yield
    await dpytest.empty_queue()
    

async def add_ihl_role(bot: Bot, role: str) -> None:
    guilds: Sequence[Guild] = bot.guilds
    guild: Guild = guilds[0]
    members: list[Member] = list(bot.get_all_members())
    
    roles: Sequence[Role] = guild.roles
    ihl_role: Role = [x for x in roles if x.name == role][0]
    await dpytest.add_role(members[0], ihl_role)