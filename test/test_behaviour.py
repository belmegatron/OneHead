import pytest
import pytest_asyncio
from discord import Intents
from discord.ext.commands import Bot, Cog, Command, Context
import discord.ext.test as dpytest


from onehead.behaviour import Behaviour
from onehead.common import load_config
from onehead.core import bot_factory
from onehead.database import Database


@pytest_asyncio.fixture
async def bot() -> Bot:
    intents: Intents = Intents.default()
    intents.members = True
    intents.message_content = True
    b: Bot = Bot(command_prefix="!", intents=intents)
    await b._async_setup_hook()  # setup the loop
    await b.add_cog(Behaviour(Database(load_config())))
    dpytest.configure(b)
    return b

@pytest.mark.asyncio
async def test_ping(bot) -> None:
    await dpytest.message("!commend")
    assert dpytest.verify().message().content("Pong !")
