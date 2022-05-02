from typing import TYPE_CHECKING

from discord import Embed, colour
from discord.ext import commands
from tabulate import tabulate

from onehead.common import RADIANT, DIRE

if TYPE_CHECKING:
    from onehead.db import OneHeadDB


class OneHeadBetting(commands.Cog):
    def __init__(self, database: "OneHeadDB"):
        self.database = database
        self.bets = []
        self.in_play = False

    @commands.has_role("IHL")
    @commands.command(aliases=["derp"])
    async def _update_post_match_result(self, ctx: commands.Context, radiant_won: bool):
        retStr = str("""```css\nThis is some colored Text```""")
        embed = Embed(title="Random test", colour=colour.Colour.teal())
        embed.add_field(name="Name field can't be colored as it seems", value=retStr)
        await ctx.send(embed=embed)

    @commands.has_role("IHL")
    @commands.command(aliases=["bet"])
    async def place_bet(self, ctx: commands.Context, side: str, amount: str):
        """
        Place a bet on the match that is about to happen.
        """

        name = ctx.author.display_name

        if self.database.player_exists(name) is False:
            await ctx.send(f"{name} cannot be found in the database.")
            return

        if side.lower() not in (RADIANT, DIRE):
            await ctx.send(f"Cannot bet on {side} - Must be either Radiant/Dire.")
            return

        try:
            stake = int(amount)
        except ValueError:
            await ctx.send(f"{amount} is not a valid number of rbucks to place a bet with.")
            return

        profile = self.database.lookup_player(name)
        balance = profile.get("rbucks", 0)
        if stake > balance:
            await ctx.send(f"Unable to place bet - tried to stake {stake} rbucks but only {balance} rbucks available.")
            return

        self.bets.append({"name": name, "side": side, "stake": stake})
        await ctx.send(f"{name} has placed a bet of {stake} rbucks on {side.title()}.")

    @commands.has_role("IHL")
    @commands.command()
    async def balance(self, ctx: commands.Context):
        """
        Displays current balance of rbucks.
        """
        name = ctx.author.display_name
        profile = self.database.lookup_player(name)
        balance = profile.get("rbucks", 0)
        await ctx.send(f"{name} currently has a balance of {balance} rbucks.")

    @commands.has_role("IHL")
    @commands.command(aliases=["bets"])
    async def list_bets(self, ctx: commands.Context):
        """
        List all active matched bets.
        """
        pass

    @commands.has_role("IHL")
    @commands.command()
    async def bucks(self, ctx: commands.Context):
        """
        Lists the number of rbucks each member of the IHL has.
        """

        scoreboard = self.database.retrieve_table()

        subset = []

        for profile in scoreboard:
            subset.append({
                "name": profile["name"],
                "rbucks": profile["rbucks"]}
            )

        subset = sorted(subset, key=lambda d: d['rbucks'], reverse=True)

        bucks_board = tabulate(
            subset, headers="keys", tablefmt="simple"
        )

        embed = Embed(title="**RBUCKS**", colour=colour.Colour.green())
        embed.add_field(name="Leaderboard", value=f"```{bucks_board}```")

        await ctx.send(embed=embed)
