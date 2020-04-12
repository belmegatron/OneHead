from discord.ext import commands
from asyncio import sleep
from onehead_common import OneHeadException


class OneHeadRegistration(commands.Cog):

    def __init__(self, database):

        self.database = database

    @commands.command(aliases=['reg'])
    async def register(self, ctx, mmr):
        """
        Register yourself to the IHL by typing !register <your mmr>.
        """

        name = ctx.author.display_name

        try:
            tmp = int(mmr)
        except ValueError:
            raise OneHeadException("{} is not a valid integer.".format(mmr))

        if self.database.player_exists(name) is False:
            self.database.add_player(ctx.author.display_name, mmr)
            await ctx.send("{} successfully registered.".format(name))
        else:
            await ctx.send("{} is already registered.".format(name))

    @commands.has_permissions(administrator=True)
    @commands.command(aliases=['dereg'])
    async def deregister(self, ctx):
        """
        Removes a player from the internal IHL database.
        """

        name = ctx.author.display_name

        if self.database.player_exists(name):
            self.database.remove_player(name)
            await ctx.send("Successfully Deregistered.")
        else:
            await ctx.send("Discord Name could not be found.")


class OneHeadPreGame(commands.Cog):

    def __init__(self, database):

        self.database = database
        self.signups = []
        self.players_ready = []
        self.ready_check_in_progress = False

    @commands.has_role("IHL Admin")
    @commands.command()
    async def summon(self, ctx):
        """
        Messages all registered players of the IHL to come and sign up.
        """

        all_registered_players = self.database.retrieve_table()
        if not all_registered_players:
            raise OneHeadException("No players could be found in database.")

        names = [x['name'] for x in all_registered_players]
        members = [x for x in ctx.guild.members if x.display_name in names]
        mentions = " ".join([x.mention for x in members])
        message = "IT'S DOTA TIME BOYS! Summoning all 1Heads - {}".format(mentions)
        await ctx.send(message)

    def clear_signups(self):
        self.signups = []

    async def signup_check(self, ctx):

        signups_full = False
        signup_count = len(self.signups)
        if signup_count != 10:
            if signup_count == 0:
                await ctx.send("There are currently no signups.")
            elif signup_count == 1:
                await ctx.send("Only {} Signup, require {} more.".format(signup_count, 10 - signup_count))
            else:
                await ctx.send("Only {} Signups, require {} more.".format(signup_count, 10 - signup_count))
        else:
            signups_full = True

        return signups_full

    @commands.command()
    async def who(self, ctx):
        """
        Shows all players currently signed up to play in the IHL.
        """

        await ctx.send("There are currently {} players signed up.".format(len(self.signups)))
        await ctx.send("Current Signups: {}".format(self.signups))

    @commands.has_role("IHL Admin")
    @commands.command()
    async def reset(self, ctx):
        """
        Reset current sign ups.
        """

        self.clear_signups()
        await ctx.send("Signups have been reset.")

    @commands.command(aliases=['su'])
    async def signup(self, ctx):
        """
        Signup to join a game in the IHL.
        """

        name = ctx.author.display_name
        if self.database.player_exists(name) is False:
            await ctx.send("Please register first using the !reg command.")
            return

        if name in self.signups:
            await ctx.send("{} is already signed up.".format(name))
        elif len(self.signups) >= 10:
            await ctx.send("Signups full.")
        else:
            self.signups.append(name)

        await ctx.send("Current Signups: {}".format(self.signups))

    @commands.command(aliases=['so'])
    async def signout(self, ctx):
        """
        Remove yourself from the current pool of signed up players.
        """
        if ctx.author.display_name not in self.signups:
            await ctx.send("{} is not currently signed up.".format(ctx.author.display_name))
        else:
            self.signups.remove(ctx.author.display_name)

        await ctx.send("Current Signups: {}".format(self.signups))

    @commands.has_role("IHL Admin")
    @commands.command(aliases=['rm'])
    async def remove(self, ctx, name):
        """
        Remove a player who is currently signed up.
        """

        if name not in self.signups:
            await ctx.send("{} is not currently signed up.".format(name))
            return

        self.signups.remove(name)
        ctx.send("{} has been removed from the signup pool.".format(name))

    @commands.command(aliases=['r'])
    async def ready(self, ctx):
        """
        Use this command in response to a ready check.
        """
        name = ctx.author.display_name

        if name not in self.signups:
            await ctx.send("{} needs to sign in first.".format(name))
            return

        if self.ready_check_in_progress is False:
            await ctx.send("No ready check initiated.")
            return

        self.players_ready.append(name)
        await ctx.send("{} is ready.".format(name))

    @commands.command(aliases=['rc'])
    async def ready_check(self, ctx):
        """
        Initiates a ready check, after approx. 30s the result of the check will be displayed.
        """
        if await self.signup_check(ctx):
            await ctx.send("Ready Check Started, 30s remaining - type '!ready' to ready up.")
            self.ready_check_in_progress = True
            await sleep(30)
            players_ready_count = len(self.players_ready)
            players_not_ready = " ,".join([x for x in self.signups if x not in self.players_ready])
            if players_ready_count == 10:
                await ctx.send("Ready Check Complete - All players ready.")
            else:
                await ctx.send("Still waiting on {} players: {}".format(10 - players_ready_count, players_not_ready))

        self.ready_check_in_progress = False
        self.players_ready = []
