from discord.ext.commands import Bot, Cog

from onehead.core import bot_factory

if __name__ == "__main__":

    bot: Bot = bot_factory()
    core: Cog = bot.get_cog("Core")
    bot.run(core.token)
