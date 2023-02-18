import asyncio

from discord.ext.commands import Bot, Cog

from onehead.core import bot_factory

async def main() -> None:
    bot: Bot = await bot_factory()
    core: Cog = bot.get_cog("Core")
    await bot.start(core.token)


if __name__ == "__main__":
    asyncio.run(main())
