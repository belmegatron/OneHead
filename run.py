from onehead.core import bot_factory

if __name__ == "__main__":
    bot = bot_factory()
    core = bot.get_cog("OneHeadCore")
    bot.run(core.token)
