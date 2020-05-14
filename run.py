from dotenv import load_dotenv
import os
from discord.ext import commands
from src.onehead_core import OneHeadCore


if __name__ == "__main__":

    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    bot = commands.Bot(command_prefix='!')

    bot.add_cog(OneHeadCore(bot))

    bot.run(TOKEN)
