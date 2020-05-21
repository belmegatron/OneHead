from discord.ext import commands
from src.onehead_core import OneHeadCore


if __name__ == "__main__":

    bot = commands.Bot(command_prefix='!')
    onehead = OneHeadCore(bot)
    bot.add_cog(onehead)
    TOKEN = onehead.config["discord"]["token"]
    bot.run(TOKEN)
