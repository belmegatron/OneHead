import asyncio
from typing import TYPE_CHECKING

from discord import Embed, colour
from discord.ext import commands
from tabulate import tabulate

from onehead.common import DIRE, RADIANT, OneHeadException, OneHeadRoles

if TYPE_CHECKING:
    from onehead.common import Player
    from onehead.db import OneHeadDB
    from onehead.user import OneHeadPreGame


class OneHeadBetting(commands.Cog):
    def __init__(self, database: "OneHeadDB", pre_game: "OneHeadPreGame") -> None:

        self.database: OneHeadDB = database
        self.betting_window_open: bool = False
        self.bets: list[dict] = []
        self.pre_game: OneHeadPreGame = pre_game

    def get_bet_results(self, radiant_won: bool) -> dict:

        bet_results: dict[str, float] = {}

        for bet in self.bets:
            name: str = bet["name"]

            if bet_results.get(name) is None:
                bet_results[name] = 0

            if (radiant_won and bet["side"] == "radiant") or (
                radiant_won is False and bet["side"] == "dire"
            ):
                bet_results[name] += bet["stake"] * 2.0
            else:
                bet_results[name] -= bet["stake"]

        return bet_results

    async def open_betting_window(
        self, ctx: commands.Context, event: asyncio.Event
    ) -> None:
        self.betting_window_open = True

        await ctx.send(f"Bets are now open for 5 minutes!")

        try:
            await asyncio.wait_for(event.wait(), timeout=240)
        except asyncio.TimeoutError:
            await ctx.send("1 minute remaining for bets!")
            try:
                await asyncio.wait_for(event.wait(), timeout=60)
            except asyncio.TimeoutError:
                pass
        finally:
            self.betting_window_open = False
            await ctx.send("Bets are now closed!")

    @commands.has_role(OneHeadRoles.MEMBER)
    @commands.command(aliases=["bet"])
    async def place_bet(self, ctx: commands.Context, side: str, amount: str) -> None:
        """
        Place a bet on the match that is about to happen.

        e.g. !bet radiant 500 or !bet dire all
        """

        if self.betting_window_open is False:
            await ctx.send("Betting window closed.")
            return

        name: str = ctx.author.display_name

        try:
            record: Player = self.database.lookup_player(name)
        except OneHeadException:
            await ctx.send(f"Unable to find player in database")
            return

        available_balance: int = record["rbucks"]

        if available_balance is None:
            await ctx.send(f"{name} cannot be found in the database.")
            return

        if side.lower() not in (RADIANT, DIRE):
            await ctx.send(
                f"{name} - Cannot bet on {side} - Must be either Radiant/Dire."
            )
            return

        if available_balance == 0:
            await ctx.send(f"{name} cannot bet as they have no available RBUCKS.")
            return

        if amount == "all":
            stake: int = available_balance
        else:
            try:
                stake = int(amount)
            except ValueError:
                await ctx.send(
                    f"{name} - {amount} is not a valid number of RBUCKS to place a bet with."
                )
                return

        if stake <= 0:
            await ctx.send(f"{name} - Bet stake must be greater than 0.")
            return

        if stake > available_balance:
            await ctx.send(
                f"Unable to place bet - {name} tried to stake {stake} RBUCKS but only has {available_balance} RBUCKS available."
            )
            return

        self.bets.append({"name": name, "side": side, "stake": stake})
        self.database.update_rbucks(name, -stake)

        await ctx.send(f"{name} has placed a bet of {stake} RBUCKS on {side.title()}.")

    @commands.has_role(OneHeadRoles.MEMBER)
    @commands.command(aliases=["rbucks"])
    async def bucks(self, ctx: commands.Context) -> None:
        """
        Lists the number of rbucks each member of the IHL has.
        """

        subset: list = []

        table: list[Player] = self.database.retrieve_table()

        for player in table:
            subset.append({"name": player["name"], "RBUCKS": player["rbucks"]})

        subset = sorted(subset, key=lambda d: d["RBUCKS"], reverse=True)  # type: ignore

        bucks_board: str = tabulate(subset, headers="keys", tablefmt="simple")

        embed: Embed = Embed(title="**RBUCKS**", colour=colour.Colour.green())
        embed.add_field(name="Leaderboard", value=f"```{bucks_board}```")

        await ctx.send(embed=embed)

    @staticmethod
    def create_bet_report(bet_results: dict) -> Embed:

        contents: str = ""

        for name, delta in bet_results.items():
            won_or_lost: str = "won" if delta >= 0 else "lost"

            # All bets are at an assumed price of 2.0, therefore need to divide by 2 to ignore the stake.
            corrected_delta: int = delta if delta <= 0 else int(delta / 2)

            line: str = f"{name} {won_or_lost} {abs(corrected_delta)} RBUCKS!\n"
            contents += line

        embed: Embed = Embed(title="**RBUCKS**", colour=colour.Colour.green())
        embed.add_field(name="Bet Report", value=f"```{contents}```")

        return embed

    async def refund_all_bets(self, ctx: commands.Context) -> None:

        if len(self.bets) == 0:
            return

        for bet in self.bets:
            self.database.update_rbucks(bet["name"], bet["stake"])

        await ctx.send("All bets have been refunded.")
