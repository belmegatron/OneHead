from logging import Logger

from discord.ext.commands import Cog, Context, command, has_role
from structlog import get_logger
from tabulate import tabulate

from onehead.common import Metadata, Roles, Side, get_player_names
from onehead.game import Challenge, ClassicGame, Game
from onehead.interfaces.database import PlayerDatabase

log: Logger = get_logger()


class GameStore(Cog):
    def __init__(self, database: PlayerDatabase) -> None:
        self.database: PlayerDatabase = database
        self.current_game: Game | None = None
        self.previous_game: Game | None = None

    @has_role(Roles.MEMBER)
    @command()
    async def status(self, ctx: Context) -> None:
        """
        If a game is active, displays the teams and their respective players.
        """
        if self.current_game is None:
            await ctx.send("No currently active game.")
            return

        if self.current_game.in_progress():
            if isinstance(self.current_game, ClassicGame):
                if self.current_game.radiant and self.current_game.dire:
                    t1_names: tuple[str, ...]
                    t2_names: tuple[str, ...]
                    t1_names, t2_names = get_player_names(self.current_game.radiant, self.current_game.dire)

                    players: dict[Side, tuple[str, ...]] = {
                        Side.RADIANT: t1_names,
                        Side.DIRE: t2_names,
                    }
                    in_game_players: str = tabulate(players, headers="keys", tablefmt="simple")
                    metadata: Metadata = self.database.get_metadata()

                    await ctx.send(
                        f"**Current Game** - Season `{metadata.season}`, Game `{metadata.game_id}` ```\n"
                        f"{in_game_players}```"
                    )
            elif isinstance(self.current_game, Challenge):
                await ctx.send(
                    f"**Current Duel** - {self.current_game.challenger.mention} vs. {self.current_game.opponent.mention}"
                )
