from unittest.mock import AsyncMock, MagicMock

import pytest
from discord.errors import ClientException

from onehead.common import play_sound


class TestPlaySound:
    @pytest.mark.asyncio
    async def test_success(self, bot) -> None:
        def mock_play(_, *, after=None):
            if after:
                after(MagicMock())

        ctx = AsyncMock()
        ctx.voice_client.play = mock_play

        await play_sound(ctx, "start.mp3")

    @pytest.mark.asyncio
    async def test_ffmpeg_fails_to_play(self, bot) -> None:
        def mock_play(_, *, after=None):
            raise ClientException("oops!")

        ctx = AsyncMock()
        ctx.voice_client.play = mock_play

        await play_sound(ctx, "start.mp3")
