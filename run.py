import asyncio
import logging

from discord.ext.commands import Bot
from discord.utils import setup_logging

from onehead.core import Core, bot_factory


handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')


async def main() -> None:
    bot: Bot = await bot_factory()
    core: Core = bot.get_cog("Core")  # type: ignore[assignment]
    setup_logging(level=logging.INFO, root=False, handler=handler)
    await bot.start(core.token)


if __name__ == "__main__":
    asyncio.run(main())
