import asyncio

from discord.ext.commands import Bot

from onehead.core import Core, bot_factory


async def main() -> None:
    bot: Bot = await bot_factory()
    core: Core = bot.get_cog("Core")  # type: ignore[assignment]
    await bot.start(core.token)


if __name__ == "__main__":
    asyncio.run(main())
