from dataclasses import asdict
from logging import Logger
from typing import TYPE_CHECKING, cast

from discord import Embed, colour
from discord.member import Member
from discord.ext.commands import Bot, Cog, Context, command, has_role
from structlog import get_logger
from tabulate import tabulate

from onehead.common import Bet, Player, Roles, Side, get_bot_instance, get_discord_member_from_name, play_sound
from onehead.game import Game, Challenge
from onehead.protocols.database import OneHeadDatabase, Operation
from onehead.lobby import Lobby
from onehead.challenge import ChallengeMode


if TYPE_CHECKING:
    from onehead.core import Core


log: Logger = get_logger()


class Betting(Cog):
    INITIAL_BALANCE: int = 100
    REWARD_ON_WIN: int = 100
    REWARD_ON_LOSS: int = 50

    def __init__(self, database: OneHeadDatabase, lobby: Lobby) -> None:
        self.database: OneHeadDatabase = database
        self.lobby: Lobby = lobby

    def get_bet_results(self, winner: Side | Member) -> dict[str, list[float]]:
        bot: Bot = get_bot_instance()
        core: Core = cast(Core, bot.get_cog("Core"))
        current_game: Game | None = core.current_game

        bet_results: dict[str, list[float]] = {}

        if current_game is None:
            return bet_results

        active_bets: list[Bet] = current_game.get_bets()

        for bet in active_bets:
            if bet_results.get(bet.bettor) is None:
                bet_results[bet.bettor] = []

            if bet.selection == winner:
                winnings: float = (bet.stake * bet.price) - bet.stake
                bet_results[bet.bettor].append(winnings)
            else:
                bet_results[bet.bettor].append(-1 * bet.stake)

        return bet_results

    @has_role(Roles.MEMBER)
    @command()
    async def bets(self, ctx: Context) -> None:
        """
        Lists active bets for the current game.
        """
        bot: Bot = get_bot_instance()
        core: Core = cast(Core, bot.get_cog("Core"))
        current_game: Game | None = core.current_game
        if current_game is None:
            return

        active_bets: list[Bet] = current_game.get_bets()
        bets: list[dict[str, str | int | float]] = [asdict(bet) for bet in active_bets]

        table_of_bets: str = tabulate(bets, headers="keys", tablefmt="simple")

        await ctx.send(f"**Bets** ```\n{table_of_bets}```")

    @has_role(Roles.MEMBER)
    @command(aliases=["bet"])
    async def place_bet(self, ctx: Context, first: str, second: str) -> None:
        """
        Place a bet on the match that is about to happen.

        e.g. !bet radiant 500 or !bet dire all or !bet 500 radiant or bet all dire
        """

        bot: Bot = get_bot_instance()
        core: Core = cast(Core, bot.get_cog("Core"))
        current_game: Game | None = core.current_game

        if current_game is None:
            await ctx.send("Unable to bet as there is currently no game being played.")
            return

        if current_game.betting_window_open() is False:
            await ctx.send("Betting window closed.")
            return

        record: Player | None = self.database.get(ctx.author.id)
        if record is None:
            await ctx.send(f"Unable to find {ctx.author.mention} in database.")
            return None

        bet: Bet | None = await self.parse_bet_arguments(ctx, first, second, record)
        if bet is None:
            return

        if bet.stake <= 0:
            await ctx.send(f"{ctx.author.mention} - Bet stake must be greater than 0.")
            return

        available_balance: int = record.get("rbucks")
        if bet.stake > available_balance:
            await ctx.send(
                f"Unable to place bet - {ctx.author.mention} tried to stake `{bet.stake:.0f}` RBUCKS but only has `{available_balance:.0f}` RBUCKS available."
            )
            return

        if isinstance(current_game, Challenge):
            if ctx.author in (current_game.challenger, current_game.opponent):
                await ctx.send(f"{ctx.author.mention} cannot place a bet on this duel as they are participating in it!")
                return

            challenger_price, opponent_price = self.calculate_challenge_odds(current_game)

            if bet.selection == current_game.challenger.display_name:
                bet.price = challenger_price
            else:
                bet.price = opponent_price

        bets: list[Bet] = current_game.get_bets()
        bets.append(bet)
        self.database.modify(ctx.author.id, "rbucks", bet.stake, Operation.SUBTRACT)

        await play_sound(ctx, "bet.mp3")

        log.info(
            f"{ctx.author.display_name} has placed a bet of {bet.stake:.0f} RBUCKS on {bet.selection} at a price of {bet.price}."
        )

        await ctx.send(
            f"{ctx.author.mention} has placed a bet of `{bet.stake:.0f}` RBUCKS on {bet.selection} at a price of {bet.price}."
        )

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
        await ctx.send(f"**RBUCKS** ```\n{bucks_board}```")

    @staticmethod
    def create_bet_report(bet_results: dict[str, list[float]]) -> Embed:
        contents: str = ""

        for name, deltas in bet_results.items():
            for delta in deltas:
                won_or_lost: str = "won" if delta >= 0 else "lost"
                line: str = f"{name} {won_or_lost} {abs(delta)} RBUCKS!"
                log.info(line)
                contents += line
                contents += "\n"

        embed: Embed = Embed(title="**RBUCKS**", colour=colour.Colour.green())
        embed.add_field(name="Bet Report", value=f"```{contents}```")

        return embed

    async def refund_all_bets(self, ctx: Context) -> None:
        bot: Bot = get_bot_instance()
        core: Core = cast(Core, bot.get_cog("Core"))
        current_game: Game | None = core.current_game

        if current_game is None:
            return

        active_bets: list[Bet] = current_game.get_bets()

        if len(active_bets) == 0:
            return

        for bet in active_bets:
            m: Member | None = get_discord_member_from_name(ctx, bet.bettor)
            if m:
                self.database.modify(m.id, "rbucks", bet.stake, Operation.ADD)

        log.info("Refunded all bets.")

        await ctx.send("All bets have been refunded.")

    async def parse_bet_arguments(self, ctx: Context, first: str, second: str, record: Player) -> Bet | None:
        selection: str = ""
        amount: str = ""

        # Is it a classic bet?
        if first in Side:
            selection = first
            amount = second
        elif second in Side:
            selection = second
            amount = first

        # If it isn't a classic bet, is it a challenge bet?
        if not selection:
            member: Member | None = get_discord_member_from_name(ctx, first)
            if member:
                selection = member.display_name
                amount = second
            else:
                member = get_discord_member_from_name(ctx, second)
                if member:
                    selection = member.display_name
                    amount = first

        available_balance: int = record.get("rbucks", 0)
        stake: int = 0

        if amount == "all":
            stake = available_balance
        else:
            try:
                stake = int(amount)
            except ValueError:
                await ctx.send(
                    f"{ctx.author.mention} - `{amount}` is not a valid number of RBUCKS to place a bet with."
                )

        if selection:
            return Bet(bettor=ctx.author.display_name, selection=selection, stake=stake)

        return None

    @staticmethod
    def convert_decimal_odds_to_percentage_odds(decimal_odds: float) -> float:
        return (1.0 / decimal_odds) * 100

    @staticmethod
    def convert_percentage_odds_to_decimal(percentage_odds: float) -> float:
        return 1.0 / (percentage_odds / 100.0)

    def calculate_challenge_odds(self, challenge: Challenge) -> tuple[float, float]:
        challenger: Player | None = self.database.get(challenge.challenger.id)
        opponent: Player | None = self.database.get(challenge.opponent.id)

        if challenger is None or opponent is None:
            raise

        mmr_difference: int = challenger["mmr"] - opponent["mmr"]

        challenger_decimal_odds: float = 2.0
        opponent_decimal_odds: float = 2.0
        scaled_difference: float = abs(float(mmr_difference / ChallengeMode.MAX_RATING_DIFFERENCE))

        # Challenger is favoured
        if mmr_difference > 0:
            challenger_decimal_odds -= scaled_difference
            challenger_percentage_odds = self.convert_decimal_odds_to_percentage_odds(challenger_decimal_odds)
            opponent_percentage_odds = 100 - challenger_percentage_odds
            opponent_decimal_odds: float = self.convert_percentage_odds_to_decimal(opponent_percentage_odds)

        # Opponent is favoured.
        elif mmr_difference < 0:
            opponent_decimal_odds -= scaled_difference
            opponent_percentage_odds = self.convert_decimal_odds_to_percentage_odds(opponent_decimal_odds)
            challenger_percentage_odds = 100 - opponent_percentage_odds
            challenger_decimal_odds: float = self.convert_percentage_odds_to_decimal(challenger_percentage_odds)

        return round(challenger_decimal_odds, 2), round(opponent_decimal_odds, 2)
