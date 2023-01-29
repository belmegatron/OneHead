from discord import Embed, Intents
from discord.ext.commands import (Bot, BucketType, Cog, Command, Context,
                                  command, has_role, max_concurrency)
from tabulate import tabulate

from onehead.behaviour import Behaviour
from onehead.betting import Betting
from onehead.channels import Channels
from onehead.common import (OneHeadException, Roles, Side, get_player_names,
                            load_config, set_bot_instance)
from onehead.database import Database
from onehead.game import Game
from onehead.lobby import Lobby, on_member_update, on_voice_state_update
from onehead.matchmaking import Matchmaking
from onehead.mental_health import MentalHealth
from onehead.registration import Registration
from onehead.scoreboard import ScoreBoard
from onehead.transfers import Transfers
from version import __changelog__, __version__


def bot_factory() -> Bot:
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

    bot.add_cog(database)
    bot.add_cog(lobby)
    bot.add_cog(scoreboard)
    bot.add_cog(registration)
    bot.add_cog(team_balance)
    bot.add_cog(channels)
    bot.add_cog(mental_health)
    bot.add_cog(betting)
    bot.add_cog(behaviour)
    bot.add_cog(transfers)

    # Add cogs first, then instantiate OneHeadCore as we reference them as instance variables
    token: str = config["discord"]["token"]
    core: Core = Core(bot, token)
    bot.add_cog(core)

    # Register events
    bot.event(on_voice_state_update)
    bot.event(on_member_update)

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
        self.behaviour: Behaviour = bot.get_cog("Behaviour")
        self.database: Database = bot.get_cog("Database")
        self.scoreboard: ScoreBoard = bot.get_cog("ScoreBoard")
        self.lobby: Lobby = bot.get_cog("Lobby")
        self.matchmaking: Matchmaking = bot.get_cog("Matchmaking")
        self.channels: Channels = bot.get_cog("Channels")
        self.registration: Registration = bot.get_cog("Registration")
        self.betting: Betting = bot.get_cog("Betting")
        self.transfers: Transfers = bot.get_cog("Transfers")

        if None in (
            self.database,
            self.scoreboard,
            self.lobby,
            self.matchmaking,
            self.channels,
            self.registration,
            self.betting,
            self.transfers,
            self.behaviour
        ):
            raise OneHeadException("Unable to find cog(s)")
        
    async def reset(self, ctx: Context, game_cancelled=False) -> None:

        await self.channels.move_back_to_lobby(ctx)
        
        if game_cancelled is True:
            self.previous_game = None
        else:
            self.previous_game = self.current_game

        self.current_game = Game()
        self.lobby.clear_signups()

    async def setup_teams(self, ctx: Context) -> None:

        status: Command = self.bot.get_command("status")
        await Command.invoke(status, ctx)
        await self.channels.create_discord_channels(ctx)
        
        if self.current_game.radiant is None or self.current_game.dire is None:
            raise OneHeadException(f"Expected valid teams: {self.current_game.radiant}, {self.current_game.dire}")
        
        self.channels.set_teams(self.current_game.radiant, self.current_game.dire)
        await self.channels.move_discord_channels(ctx)
        await ctx.send("Setup Lobby in Dota 2 Client and join with the above teams.")

    @has_role(Roles.ADMIN)
    @command()
    @max_concurrency(1, per=BucketType.default, wait=False)
    async def start(self, ctx: Context) -> None:
        """
        Starts an IHL game.
        """

        if self.current_game.active():
            await ctx.send("Game already in progress...")
            return

        signup_threshold_met: bool = await self.lobby.signup_check(ctx)
        if signup_threshold_met is False:
            return

        await self.lobby.select_players(ctx)

        self.current_game.start()
        self.lobby.disable_signups()

        self.current_game.radiant, self.current_game.dire = await self.matchmaking.balance(ctx)
        await self.setup_teams(ctx)
        await self.current_game.open_transfer_window(ctx)
        await self.current_game.open_betting_window(ctx)

    @has_role(Roles.ADMIN)
    @command()
    @max_concurrency(1, per=BucketType.default, wait=False)
    async def stop(self, ctx: Context) -> None:
        """
        Cancels an IHL game.
        """

        if self.current_game.in_progress():
            self.current_game.cancel()
            await ctx.send("Game stopped.")
            await self.betting.refund_all_bets(ctx)
            await self.transfers.refund_transfers(ctx)
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
            await ctx.send("Cannot enter result as the Transfer window for the game is currently open. Use the !stop command if you wish to abort the game.")
            return
        
        if self.current_game.betting_window_open():
            await ctx.send("Cannot enter result as the Betting window for the game is currently open. Use the !stop command if you wish to abort the game.")
            return

        if result in Side is False:
            await ctx.send(f"Invalid Value - Must be either {Side.RADIANT} or {Side.DIRE}.")
            return

        bet_results: dict = self.betting.get_bet_results(result == Side.RADIANT)

        for name, delta in bet_results.items():
            if delta > 0:
                self.database.update_rbucks(name, delta)

        report: Embed = self.betting.create_bet_report(bet_results)
        await ctx.send(embed=report)

        await ctx.send("Updating Scores...")
        
        if self.current_game.radiant is None or self.current_game.dire is None:
            raise OneHeadException(f"Expected valid teams: {self.current_game.radiant}, {self.current_game.dire}")
        
        radiant_names, dire_names = get_player_names(
            self.current_game.radiant, self.current_game.dire
        )

        if result == Side.RADIANT:
            await ctx.send("Radiant Victory!")
            for player in radiant_names:
                self.database.update_player(player, True)
            for player in dire_names:
                self.database.update_player(player, False)
        elif result == Side.DIRE:
            await ctx.send("Dire Victory!")
            for player in radiant_names:
                self.database.update_player(player, False)
            for player in dire_names:
                self.database.update_player(player, True)

        scoreboard: Command = self.bot.get_command("scoreboard")
        await Command.invoke(scoreboard, ctx)
        await self.reset(ctx)

    @has_role(Roles.MEMBER)
    @command()
    async def status(self, ctx: Context) -> None:
        """
        If a game is active, displays the teams and their respective players.
        """

        if self.current_game.active() and self.current_game.radiant and self.current_game.dire:
            t1_names, t2_names = get_player_names(self.current_game.radiant, self.current_game.dire)
            players = {Side.RADIANT: t1_names, Side.DIRE: t2_names}
            in_game_players = tabulate(players, headers="keys", tablefmt="simple")
            await ctx.send(f"**Current Game** ```\n" f"{in_game_players}```")
        else:
            await ctx.send("No currently active game.")

    @has_role(Roles.MEMBER)
    @command()
    async def version(self, ctx: Context) -> None:
        """
        Displays the current version of OneHead.
        """

        await ctx.send(f"**Current Version** - {__version__}")
        await ctx.send(f"**Changelog** - {__changelog__}")

    @command()
    async def matches(self, ctx: Context) -> None:
        """
        Display the top 10 most recent matches in the IHL.
        """

        await ctx.send(
            "https://www.dotabuff.com/esports/leagues/13630-igc-inhouse-league"
        )

    @has_role(Roles.ADMIN)
    @command(aliases=["sim"])
    async def simulate_signups(self, ctx: Context) -> None:
        """
        For testing purposes.
        """
        self.lobby._signups = [
            "ERIC",
            "HARRY",
            "JEFFERIES",
            "ZEED",
            "PECRO",
            "LAURENCE",
            "THANOS",
            "JAMES",
            "LUKE",
            "ZEE",
        ]
