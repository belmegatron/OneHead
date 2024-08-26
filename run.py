import asyncio
import logging
from traceback import print_exception

from discord.ext.commands import Bot
from discord.utils import setup_logging

from onehead.core import Core, bot_factory


handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")


async def main() -> None:
    bot: Bot = await bot_factory()
    core: Core = bot.get_cog("Core")  # type: ignore[assignment]
    setup_logging(level=logging.INFO, root=False, handler=handler)
    loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
    loop.set_exception_handler(global_exception_handler)
    await bot.start(core.token)

def global_exception_handler(_: asyncio.AbstractEventLoop, context: dict) -> None:
    ex: Exception | None = context.get('exception')
    if ex:
        print_exception(ex)

if __name__ == "__main__":
    asyncio.run(main())
