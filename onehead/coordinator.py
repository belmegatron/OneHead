from asyncio import create_task
from logging import Logger
from typing import cast

from discord.member import Member
from discord import Embed
from discord.ext.commands import (
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

from onehead.betting import Betting
from onehead.channels import Channels
from onehead.common import (
    OneHeadException,
    Roles,
    Side,
    get_player_names,
    get_discord_member_from_name,
    Metadata,
    play_sound,
    voice_client_disconnect,
    get_command_from_cog
)
from onehead.game import ClassicGame, Challenge
from onehead.lobby import Lobby
from onehead.matchmaking import Matchmaking
from onehead.protocols.database import PlayerDatabase, Operation
from onehead.scoreboard import ScoreBoard
from onehead.transfers import Transfers
from onehead.challenge import ChallengeMode
from onehead.store import GameStore
from version import __changelog__, __version__


log: Logger = get_logger()


class GameCoordinator(Cog):
    def __init__(self,
                 store: GameStore, 
                 betting: Betting, 
                 transfers: Transfers, 
                 channels: Channels, 
                 database: PlayerDatabase, 
                 challenge_mode: ChallengeMode,
                 lobby: Lobby,
                 matchmaking: Matchmaking,
                 scoreboard: ScoreBoard) -> None:
        super().__init__()
        
        self.store: GameStore = store
        self.betting: Betting = betting
        self.transfers: Transfers = transfers
        self.channels: Channels = channels
        self.database: PlayerDatabase = database
        self.challenge_mode: ChallengeMode = challenge_mode
        self.lobby: Lobby = lobby
        self.matchmaking: Matchmaking = matchmaking
        self.scoreboard: ScoreBoard = scoreboard
    
    @has_role(Roles.ADMIN)
    @command()
    @max_concurrency(1, per=BucketType.default, wait=False)
    async def start(self, ctx: Context, duel_id: str = "") -> None:
        """
        If duel_id is specified, attempts to start a duel else attempts to start a 5v5 game.
        """
        if self.store.current_game and self.store.current_game.in_progress():
            await ctx.send("Game already in progress...")
            return

        if duel_id:
            await self.start_challenge(ctx, duel_id)
        else:
            await self.start_classic_game(ctx)
        
    @has_role(Roles.ADMIN)
    @command()
    @max_concurrency(1, per=BucketType.default, wait=False)
    async def stop(self, ctx: Context) -> None:
        """
        Cancels an IHL game.
        """
        if self.store.current_game and self.store.current_game.in_progress():
            self.store.current_game.cancel()
            log.info(f"Game was cancelled by {ctx.author.display_name}.")
            await ctx.send("Game cancelled.")
            await self.betting.refund_all_bets(ctx)

            if isinstance(self.store.current_game, ClassicGame):
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
        if self.store.current_game is None or self.store.current_game.in_progress() is False:
            await ctx.send("No currently active game.")
            return
        
        winner: Side | Member | None = None
        
        if isinstance(self.store.current_game, ClassicGame):
            await self.handle_classic_game_result(ctx, result)
            winner = cast(Side, result)
        elif isinstance(self.store.current_game, Challenge):
            winner = await self.handle_challenge_result(ctx, result)

        if winner:
            await self.handle_bet_results(ctx, winner)
            await self.reset(ctx)
   
    async def handle_challenge_result(self, ctx: Context, result: str) -> Member | None:
        self.store.current_game = cast(Challenge, self.store.current_game)
        if self.store.current_game.betting_window_open():
            await ctx.send(
                "Cannot enter result as the betting window for the game is currently open. Use the `!stop` command if you wish to abort the game."
            )
            return
        
        winner = get_discord_member_from_name(ctx, result)

        if winner not in (self.store.current_game.challenger, self.store.current_game.opponent):
            await ctx.send(
                f"Must specify either {self.store.current_game.challenger.mention} or {self.store.current_game.opponent.mention} as the winner when entering a result."
            )
            return
        
        await play_sound(ctx, "winner.mp3")
        await ctx.send(f"{winner.mention} has emerged victorious!")
        await ctx.send(f"All hail {winner.mention}!")
        
        return winner
    
    async def handle_bet_results(self, ctx: Context, winner: Side | Member) -> None:
        bet_results: dict = self.betting.get_bet_results(winner)

        for name, bets in bet_results.items():
            for bet_result in bets:
                if bet_result > 0:
                    member: Member | None = get_discord_member_from_name(ctx, name)
                    if member is None:
                        continue
                    self.database.modify(member.id, "rbucks", bet_result, Operation.ADD)

        if len(bet_results) > 0:
            report: str = self.betting.create_bet_report(bet_results)
            await ctx.send(report)
    
    async def show_teams(self, ctx: Context) -> None:
        command: Command | None = get_command_from_cog(self.store, "status")
        if command:
            await Command.invoke(command, ctx)

    async def setup_team_channels(self, ctx: Context) -> None:
        if self.store.current_game is None:
            return

        if isinstance(self.store.current_game, ClassicGame):
            self.store.current_game = cast(ClassicGame, self.store.current_game)

            await self.channels.create_discord_channels(ctx)

            if self.store.current_game.radiant is None or self.store.current_game.dire is None:
                raise OneHeadException(f"Expected valid teams: {self.store.current_game.radiant}, {self.store.current_game.dire}")

            await self.channels.move_discord_channels(ctx)

    async def start_challenge(self, ctx: Context, duel_id: str) -> None:
        try:
            id = int(duel_id)
        except ValueError:
            await ctx.send(f"Invalid duel id: `{duel_id}`.")
            return
        else:
            target_challenge: Challenge | None = None
            for challenge in self.challenge_mode.challenges:
                if challenge.id == id:
                    target_challenge = challenge

            if target_challenge:
                await play_sound(ctx, "fight.mp3")
                self.store.current_game = target_challenge
                target_challenge.start()
                await ctx.send(
                    f"**Duel starting**: {target_challenge.challenger.mention} and {target_challenge.opponent.mention}, prepare to fight!"
                )
                await self.store.current_game.open_betting_window(ctx)
                await ctx.send("GL HF!")
            else:
                await ctx.send(f"Unable to find Duel ID: `{id}`.")
                await ctx.invoke(self.challenge_mode.list_challenges)

    async def start_classic_game(self, ctx: Context) -> None:
        signup_threshold_met: bool = await self.lobby.signup_check(ctx)
        if signup_threshold_met is False:
            return

        await play_sound(ctx, "start.mp3")
        metadata: Metadata = self.database.get_metadata()
        await ctx.send(f"Starting game: `Season {metadata.get('season')}`, Game `{metadata.get('game_id')}`.")

        await self.lobby.select_players(ctx)

        self.store.current_game = ClassicGame()
        self.store.current_game.start()
        self.lobby.disable_signups()

        (
            self.store.current_game.radiant, 
            self.store.current_game.dire,
        ) = await self.matchmaking.balance(ctx)

        await self.show_teams(ctx)
        await self.store.current_game.open_transfer_window(ctx)
        await self.store.current_game.open_betting_window(ctx)

        # We have to set up team channels after the transfer/betting windows as the bot plays sounds for certain commands.
        # This requires everyone to be in the same channel.
        await self.setup_team_channels(ctx)
        await ctx.send("Create Dota 2 Lobby and join with the above teams.")

        if self.store.current_game.in_progress():
            await ctx.send("GLHF")

            radiant: tuple[str, ...]
            dire: tuple[str, ...]
            radiant, dire = get_player_names(self.store.current_game.radiant, self.store.current_game.dire)

            log.info(f"Season {metadata['season']}, Game {metadata['game_id']} has started.")
            log.info(f"Radiant: {', '.join(radiant)}, Dire: {', '.join(dire)}.")

    async def update_database_with_classic_result(self, ctx: Context, result: Side) -> None:
        if self.store.current_game is None:
            raise OneHeadException("Failed to update database as there is no active game")

        if isinstance(self.store.current_game, ClassicGame) is False:
            raise OneHeadException(
                "Attempted to update database with a ClassicGame result when the active game is a Challenge"
            )

        self.store.current_game = cast(ClassicGame, self.store.current_game)
        if self.store.current_game.radiant is None or self.store.current_game.dire is None:
            raise OneHeadException("Unable to update database due to invalid teams")

        radiant_names: tuple[str, ...]
        dire_names: tuple[str, ...]

        radiant_names, dire_names = get_player_names(self.store.current_game.radiant, self.store.current_game.dire)

        if result == Side.RADIANT:

            await ctx.send("`Radiant` victory!")

            for player in radiant_names:
                member: Member | None = get_discord_member_from_name(ctx, player)

                if member is None:
                    continue

                self.database.modify(member.id, "win", 1, Operation.ADD)
                self.database.modify(member.id, "win_streak", 1, Operation.ADD)
                self.database.modify(member.id, "loss_streak", 0)
                self.database.modify(member.id, "rbucks", Betting.REWARD_ON_WIN, Operation.ADD)

            for player in dire_names:
                member: Member | None = get_discord_member_from_name(ctx, player)

                if member is None:
                    continue

                self.database.modify(member.id, "loss", 1, Operation.ADD)
                self.database.modify(member.id, "loss_streak", 1, Operation.ADD)
                self.database.modify(member.id, "win_streak", 0)
                self.database.modify(member.id, "rbucks", Betting.REWARD_ON_LOSS, Operation.ADD)

        elif result == Side.DIRE:

            await ctx.send("`Dire` victory!")

            for player in radiant_names:
                member: Member | None = get_discord_member_from_name(ctx, player)

                if member is None:
                    continue

                self.database.modify(member.id, "loss", 1, Operation.ADD)
                self.database.modify(member.id, "loss_streak", 1, Operation.ADD)
                self.database.modify(member.id, "win_streak", 0)
                self.database.modify(member.id, "rbucks", Betting.REWARD_ON_LOSS, Operation.ADD)

            for player in dire_names:
                member: Member | None = get_discord_member_from_name(ctx, player)

                if member is None:
                    continue

                self.database.modify(member.id, "win", 1, Operation.ADD)
                self.database.modify(member.id, "win_streak", 1, Operation.ADD)
                self.database.modify(member.id, "loss_streak", 0)
                self.database.modify(member.id, "rbucks", Betting.REWARD_ON_WIN, Operation.ADD)

    async def handle_classic_game_result(self, ctx: Context, result: str) -> None:
        self.store.current_game = cast(ClassicGame, self.store.current_game)
        
        if self.store.current_game.transfer_window_open():
            await ctx.send(
                "Cannot enter result as the transfer window for the game is currently open. Use the `!stop` command if you wish to abort the game."
            )
            return

        if self.store.current_game.betting_window_open():
            await ctx.send(
                "Cannot enter result as the betting window for the game is currently open. Use the `!stop` command if you wish to abort the game."
            )
            return

        result = result.lower()

        if result not in Side:
            await ctx.send(f"Must be either {Side.RADIANT} or {Side.DIRE}.")
            return

        result = cast(Side, result)

        await self.channels.move_back_to_lobby(ctx)

        log.info(f"{ctx.author.display_name} entered a result of {result}.")

        if self.store.current_game.radiant is None or self.store.current_game.dire is None:
            raise OneHeadException(f"Expected valid teams: {self.store.current_game.radiant}, {self.store.current_game.dire}")

        metadata: Metadata = self.database.get_metadata()

        log.info(f"Game {metadata['game_id']} has ended.")

        await play_sound(ctx, "result.mp3")

        await ctx.send("Updating scores...")
        await self.update_database_with_classic_result(ctx, result)

        command: Command | None = get_command_from_cog(self.scoreboard, "scoreboard")
        if command:
            await Command.invoke(command, ctx)

        metadata["game_id"] += 1
        self.database.update_metadata(metadata)

        if self.is_end_of_season():
            await ctx.send(f"Season `{metadata['season']}` has ended!")
            metadata["season"] += 1
            metadata["game_id"] = 1
            self.database.update_metadata(metadata)
            # TODO: Make a big song and dance about the end of an IHL season, present winners, go crazy.

        
    async def reset(self, ctx: Context, game_cancelled=False) -> None:
        if self.store.current_game and isinstance(self.store.current_game, Challenge):
            self.challenge_mode.challenges.remove(self.store.current_game)

        if game_cancelled:
            self.previous_game = None
        else:
            self.previous_game = self.store.current_game

        self.store.current_game = None
        if isinstance(self.previous_game, ClassicGame):
            self.lobby.clear_signups()

        create_task(voice_client_disconnect(ctx))
    
    def is_end_of_season(self) -> bool:
        metadata: Metadata = self.database.get_metadata()
        return metadata["game_id"] >= metadata["max_game_count"]