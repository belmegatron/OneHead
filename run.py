from discord.ext import commands
from onehead.core import OneHeadCore

from onehead.balance import OneHeadBalance, OneHeadCaptainsMode
from onehead.scoreboard import OneHeadScoreBoard
from onehead.db import OneHeadDB
from onehead.common import OneHeadCommon
from onehead.channels import OneHeadChannels
from onehead.user import OneHeadPreGame, OneHeadRegistration

if __name__ == "__main__":

    bot = commands.Bot(command_prefix='!')
    config = OneHeadCommon.load_config()

    database = OneHeadDB(config)
    scoreboard = OneHeadScoreBoard(database)
    pre_game = OneHeadPreGame(database)
    team_balance = OneHeadBalance(database, pre_game, config)
    captains_mode = OneHeadCaptainsMode(database, pre_game)
    channels = OneHeadChannels(config)
    registration = OneHeadRegistration(database)

    bot.add_cog(database)
    bot.add_cog(pre_game)
    bot.add_cog(scoreboard)
    bot.add_cog(registration)
    bot.add_cog(captains_mode)
    bot.add_cog(team_balance)
    bot.add_cog(channels)

    # Add cogs first, then instantiate OneHeadCore as we reference them as instance variables
    onehead = OneHeadCore(bot)
    bot.add_cog(onehead)

    TOKEN = onehead.config["discord"]["token"]
    bot.run(TOKEN)
