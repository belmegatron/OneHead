import os
import time
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix='!')


class OneHead(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.game_in_progress = False
        self.is_balanced = False
        self.discord_uid_steamid_map = {}
        self.signups = []

        self.radiant = []
        self.dire = []

    def reset_state(self):

        self.game_in_progress = False
        self.is_balanced = False
        self.signups = []
        self.radiant = []
        self.dire = []

    @commands.command()
    async def start(self, ctx):

        if self.game_in_progress:
            await ctx.send("Game already in progress...")
            return

        if self.is_balanced is False:
            await self.balance(ctx)

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
            self.reset_state()
        else:
            await ctx.send("No currently active game.")

    async def balance(self, ctx):
        await ctx.send("Balancing teams...")
        # TODO: Calculate how to balance teams based on DB entries.
        self.is_balanced = True

    @commands.command()
    async def result(self, ctx, side):
        if self.game_in_progress is False:
            await ctx.send("No currently active game.")

        sides = ["Radiant", "Dire"]

        if side not in sides:
            await ctx.send("Invalid Value - Must be either 'Radiant' or 'Dire'.")
            return

        await ctx.send("{} Victory!".format(side))
        # TODO: Update DB
        await ctx.send("Updating Scores...")
        self.reset_state()

    @commands.command()
    async def leaderboard(self, ctx):
        await ctx.send("Current IGC Leaderboard:")

    @commands.command()
    async def register(self, ctx, steam_id):

        #   TODO: Sanity check steam_id.

        if not steam_id:
            await ctx.send("Please supply 64bit SteamID.")
            return

        if ctx.author.display_name not in self.discord_uid_steamid_map.keys():
            self.discord_uid_steamid_map[ctx.author.display_name] = steam_id
            await ctx.send("Successfully Registered.")
        else:
            await ctx.send("Already registered.")

    @commands.command()
    async def deregister(self, ctx):

        if ctx.author.display_name in self.discord_uid_steamid_map.keys():
            self.discord_uid_steamid_map.pop(ctx.author.display_name)
            await ctx.send("Successfully Deregistered.")
        else:
            await ctx.send("Discord Name could not be found.")

    @commands.command()
    async def signup(self, ctx):
        if ctx.author.display_name in self.signups:
            await ctx.send("{} is already signed up.".format(ctx.author.display_name))
        elif len(self.signups) >= 10:
            ctx.send("Signups full.")
        else:
            self.signups.append(ctx.author.display_name)

        await ctx.send("Current Signups: {}".format(self.signups))

    @commands.command()
    async def signout(self, ctx):
        if ctx.author.display_name not in self.signups:
            await ctx.send("{} is not currently signed up.".format(ctx.author.display_name))
        else:
            self.signups.remove(ctx.author.display_name)

        await ctx.send("Current Signups: {}".format(self.signups))


bot.add_cog(OneHead(bot))
bot.run(TOKEN)
