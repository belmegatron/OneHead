import asyncio
from typing import TYPE_CHECKING

from discord.ext.commands import (Bot, BucketType, Cog, Command, Context,
                                  command, has_role, max_concurrency)

if TYPE_CHECKING:
    from common import Team


class Game:
    def __init__(self) -> None:
        
        self._active: bool = False
        self._cancel_event: asyncio.Event = asyncio.Event()
        self._transfer_window_open: bool = False
        self._betting_window_open: bool = False
        self._bets: list[dict] = []
        self._transactions: list[dict] = []
        
        self.radiant: Team | None = None
        self.dire: Team | None = None
        
    def active(self) -> bool:
        return self._active
    
    def in_progress(self) -> bool:
        return self._active
    
    def start(self) -> None:
        self._active = True
    
    def cancel(self) -> None:
        self._cancel_event.set()
        
    async def open_transfer_window(self, ctx) -> None:
        
        self._transfer_window_open = True
        await ctx.send(f"Player transfer window is now open for 2 minutes!")

        try:
            await asyncio.wait_for(self._cancel_event.wait(), timeout=120)
        except asyncio.TimeoutError:
            pass

        self._transfer_window_open = False
        await ctx.send(f"Player transfer window has now closed!")
        
    async def open_betting_window(self, ctx: Context) -> None:
        
        self._betting_window_open = True

        await ctx.send(f"Bets are now open for 5 minutes!")

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
        
    def transfer_window_open(self) -> bool:
        return self._transfer_window_open
    