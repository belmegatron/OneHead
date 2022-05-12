from asyncio import sleep
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
        self.betting_window_open = False
        self.snapshot = None
        self.bets = []

    def get_bet_results(self, radiant_won: bool) -> dict:

        bet_results = {}

        for bet in self.bets:
            name = bet["name"]

            if bet_results.get(name) is None:
                bet_results[name] = 0

            if (radiant_won and bet["side"] == "radiant") or (radiant_won is False and bet["side"] == "dire"):
                bet_results[name] += bet["stake"]
            else:
                bet_results[name] -= bet["stake"]

        return bet_results

    async def open_betting_window(self, ctx: commands.Context):
        table = self.database.retrieve_table()
        self.snapshot = {player["name"]: player["rbucks"] for player in table}
        self.betting_window_open = True

        await ctx.send("Bets are now open for 5 minutes!")
        await sleep(30)

        self.betting_window_open = False
        await ctx.send("Bets are now closed!")

    @commands.has_role("IHL")
    @commands.command(aliases=["bet"])
    async def place_bet(self, ctx: commands.Context, side: str, amount: str):
        """
        Place a bet on the match that is about to happen.

        e.g. !bet radiant 500 or !bet dire all
        """

        if self.betting_window_open is False:
            await ctx.send("Betting window closed.")
            return

        name = ctx.author.display_name

        available_balance = self.snapshot.get(name)

        if available_balance is None:
            await ctx.send(f"{name} cannot be found in the database.")
            return

        if side.lower() not in (RADIANT, DIRE):
            await ctx.send(f"{name} - Cannot bet on {side} - Must be either Radiant/Dire.")
            return

        if available_balance == 0:
            await ctx.send(f"{name} cannot bet as they have no available RBUCKS.")
            return

        if amount == "all":
            stake = available_balance
        else:
            try:
                stake = int(amount)
            except ValueError:
                await ctx.send(f"{name} - {amount} is not a valid number of RBUCKS to place a bet with.")
                return

        if stake <= 0:
            await ctx.send(f"{name} - Bet stake must be greater than 0.")
            return

        if stake > available_balance:
            await ctx.send(
                f"Unable to place bet - {name} tried to stake {stake} RBUCKS but only has {available_balance} RBUCKS available.")
            return

        self.snapshot[name] = available_balance - stake
        self.bets.append({"name": name, "side": side, "stake": stake})
        await ctx.send(f"{name} has placed a bet of {stake} RBUCKS on {side.title()}.")

    @commands.has_role("IHL")
    @commands.command(aliases=["rbucks"])
    async def bucks(self, ctx: commands.Context):
        """
        Lists the number of rbucks each member of the IHL has.
        """

        subset = []

        for name, rbucks in self.snapshot.items():
            subset.append({
                "name": name,
                "RBUCKS": rbucks}
            )

        subset = sorted(subset, key=lambda d: d['RBUCKS'], reverse=True)

        bucks_board = tabulate(
            subset, headers="keys", tablefmt="simple"
        )

        embed = Embed(title="**RBUCKS**", colour=colour.Colour.green())
        embed.add_field(name="Leaderboard", value=f"```{bucks_board}```")

        await ctx.send(embed=embed)
