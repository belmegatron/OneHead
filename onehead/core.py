from logging import Logger
from datetime import datetime

from discord.member import Member
from discord import Embed, Intents
from discord.ext.commands import (
    Bot,
    BucketType,
    Cog,
    Command,
    Context,
    command,
    has_role,
    max_concurrency,
)
from structlog import get_logger
from tabulate import tabulate

from onehead.behaviour import Behaviour
from onehead.betting import Betting
from onehead.channels import Channels
from onehead.common import (
    OneHeadException,
    Roles,
    Side,
    get_player_names,
    load_config,
    set_bot_instance,
    get_discord_member_from_name,
    Metadata,
    play_sound
)
from onehead.database import Database
from onehead.game import Game
from onehead.lobby import Lobby, on_presence_update, on_message
from onehead.matchmaking import Matchmaking
from onehead.mental_health import MentalHealth
from onehead.protocols.database import OneHeadDatabase, Operation
from onehead.registration import Registration
from onehead.scoreboard import ScoreBoard
from onehead.transfers import Transfers
from version import __changelog__, __version__


log: Logger = get_logger()


async def bot_factory() -> Bot:
    """
    Factory method for generating an instance of our Bot.

    :return: OneHead Bot
    """

    intents: Intents = Intents.all()
    intents.members = True
    intents.presences = True
    bot: Bot = Bot(command_prefix="!", intents=intents)

    config: dict = load_config()

    database: Database = Database(config)
    scoreboard: ScoreBoard = ScoreBoard(database)
    lobby: Lobby = Lobby(database)
    team_balance: Matchmaking = Matchmaking(database, lobby)
    channels: Channels = Channels(config)
    registration: Registration = Registration(database)
    mental_health: MentalHealth = MentalHealth()
    betting: Betting = Betting(database, lobby)
    behaviour: Behaviour = Behaviour(database)
    transfers: Transfers = Transfers(database, lobby)

    await bot.add_cog(database)
    await bot.add_cog(lobby)
    await bot.add_cog(scoreboard)
    await bot.add_cog(registration)
    await bot.add_cog(team_balance)
    await bot.add_cog(channels)
    await bot.add_cog(mental_health)
    await bot.add_cog(betting)
    await bot.add_cog(behaviour)
    await bot.add_cog(transfers)

    # Add cogs first, then instantiate Core as we reference them as instance variables
    token: str = config["discord"]["token"]
    core: Core = Core(bot, token)
    await bot.add_cog(core)

    # Register events
    bot.event(on_presence_update)
    bot.event(on_message)
    bot.commands

    # Make the bot instance globally accessible for callbacks etc.
    set_bot_instance(bot)

    return bot


