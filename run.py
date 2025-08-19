import asyncio
import logging

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

    await bot.start(config.discord.token)


if __name__ == "__main__":
    asyncio.run(main())
