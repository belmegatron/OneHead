import asyncio

from discord.ext.commands import Context

from onehead.common import Bet, PlayerTransfer, Team


class Game:
    def __init__(self) -> None:
        self._in_progress: bool = False
        self._cancel_event: asyncio.Event = asyncio.Event()
        self._transfer_window_open: bool = False
        self._betting_window_open: bool = False
        self._bets: list[Bet] = []
        self._player_transfers: list[PlayerTransfer] = []
        self._commends: dict[str, list[str]] = {}
        self._reports: dict[str, list[str]] = {}

        self.radiant: Team | None = None
        self.dire: Team | None = None

    def in_progress(self) -> bool:
        return self._in_progress

    def start(self) -> None:
        self._in_progress = True

    def cancel(self) -> None:
        self._cancel_event.set()
        self._in_progress: bool = False

    async def open_transfer_window(self, ctx: Context) -> None:
        self._transfer_window_open = True
        await ctx.send("Player transfer window is now open for 2 minutes!")

        try:
            await asyncio.wait_for(self._cancel_event.wait(), timeout=120)
        except asyncio.TimeoutError:
            pass

        self._transfer_window_open = False
        await ctx.send("Player transfer window has now closed!")

    async def open_betting_window(self, ctx: Context) -> None:
        self._betting_window_open = True

        await ctx.send("Bets are now open for 5 minutes!")

        try:
            await asyncio.wait_for(self._cancel_event.wait(), timeout=240)
        except asyncio.TimeoutError:
            await ctx.send("1 minute remaining for bets!")
            try:
                await asyncio.wait_for(self._cancel_event.wait(), timeout=60)
            except asyncio.TimeoutError:
                pass
        finally:
            self._betting_window_open = False
            await ctx.send("Bets are now closed!")

    def betting_window_open(self) -> bool:
        return self._betting_window_open

    def transfer_window_open(self) -> bool:
        return self._transfer_window_open

    def get_bets(self) -> list[Bet]:
        return self._bets

    def get_player_transfers(self) -> list[PlayerTransfer]:
        return self._player_transfers

    def has_been_previously_commended(self, commender: str, commendee: str) -> bool:
        commends: list[str] | None = self._commends.get(commendee)
        return commends is not None and commender in commends

    def has_been_previously_reported(self, reporter: str, reportee: str) -> bool:
        reports: list[str] | None = self._reports.get(reportee)
        return reports is not None and reporter in reports

    def add_report(self, reporter: str, reportee: str) -> None:
        updated_reports: list[str] | None = self._reports.get(reportee)
        if updated_reports is None:
            self._reports[reportee] = [reporter]
        else:
            updated_reports.append(reporter)

    def add_commend(self, commender: str, commendee: str) -> None:
        updated_commends: list[str] | None = self._commends.get(commendee)
        if updated_commends is None:
            self._commends[commendee] = [commender]
        else:
            updated_commends.append(commender)
