import asyncio
import logging
from traceback import print_exception

from discord.ext.commands import Bot
from discord.utils import setup_logging
from structlog import get_logger

from onehead.config import Config, load_config
from onehead.core import bot_builder


log: logging.Logger = get_logger()


async def main() -> None:
    config: Config = load_config()
    bot: Bot = await bot_builder(config)
    
    setup_logging(level=logging.INFO, root=True)
    
    loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
    loop.set_exception_handler(global_exception_handler)
    
    await bot.start(config.discord.token)


def global_exception_handler(_: asyncio.AbstractEventLoop, context: dict) -> None:
    message: str | None = context.get("message")
    if message:
        log.error(f"Caught exception: {message}")
    
    ex: Exception | None = context.get("exception")
    if ex:
        print_exception(ex)


if __name__ == "__main__":
    asyncio.run(main())
