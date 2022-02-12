from typing import TYPE_CHECKING
import random
from asyncio import sleep

from discord.ext import commands
from tabulate import tabulate

from onehead.common import OneHeadException

if TYPE_CHECKING:
    from onehead.db import OneHeadDB


class OneHeadRegistration(commands.Cog):
    def __init__(self, database: "OneHeadDB"):

        self.database = database

    @commands.has_role("IHL")
    @commands.command(aliases=["reg"])
    async def register(self, ctx: commands.Context, mmr: str):
        """
        Register yourself to the IHL by typing !register <your mmr>.
        """

        name = ctx.author.display_name

        try:
            int(mmr)
        except ValueError:
            raise OneHeadException(f"{mmr} is not a valid integer.")

        if self.database.player_exists(name) is False:
            self.database.add_player(ctx.author.display_name, mmr)
            await ctx.send(f"{name} successfully registered.")
        else:
            await ctx.send(f"{name} is already registered.")

    @commands.has_role("IHL Admin")
    @commands.command(aliases=["dereg"])
    async def deregister(self, ctx: commands.Context, name: str):
        """
        Removes a player from the internal IHL database.
        """

        if self.database.player_exists(name):
            self.database.remove_player(name)
            await ctx.send(f"{name} successfully removed from the database.")
        else:
            await ctx.send(f"{name} could not be found in the database.")


class OneHeadPreGame(commands.Cog):
    def __init__(self, database: "OneHeadDB"):

        self.database = database
        self.signups = []
        self.players_ready = []
        self.ready_check_in_progress = False

    @commands.has_role("IHL Admin")
    @commands.command()
    async def summon(self, ctx: commands.Context):
        """
        Messages all registered players of the IHL to come and sign up.
        """

        ihl_role = [x for x in ctx.guild.roles if x.name == "IHL"]
        if not ihl_role:
            return

        await ctx.send(f"IHL DOTA - LET'S GO! {ihl_role[0].mention}")

    def reset_state(self):
        self.signups = []

    async def signup_check(self, ctx: commands.Context) -> bool:

        signup_count = len(self.signups)
        if signup_count < 10:
            if signup_count == 0:
                await ctx.send("There are currently no signups.")
            else:
                await ctx.send(
                    f"Only {signup_count} Signup(s), require {10 - signup_count} more."
                )
        else:
            return True

        return False

    async def handle_signups(self, ctx: commands.Context):
        """
        Handle the case where there are less than 10 signups, exactly 10 signups or more than 10 signups. If there are
        more, then players will be randomly removed until there are only 10 players in self.signups.

        :param ctx: Discord context
        """

        number_of_signups = len(self.signups)
        if number_of_signups <= 10:
            return

        benched_players = []
        await ctx.send(
            f"{number_of_signups} Players have signed up and therefore {number_of_signups - 10} players will be benched."
        )
        while len(self.signups) > 10:
            idx = self.signups.index(random.choice(self.signups))
            random_selection = self.signups.pop(idx)
            benched_players.append(random_selection)

        await ctx.send(f"**Benched Players:** ```\n{benched_players}```")
        await ctx.send(f"**Selected Players:** ```\n{self.signups}```")

    @commands.has_role("IHL")
    @commands.command()
    async def who(self, ctx: commands.Context):
        """
        Shows all players currently signed up to play in the IHL.
        """

        await ctx.send(
            f"There are currently {len(self.signups)} players signed up."
        )
        signups_dict = [
            {"#": i + 1, "name": name} for i, name in enumerate(self.signups)
        ]
        signups = tabulate(signups_dict, headers="keys", tablefmt="simple")

        await ctx.send(f"**Current Signups** ```\n{signups}```")

    @commands.has_role("IHL")
    @commands.command(aliases=["su"])
    async def signup(self, ctx: commands.Context):
        """
        Signup to join a game in the IHL.
        """

        name = ctx.author.display_name
        if self.database.player_exists(name) is False:
            await ctx.send("Please register first using the !reg command.")
            return

        if name in self.signups:
            await ctx.send(f"{name} is already signed up.")
        else:
            self.signups.append(name)

        await commands.Command.invoke(self.who, ctx)

    @commands.has_role("IHL")
    @commands.command(aliases=["so"])
    async def signout(self, ctx: commands.Context):
        """
        Remove yourself from the current pool of signed up players.
        """
        if ctx.author.display_name not in self.signups:
            await ctx.send(
                f"{ctx.author.display_name} is not currently signed up."
            )
        else:
            self.signups.remove(ctx.author.display_name)

        await commands.Command.invoke(self.who, ctx)

    @commands.has_role("IHL Admin")
    @commands.command(aliases=["rm"])
    async def remove(self, ctx: commands.Context, name: str):
        """
        Remove a player who is currently signed up.
        """

        if name not in self.signups:
            await ctx.send(f"{name} is not currently signed up.")
            return

        self.signups.remove(name)
        await ctx.send(f"{name} has been removed from the signup pool.")

    @commands.has_role("IHL")
    @commands.command(aliases=["r"])
    async def ready(self, ctx: commands.Context):
        """
        Use this command in response to a ready check.
        """
        name = ctx.author.display_name

        if name not in self.signups:
            await ctx.send(f"{name} needs to sign in first.")
            return

        if self.ready_check_in_progress is False:
            await ctx.send("No ready check initiated.")
            return

        self.players_ready.append(name)
        await ctx.send(f"{name} is ready.")

    @commands.has_role("IHL")
    @commands.command(aliases=["rc"])
    async def ready_check(self, ctx: commands.Context):
        """
        Initiates a ready check, after approx. 30s the result of the check will be displayed.
        """
        if await self.signup_check(ctx):
            await ctx.send(
                "Ready Check Started, 30s remaining - type '!ready' to ready up."
            )
            self.ready_check_in_progress = True
            await sleep(30)
            players_ready_count = len(self.players_ready)
            players_not_ready = " ,".join(
                [x for x in self.signups if x not in self.players_ready]
            )
            if players_ready_count == 10:
                await ctx.send("Ready Check Complete - All players ready.")
            else:
                await ctx.send(
                    f"Still waiting on {10 - players_ready_count} players: {players_not_ready}"
                )

        self.ready_check_in_progress = False
        self.players_ready = []
