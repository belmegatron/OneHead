from dataclasses import asdict
from logging import Logger
from typing import Literal, TYPE_CHECKING, Any, cast

from discord import Embed, colour
from discord.member import Member
from discord.ext.commands import Bot, Cog, Context, command, has_role
from structlog import get_logger
from tabulate import tabulate

from onehead.common import Bet, Player, Roles, Side, get_bot_instance, get_discord_member_from_name, play_sound
from onehead.protocols.database import OneHeadDatabase, Operation
from onehead.challenge import Challenge, ChallengeMode


if TYPE_CHECKING:
    from onehead.core import Core
    from onehead.game import Game
    from onehead.lobby import Lobby


log: Logger = get_logger()


class Betting(Cog):
    INITIAL_BALANCE: Literal[100] = 100
    REWARD_ON_WIN: Literal[100] = 100
    REWARD_ON_LOSS: Literal[50] = 50

    def __init__(self, database: OneHeadDatabase, lobby: Lobby) -> None:
        self.database: OneHeadDatabase = database
        self.lobby: Lobby = lobby

    def get_bet_results(self, radiant_won: bool) -> dict[str, list[float]]:
        bot: Bot = get_bot_instance()
        core: Core = bot.get_cog("Core")  # type: ignore[assignment]
        current_game: Game = core.current_game

        active_bets: list[Bet] = current_game.get_bets()

        bet_results: dict[str, list[float]] = {}

        for bet in active_bets:
            if bet_results.get(bet.bettor) is None:
                bet_results[bet.bettor] = []

            if (radiant_won and bet.selection == Side.RADIANT) or (radiant_won is False and bet.selection == Side.DIRE):
                bet_results[bet.bettor].append(bet.stake * bet.price)
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
        core: Core = bot.get_cog("Core")  # type: ignore[assignment]
        current_game: Game = core.current_game

        active_bets: list[Bet] = current_game.get_bets()
        bets: list[dict[str, Any]] = [asdict(bet) for bet in active_bets]

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
        core: Core = bot.get_cog("Core")  # type: ignore[assignment]
        current_game: Game = core.current_game

        if current_game.betting_window_open() is False:
            await ctx.send("Betting window closed.")
            return
        
        # TODO: Determine if match bet/challenge bet.
        # TODO: Find the challenge the bet relates to.
        # TODO: Check if betting window is open for that challengew
        # TODO: Check that the challenger/opponent cannot participate in the bet.

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

        # TODO: If it's a challenge bet, we need to grab the prices from somewhere before appending it to bets.
        bets: list[Bet] = current_game.get_bets()
        bets.append(bet)
        self.database.modify(ctx.author.id, "rbucks", bet.stake, Operation.SUBTRACT)

        await play_sound(ctx, "bet.mp3")
        
        if isinstance(bet.selection, Side):
            log.info(f"{ctx.author.display_name} has placed a bet of {bet.stake:.0f} RBUCKS on {bet.selection.title()}.")
            await ctx.send(f"{ctx.author.mention} has placed a bet of `{bet.stake:.0f}` RBUCKS on {bet.selection.title()}.")
        elif isinstance(bet.selection, Member):
            log.info(f"{ctx.author.display_name} has placed a bet of {bet.stake:.0f} RBUCKS on {bet.selection.display_name}.")
            await ctx.send(f"{ctx.author.mention} has placed a bet of `{bet.stake:.0f}` RBUCKS on {bet.selection.mention}.")
            
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
            m: Member | None = get_discord_member_from_name(ctx, bet.bettor)
            self.database.modify(m.id, "rbucks", bet.stake, Operation.ADD)

        log.info("Refunded all bets.")

        await ctx.send("All bets have been refunded.")
        
    async def parse_bet_arguments(self, ctx: Context, first: str, second: str, record: Player) -> Bet | None:
        selection: Side | Member | None = None
        amount: str = ""

        # Is it a match bet?
        if first in Side:
            selection = cast(Side, first)
            amount = second
        elif second in Side:
            selection = cast(Side, second)
            amount = first
        
        # If it isn't a match bet, is it a challenge bet?
        if not selection:
            member: Member | None = None
            member = get_discord_member_from_name(ctx, first)
            if member:
                selection = member
                amount = second
            else:
                member = get_discord_member_from_name(ctx, second)
                if member:
                    selection = member
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