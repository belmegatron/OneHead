from logging import Logger
from datetime import datetime, UTC
from typing import cast

from discord import Intents
from discord.ext.commands import (
    Bot,
    Cog,
    Context,
    command,
    has_role,
)
from structlog import get_logger

from onehead.behaviour import Behaviour
from onehead.betting import Betting
from onehead.callbacks import on_presence_update, on_message, set_bot_instance
from onehead.channels import Channels
from onehead.common import (
    OneHeadException,
    Roles,
    Metadata,
)
from onehead.config import Config, load_config
from onehead.coordinator import GameCoordinator
from onehead.database import Database
from onehead.lobby import Lobby
from onehead.matchmaking import Matchmaking
from onehead.mental_health import MentalHealth
from onehead.protocols.database import PlayerDatabase
from onehead.registration import Registration
from onehead.scoreboard import ScoreBoard
from onehead.transfers import Transfers
from onehead.challenge import ChallengeMode
from onehead.store import GameStore
from version import __changelog__, __version__


log: Logger = get_logger()


async def bot_builder() -> Bot:
    """
    Builder method for generating an instance of our Bot.

    :return: OneHead bot
    """

    intents: Intents = Intents.all()
    intents.members = True
    intents.presences = True
    bot: Bot = Bot(command_prefix="!", intents=intents)

    config: Config = load_config()
    store: GameStore = GameStore()
    
    database: Database = Database(config)
    scoreboard: ScoreBoard = ScoreBoard(database)
    lobby: Lobby = Lobby(store, database)
    matchmaking: Matchmaking = Matchmaking(database, lobby)
    channels: Channels = Channels(store, config)
    registration: Registration = Registration(database)
    mental_health: MentalHealth = MentalHealth()
    betting: Betting = Betting(store, database, lobby)
    behaviour: Behaviour = Behaviour(store, database)
    transfers: Transfers = Transfers(store, database, lobby, matchmaking)
    challenge_mode: ChallengeMode = ChallengeMode(database)
    coordinator: GameCoordinator = GameCoordinator(store, betting, transfers, channels, database, challenge_mode, lobby, matchmaking, scoreboard)

    await bot.add_cog(database)
    await bot.add_cog(lobby)
    await bot.add_cog(scoreboard)
    await bot.add_cog(registration)
    await bot.add_cog(matchmaking)
    await bot.add_cog(channels)
    await bot.add_cog(mental_health)
    await bot.add_cog(betting)
    await bot.add_cog(behaviour)
    await bot.add_cog(transfers)
    await bot.add_cog(challenge_mode)
    await bot.add_cog(coordinator)

    # Add cogs first, then instantiate Core as we reference them as instance variables
    core: Core = Core(bot, config.discord.token)
    await bot.add_cog(core)

    # Register events
    bot.event(on_presence_update)
    bot.event(on_message)

    # Make the bot instance globally accessible for callbacks etc.
    set_bot_instance(bot)

    return bot


class Core(Cog):
    def __init__(self, bot: Bot, token: str) -> None:
        self.bot: Bot = bot
        self.token: str = token

        self.database: PlayerDatabase = cast(Database, bot.get_cog("Database"))
        self.lobby: Lobby = cast(Lobby, bot.get_cog("Lobby"))

    @has_role(Roles.MEMBER)
    @command()
    async def version(self, ctx: Context) -> None:
        """
        Displays the current version of OneHead.
        """
        await ctx.send(f"**Current Version** - `{__version__}`")
        await ctx.send(f"**Changelog** - {__changelog__}")

    @has_role(Roles.MEMBER)
    @command()
    async def matches(self, ctx: Context) -> None:
        """
        Display the top 10 most recent matches in the IHL.
        """
        await ctx.send("https://www.dotabuff.com/esports/leagues/13630-igc-inhouse-league")

    @has_role(Roles.MEMBER)
    @command()
    async def season(self, ctx: Context) -> None:
        """
        Display info on the current IHL season.
        """
        metadata: Metadata = self.database.get_metadata()
        dt: datetime = datetime.fromtimestamp(metadata["timestamp"], UTC)

        await ctx.send(f"Season `{metadata['season']}` started on: `{dt}`")

    @has_role(Roles.ADMIN)
    @command(aliases=["sim"])
    async def simulate_signups(self, _: Context) -> None:
        """
        For testing purposes.
        """
        now: datetime = datetime.now()

        self.lobby._signups.update(
            {
                "ERIC": now,
                "GEE": now,
                "JEFFERIES": now,
                "ZEED": now,
                "PECRO": now,
                "LAURENCE": now,
                "TOCCO": now,
                "JAMES": now,
                "LUKE": now,
                "ZEE": now,
            }
        )
