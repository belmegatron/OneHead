from unittest.mock import Mock

import discord.ext.test as dpytest
import pytest
from conftest import add_ihl_role, TEST_USER
from discord import Embed, colour
from discord.ext.commands import Bot, errors
from discord.member import Member

from onehead.betting import Bet
from onehead.common import Side
from onehead.core import Core


class TestBets:
    @pytest.mark.asyncio
    async def test_no_ihl_role(self, bot: Bot) -> None:
        with pytest.raises(errors.MissingRole):
            await dpytest.message("!bets")

    @pytest.mark.asyncio
    async def test_no_bets(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")

        embed: Embed = Embed(colour=colour.Colour.green())
        embed.add_field(name="Active Bets", value="``````")

        await dpytest.message("!bets")
        assert dpytest.verify().message().embed(embed)

    @pytest.mark.asyncio
    async def test_success(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")

        core: Core = bot.get_cog("Core")
        core.current_game._bets.append(Bet("dire", 1000, "RBEEZAY"))

        embed: Embed = Embed(colour=colour.Colour.green())
        embed.add_field(
            name="Active Bets",
            value="```side      stake  player\n------  -------  --------\ndire       1000  RBEEZAY```",
        )
        await dpytest.message("!bets")
        assert dpytest.verify().message().embed(embed)


class TestPlaceBet:
    @pytest.mark.asyncio
    async def test_no_ihl_role(self, bot: Bot) -> None:
        with pytest.raises(errors.MissingRole):
            await dpytest.message("!bets")

    @pytest.mark.asyncio
    async def test_betting_window_closed(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")
        await dpytest.message("!bet dire all")
        assert dpytest.verify().message().content("Betting window closed.")

    @pytest.mark.asyncio
    async def test_player_does_not_exist(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")
        core: Core = bot.get_cog("Core")
        core.current_game._betting_window_open = True
        await dpytest.message(f"!bet {Side.RADIANT} all")
        assert dpytest.verify().message().content(f"Unable to find {TEST_USER} in database.")

    @pytest.mark.asyncio
    async def test_available_balance_is_zero(self, bot: Bot) -> None:
        member: Member = await dpytest.member_join(name="RBEEZAY")
        await add_ihl_role(bot, "IHL", "RBEEZAY")
        core: Core = bot.get_cog("Core")

        core.database.get = Mock()
        core.database.get.return_value = {"name": "RBEEZAY", "rbucks": 0}

        core.current_game._betting_window_open = True
        await dpytest.message(f"!bet {Side.RADIANT} all", 0, member)
        assert dpytest.verify().message().content("RBEEZAY cannot bet as they have no available RBUCKS.")

    @pytest.mark.asyncio
    async def test_invalid_side(self, bot: Bot) -> None:
        member: Member = await dpytest.member_join(name="RBEEZAY")
        await add_ihl_role(bot, "IHL", "RBEEZAY")
        core: Core = bot.get_cog("Core")

        core.database.get = Mock()
        core.database.get.return_value = {"name": "RBEEZAY", "rbucks": 100}

        core.current_game._betting_window_open = True
        await dpytest.message("!bet derp all", 0, member)
        assert dpytest.verify().message().content("RBEEZAY - Cannot bet on derp - Must be either Radiant/Dire.")

    @pytest.mark.asyncio
    async def test_stake_not_valid_int(self, bot: Bot) -> None:
        member: Member = await dpytest.member_join(name="RBEEZAY")
        await add_ihl_role(bot, "IHL", "RBEEZAY")
        core: Core = bot.get_cog("Core")

        core.database.get = Mock()
        core.database.get.return_value = {"name": "RBEEZAY", "rbucks": 100}

        core.current_game._betting_window_open = True
        await dpytest.message(f"!bet {Side.RADIANT} foobar", 0, member)
        assert (
            dpytest.verify().message().content("RBEEZAY - foobar is not a valid number of RBUCKS to place a bet with.")
        )

    @pytest.mark.asyncio
    async def test_stake_negative_int(self, bot: Bot) -> None:
        member: Member = await dpytest.member_join(name="RBEEZAY")
        await add_ihl_role(bot, "IHL", "RBEEZAY")
        core: Core = bot.get_cog("Core")

        core.database.get = Mock()
        core.database.get.return_value = {"name": "RBEEZAY", "rbucks": 100}

        core.current_game._betting_window_open = True
        await dpytest.message(f"!bet {Side.RADIANT} -100", 0, member)
        assert dpytest.verify().message().content("RBEEZAY - Bet stake must be greater than 0.")

    @pytest.mark.asyncio
    async def test_stake_greater_than_balance(self, bot: Bot) -> None:
        member: Member = await dpytest.member_join(name="RBEEZAY")
        await add_ihl_role(bot, "IHL", "RBEEZAY")
        core: Core = bot.get_cog("Core")

        core.database.get = Mock()
        record = {"name": "RBEEZAY", "rbucks": 100}
        core.database.get.return_value = record

        core.current_game._betting_window_open = True
        stake: int = record["rbucks"] + 100
        await dpytest.message(f"!bet {Side.RADIANT} {stake:.0f}", 0, member)
        assert (
            dpytest.verify()
            .message()
            .content(
                f"Unable to place bet - RBEEZAY tried to stake {stake:.0f} RBUCKS but only has {record['rbucks']:.0f} RBUCKS available."
            )
        )

    @pytest.mark.asyncio
    async def test_success(self, bot: Bot) -> None:
        member: Member = await dpytest.member_join(name="RBEEZAY")
        await add_ihl_role(bot, "IHL", "RBEEZAY")
        core: Core = bot.get_cog("Core")

        core.database.get = Mock()
        record = {"name": "RBEEZAY", "rbucks": 100}
        core.database.get.return_value = record
        core.database.modify = Mock()

        core.current_game._betting_window_open = True
        await dpytest.message(f"!bet {Side.RADIANT} all", 0, member)
        assert (
            dpytest.verify()
            .message()
            .content(f"RBEEZAY has placed a bet of {record['rbucks']:.0f} RBUCKS on {Side.RADIANT.title()}.")
        )
