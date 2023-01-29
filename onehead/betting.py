from dataclasses import asdict
from typing import TYPE_CHECKING

from discord import Embed, colour
from discord.ext.commands import Bot, Cog, Context, command, has_role
from tabulate import tabulate

from onehead.common import (Bet, OneHeadException, Player, Roles, Side,
                            get_bot_instance)

if TYPE_CHECKING:
    from onehead.database import Database
    from onehead.game import Game
    from onehead.lobby import Lobby


class Betting(Cog):
    def __init__(self, database: "Database", lobby: "Lobby") -> None:

        self.database: Database = database
        self.lobby: Lobby = lobby

    def get_bet_results(self, radiant_won: bool) -> dict[str, float]:

        bot: Bot = get_bot_instance()
        core: Cog = bot.get_cog("Core")
        current_game: Game = core.current_game

        active_bets: list[Bet] = current_game.get_bets()

        bet_results: dict[str, float] = {}

        for bet in active_bets:
            if bet_results.get(bet.player) is None:
                bet_results[bet.player] = 0

            if (radiant_won and bet.side == Side.RADIANT) or (
                radiant_won is False and bet.side == Side.DIRE
            ):
                bet_results[bet.player] += bet.stake * 2.0
            else:
                bet_results[bet.player] -= bet.stake

        return bet_results

    @has_role(Roles.MEMBER)
    @command(aliases=["bets"])
    async def get_active_bets(self, ctx: Context) -> None:

        bot: Bot = get_bot_instance()
        core: Cog = bot.get_cog("Core")
        current_game: Game = core.current_game

        active_bets: list[Bet] = current_game.get_bets()
        bets = [asdict(bet) for bet in active_bets]

        table_of_bets: str = tabulate(bets, headers="keys", tablefmt="simple")

        # TODO: Can we make Radiant bets green and Dire bets red?
        embed: Embed = Embed(colour=colour.Colour.green())
        embed.add_field(name="Active Bets", value=f"```{table_of_bets}```")

        await ctx.send(embed=embed)

    @has_role(Roles.MEMBER)
    @command(aliases=["bet"])
    async def place_bet(self, ctx: Context, side: str, amount: str) -> None:
        """
        Place a bet on the match that is about to happen.

        e.g. !bet radiant 500 or !bet dire all
        """

        bot: Bot = get_bot_instance()
        core: Cog = bot.get_cog("Core")
        current_game: Game = core.current_game

        bets: list[Bet] = current_game.get_bets()

        if current_game.betting_window_open() is False:
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

        if side.lower() in Side is False:
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

        bets.append(Bet(side, stake, name))
        self.database.update_rbucks(name, -stake)

        await ctx.send(f"{name} has placed a bet of {stake} RBUCKS on {side.title()}.")

    @has_role(Roles.MEMBER)
    @command()
    async def rbucks(self, ctx: Context) -> None:
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

    async def refund_all_bets(self, ctx: Context) -> None:

        bot: Bot = get_bot_instance()
        core: Cog = bot.get_cog("Core")
        current_game: Game = core.current_game

        active_bets: list[Bet] = current_game.get_bets()

        if len(active_bets) == 0:
            return

        for bet in active_bets:
            self.database.update_rbucks(bet.player, bet.stake)

        await ctx.send("All bets have been refunded.")