class Core(Cog):
    def __init__(self, bot: Bot, token: str) -> None:
        self.current_game: Game = Game()
        self.previous_game: Game | None = None

        self.bot: Bot = bot
        self.token: str = token

        self.config: dict = load_config()
        self.behaviour: Behaviour = bot.get_cog("Behaviour")  # type: ignore[assignment]
        self.database: OneHeadDatabase = bot.get_cog("Database")  # type: ignore[assignment]
        self.scoreboard: ScoreBoard = bot.get_cog("ScoreBoard")  # type: ignore[assignment]
        self.lobby: Lobby = bot.get_cog("Lobby")  # type: ignore[assignment]
        self.matchmaking: Matchmaking = bot.get_cog("Matchmaking")  # type: ignore[assignment]
        self.channels: Channels = bot.get_cog("Channels")  # type: ignore[assignment]
        self.registration: Registration = bot.get_cog("Registration")  # type: ignore[assignment]
        self.betting: Betting = bot.get_cog("Betting")  # type: ignore[assignment]
        self.transfers: Transfers = bot.get_cog("Transfers")  # type: ignore[assignment]

        if None in (
            self.database,
            self.scoreboard,
            self.lobby,
            self.matchmaking,
            self.channels,
            self.registration,
            self.betting,
            self.transfers,
            self.behaviour,
        ):
            raise OneHeadException("Unable to find cog(s)")

    async def reset(self, ctx: Context, game_cancelled=False) -> None:
        if game_cancelled:
            self.previous_game = None
        else:
            self.previous_game = self.current_game

        self.current_game = Game()
        self.lobby.clear_signups()
        ctx.voice_client.disconnect()

    async def show_teams(self, ctx: Context) -> None:
        status: Command = self.bot.get_command("status")  # type: ignore[assignment]
        await Command.invoke(status, ctx)
    
    async def setup_team_channels(self, ctx: Context) -> None:        
        await self.channels.create_discord_channels(ctx)

        if self.current_game.radiant is None or self.current_game.dire is None:
            raise OneHeadException(f"Expected valid teams: {self.current_game.radiant}, {self.current_game.dire}")

        await self.channels.move_discord_channels(ctx)
        await ctx.send("Create Dota 2 Lobby and join with the above teams.")
    
    @has_role(Roles.ADMIN)
    @command()
    @max_concurrency(1, per=BucketType.default, wait=False)
    async def start(self, ctx: Context) -> None:
        """
        Starts an IHL game.
        """

        if self.current_game.in_progress():
            await ctx.send("Game already in progress...")
            return

        signup_threshold_met: bool = await self.lobby.signup_check(ctx)
        if signup_threshold_met is False:
            return

        await play_sound(ctx, "start.mp3")
        metadata: Metadata = self.database.get_metadata()       
        await ctx.send(f"Starting game: Season {metadata['season']}, Game {metadata['game_id']}.")
        
        await self.lobby.select_players(ctx)

        self.current_game.start()
        self.lobby.disable_signups()

        (
            self.current_game.radiant,
            self.current_game.dire,
        ) = await self.matchmaking.balance(ctx)
        
        await self.show_teams(ctx)
        await self.current_game.open_transfer_window(ctx)
        await self.current_game.open_betting_window(ctx)
        await self.setup_team_channels(ctx)

        if self.current_game.in_progress():
            await ctx.send("GLHF")

            radiant: tuple[str, ...]
            dire: tuple[str, ...]
            radiant, dire = get_player_names(self.current_game.radiant, self.current_game.dire)

            log.info(f"Season {metadata['season']}, Game {metadata['game_id']} has started.")
            log.info(f"Radiant: {', '.join(radiant)}, Dire: {', '.join(dire)}.")

    @has_role(Roles.ADMIN)
    @command()
    @max_concurrency(1, per=BucketType.default, wait=False)
    async def stop(self, ctx: Context) -> None:
        """
        Cancels an IHL game.
        """

        if self.current_game.in_progress():
            self.current_game.cancel()
            log.info(f"Game was cancelled by {ctx.author.display_name}.")
            await ctx.send("Game cancelled.")
            await self.betting.refund_all_bets(ctx)
            await self.transfers.refund_transfers(ctx)
            await self.channels.move_back_to_lobby(ctx)
            await self.reset(ctx, game_cancelled=True)
        else:
            await ctx.send("No currently active game.")

    @has_role(Roles.ADMIN)
    @command()
    @max_concurrency(1, per=BucketType.default, wait=False)
    async def result(self, ctx: Context, result: str) -> None:
        """
        Provide the result of game that has finished.
        """

        if self.current_game.in_progress() is False:
            await ctx.send("No currently active game.")
            return

        if self.current_game.transfer_window_open():
            await ctx.send(
                "Cannot enter result as the transfer window for the game is currently open. Use the `!stop` command if you wish to abort the game."
            )
            return

        if self.current_game.betting_window_open():
            await ctx.send(
                "Cannot enter result as the betting window for the game is currently open. Use the `!stop` command if you wish to abort the game."
            )
            return

        result = result.lower()

        if result not in Side:
            await ctx.send(f"Must be either {Side.RADIANT} or {Side.DIRE}.")
            return

        await self.channels.move_back_to_lobby(ctx)

        log.info(f"{ctx.author.display_name} entered a result of {result}.")

        if self.current_game.radiant is None or self.current_game.dire is None:
            raise OneHeadException(f"Expected valid teams: {self.current_game.radiant}, {self.current_game.dire}")

        metadata: Metadata = self.database.get_metadata()

        log.info(f"Game {metadata['game_id']} has ended.")

        radiant_names: tuple[str, ...]
        dire_names: tuple[str, ...]

        radiant_names, dire_names = get_player_names(self.current_game.radiant, self.current_game.dire)
       
        await play_sound(ctx, "result.mp3")
       
        if result == Side.RADIANT:
            await ctx.send("`Radiant` victory!")
            for player in radiant_names:
                m: Member | None = get_discord_member_from_name(ctx, player)
                self.database.modify(m.id, "win", 1, Operation.ADD)
                self.database.modify(m.id, "win_streak", 1, Operation.ADD)
                self.database.modify(m.id, "loss_streak", 0)
                self.database.modify(m.id, "rbucks", Betting.REWARD_ON_WIN, Operation.ADD)
            for player in dire_names:
                m: Member | None = get_discord_member_from_name(ctx, player)
                self.database.modify(m.id, "loss", 1, Operation.ADD)
                self.database.modify(m.id, "loss_streak", 1, Operation.ADD)
                self.database.modify(m.id, "win_streak", 0)
                self.database.modify(m.id, "rbucks", Betting.REWARD_ON_LOSS, Operation.ADD)
        elif result == Side.DIRE:
            await ctx.send("`Dire` victory!")
            for player in radiant_names:
                m: Member | None = get_discord_member_from_name(ctx, player)
                self.database.modify(m.id, "loss", 1, Operation.ADD)
                self.database.modify(m.id, "loss_streak", 1, Operation.ADD)
                self.database.modify(m.id, "win_streak", 0)
                self.database.modify(m.id, "rbucks", Betting.REWARD_ON_LOSS, Operation.ADD)
            for player in dire_names:
                m: Member | None = get_discord_member_from_name(ctx, player)
                self.database.modify(m.id, "win", 1, Operation.ADD)
                self.database.modify(m.id, "win_streak", 1, Operation.ADD)
                self.database.modify(m.id, "loss_streak", 0)
                self.database.modify(m.id, "rbucks", Betting.REWARD_ON_WIN, Operation.ADD)

        await ctx.send("Updating scores...")
        scoreboard: Command = self.bot.get_command("scoreboard")  # type: ignore[assignment]
        await Command.invoke(scoreboard, ctx)
        
        bet_results: dict = self.betting.get_bet_results(result == Side.RADIANT)

        for name, bets in bet_results.items():
            for bet_result in bets:
                if bet_result > 0:
                    m: Member | None = get_discord_member_from_name(ctx, name)
                    self.database.modify(m.id, "rbucks", bet_result, Operation.ADD)

        if len(bet_results) > 0:
            report: Embed = self.betting.create_bet_report(bet_results)
            await ctx.send(embed=report)
            
        await self.reset(ctx)
        
        metadata["game_id"] += 1
        self.database.update_metadata(metadata)

        if self.is_end_of_season():
            await ctx.send(f"Season `{metadata['season']}` has ended!")
            metadata["season"] += 1
            metadata["game_id"] = 1
            self.database.update_metadata(metadata)
            # TODO: Make a big song and dance about the end of an IHL season, present winners, go crazy.

    @has_role(Roles.MEMBER)
    @command()
    async def status(self, ctx: Context) -> None:
        """
        If a game is active, displays the teams and their respective players.
        """

        if self.current_game.in_progress() and self.current_game.radiant and self.current_game.dire:
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
                f"**Current Game** - Season `{metadata['season']}`, Game `{metadata['game_id']}` ```\n"
                f"{in_game_players}```"
            )
        else:
            await ctx.send("No currently active game.")

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
        dt: datetime = datetime.utcfromtimestamp(metadata["timestamp"])

        await ctx.send(f"Season `{metadata['season']}` started on: `{dt}`")

    def is_end_of_season(self) -> bool:
        metadata: Metadata = self.database.get_metadata()
        return (metadata["game_id"] < metadata["max_game_count"]) is False

    @has_role(Roles.ADMIN)
    @command(aliases=["sim"])
    async def simulate_signups(self, ctx: Context) -> None:
        """
        For testing purposes.
        """
        self.lobby._signups += [
            "ERIC",
            "GEE",
            "JEFFERIES",
            "ZEED",
            "PECRO",
            "LAURENCE",
            "TOCCO",
            "JAMES",
            "LUKE",
            "ZEE",
        ]
