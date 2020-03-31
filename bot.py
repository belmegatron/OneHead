import os
import time
from dotenv import load_dotenv
from discord.ext import commands
import discord

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix='!')


class OneHead(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.game_in_progress = False

    @commands.command()
    async def join(self, ctx):
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send("1Head IGC IHL Bot reporting for duty sir...")

    @commands.command()
    async def leave(self, ctx):
        await ctx.voice_client.disconnect()

    @commands.command()
    async def start(self, ctx):

        if self.game_in_progress:
            await ctx.send("Game already in progress...")
            return

        await ctx.send("Game starting in ...")
        for second in range(3, 0, -1):
            await ctx.send("{}".format(second))
            time.sleep(1)
        await ctx.send("Go!")
        self.game_in_progress = True

    @commands.command()
    async def stop(self, ctx):
        if self.game_in_progress:
            await ctx.send("Game stopped.")
            self.game_in_progress = False
        else:
            await ctx.send("No currently active game.")

    @commands.command()
    async def balance(self, ctx):
        await ctx.send("Balancing teams...")

    @commands.command()
    async def result(self, ctx, side):
        if self.game_in_progress is False:
            await ctx.send("No currently active game.")

        sides = ["Radiant", "Dire"]

        if side not in sides:
            await ctx.send("Invalid Value - Must be either 'Radiant' or 'Dire'.")
            return

        await ctx.send("{} Victory!".format(side))
        await ctx.send("Updating Scores...")

    @commands.command()
    async def leaderboard(self, ctx):
        await ctx.send("Current IGC Leaderboard:")


bot.add_cog(OneHead(bot))
bot.run(TOKEN)
