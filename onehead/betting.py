from dataclasses import asdict
from logging import Logger
from typing import Literal, TYPE_CHECKING, Any

from discord import Embed, colour
from discord.member import Member
from discord.ext.commands import Bot, Cog, Context, command, has_role
from structlog import get_logger
from tabulate import tabulate

from onehead.common import Bet, Player, Roles, Side, get_bot_instance, get_discord_member_from_name, play_sound
from onehead.protocols.database import OneHeadDatabase, Operation


if TYPE_CHECKING:
    from onehead.core import Core
    from onehead.game import Game
    from onehead.lobby import Lobby


log: Logger = get_logger()


class Betting(Cog):
    INITIAL_BALANCE: Literal[100] = 100
    REWARD_ON_WIN: Literal[100] = 100
    REWARD_ON_LOSS: Literal[50] = 50

    def __init__(self, database: OneHeadDatabase, lobby: "Lobby") -> None:
        self.database: OneHeadDatabase = database
        self.lobby: Lobby = lobby

    def get_bet_results(self, radiant_won: bool) -> dict[str, list[float]]:
        bot: Bot = get_bot_instance()
        core: Core = bot.get_cog("Core")  # type: ignore[assignment]
        current_game: Game = core.current_game

        active_bets: list[Bet] = current_game.get_bets()

        bet_results: dict[str, list[float]] = {}

        for bet in active_bets:
            if bet_results.get(bet.player) is None:
                bet_results[bet.player] = []

            if (radiant_won and bet.side == Side.RADIANT) or (radiant_won is False and bet.side == Side.DIRE):
                bet_results[bet.player].append(bet.stake * 2.0)
            else:
                bet_results[bet.player].append(-1 * bet.stake)

        return bet_results

    @has_role(Roles.MEMBER)
    @command()
    async def bets(self, ctx: Context) -> None:
        """
        Lists active bets for the current game.
        """
        bot: Bot = get_bot_instance()
        core: Core = bot.get_cog("Core")  # type: ignore[assignment]
        current_game: Game = core.current_game

        active_bets: list[Bet] = current_game.get_bets()
        bets: list[dict[str, Any]] = [asdict(bet) for bet in active_bets]

        table_of_bets: str = tabulate(bets, headers="keys", tablefmt="simple")

        # TODO: Can we make Radiant bets green and Dire bets red?
        embed: Embed = Embed(colour=colour.Colour.green())
        embed.add_field(name="Active Bets", value=f"```{table_of_bets}```")

        await ctx.send(embed=embed)

    @has_role(Roles.MEMBER)
    @command(aliases=["bet"])
    async def place_bet(self, ctx: Context, arg_0: str, arg_1: str) -> None:
        """
        Place a bet on the match that is about to happen.

        e.g. !bet radiant 500 or !bet dire all or !bet 500 radiant or bet all dire
        """

        bot: Bot = get_bot_instance()
        core: Core = bot.get_cog("Core")  # type: ignore[assignment]
        current_game: Game = core.current_game

        bets: list[Bet] = current_game.get_bets()

        if current_game.betting_window_open() is False:
            await ctx.send("Betting window closed.")
            return

        side: str
        amount: str
        
        if arg_0 in Side:
            side = arg_0
            amount = arg_1
        else:
            side = arg_1
            amount = arg_0
        
        side = side.lower()

        record: Player | None = self.database.get(ctx.author.id)
        if record is None:
            await ctx.send(f"Unable to find {ctx.author.mention} in database.")
            return

        available_balance: int = record.get("rbucks", 0)

        if available_balance == 0:
            await ctx.send(f"{ctx.author.mention} cannot bet as they have no available RBUCKS.")
            return

        if side not in Side:
            await ctx.send(f"{ctx.author.mention} - Cannot bet on `{side}` - must be either Radiant/Dire.")
            return

        if amount == "all":
            stake: int = available_balance
        else:
            try:
                stake = int(amount)
            except ValueError:
                await ctx.send(
                    f"{ctx.author.mention} - `{amount}` is not a valid number of RBUCKS to place a bet with."
                )
                return

        if stake <= 0:
            await ctx.send(f"{ctx.author.mention} - Bet stake must be greater than 0.")
            return

        if stake > available_balance:
            await ctx.send(
                f"Unable to place bet - {ctx.author.mention} tried to stake `{stake:.0f}` RBUCKS but only has `{available_balance:.0f}` RBUCKS available."
            )
            return

        bets.append(Bet(side, stake, ctx.author.display_name))
        self.database.modify(ctx.author.id, "rbucks", stake, Operation.SUBTRACT)

        await play_sound(ctx, "bet.mp3")
        log.info(f"{ctx.author.display_name} has placed a bet of {stake:.0f} RBUCKS on {side.title()}.")
        await ctx.send(f"{ctx.author.mention} has placed a bet of `{stake:.0f}` RBUCKS on {side.title()}.")

    @has_role(Roles.MEMBER)
    @command()
    async def rbucks(self, ctx: Context) -> None:
        """
        Lists the number of rbucks each member of the IHL has.
        """

        subset: list = []

        table: list[Player] = self.database.get_all()

        for player in table:
            subset.append({"name": player["name"], "RBUCKS": player["rbucks"]})

        subset = sorted(subset, key=lambda d: d["RBUCKS"], reverse=True)  # type: ignore

        bucks_board: str = tabulate(subset, headers="keys", tablefmt="simple")

        embed: Embed = Embed(title="**RBUCKS**", colour=colour.Colour.green())
        embed.add_field(name="Leaderboard", value=f"```{bucks_board}```")

        await ctx.send(embed=embed)

    @staticmethod
    def create_bet_report(bet_results: dict[str, list[float]]) -> Embed:
        contents: str = ""

        for name, deltas in bet_results.items():
            for delta in deltas:
                won_or_lost: str = "won" if delta >= 0 else "lost"

                # All bets are at an assumed price of 2.0, therefore need to divide by 2 to ignore the stake.
                corrected_delta: int = int(delta) if delta <= 0 else int(delta / 2)

                line: str = f"{name} {won_or_lost} {abs(corrected_delta)} RBUCKS!"
                log.info(line)
                contents += line
                contents += "\n"

        embed: Embed = Embed(title="**RBUCKS**", colour=colour.Colour.green())
        embed.add_field(name="Bet Report", value=f"```{contents}```")

        return embed

    async def refund_all_bets(self, ctx: Context) -> None:
        bot: Bot = get_bot_instance()
        core: Core = bot.get_cog("Core")  # type: ignore[assignment]
        current_game: Game = core.current_game

        active_bets: list[Bet] = current_game.get_bets()

        if len(active_bets) == 0:
            return

        for bet in active_bets:
            m: Member | None = get_discord_member_from_name(ctx, bet.player)
            self.database.modify(m.id, "rbucks", bet.stake, Operation.ADD)

        log.info("Refunded all bets.")

        await ctx.send("All bets have been refunded.")
