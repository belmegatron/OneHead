from discord.ext.commands import Bot, Cog

from onehead.common import setup_log
from onehead.core import bot_factory


if __name__ == "__main__":
    
    bot: Bot = bot_factory()
    core: Cog = bot.get_cog("OneHeadCore")
    setup_log()
    bot.run(core.token)
