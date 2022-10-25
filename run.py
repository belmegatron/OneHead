from onehead.common import setup_log
from onehead.core import bot_factory

if __name__ == "__main__":
    bot = bot_factory()
    core = bot.get_cog("OneHeadCore")
    setup_log()
    bot.run(core.token)
