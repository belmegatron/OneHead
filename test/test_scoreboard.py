from unittest.mock import Mock

import discord.ext.test as dpytest
import pytest
from conftest import add_ihl_role
from discord.ext.commands import Bot, errors

from onehead.common import OneHeadException
from onehead.scoreboard import ScoreBoard


class TestScoreboard:
    @pytest.mark.asyncio
    async def test_no_ihl_role(self, bot: Bot) -> None:
        with pytest.raises(errors.MissingRole):
            await dpytest.message("!sb")

    @pytest.mark.asyncio
    async def test_empty_scoreboard(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")

        scoreboard: ScoreBoard = bot.get_cog("ScoreBoard")
        scoreboard.database.get_all = Mock()
        scoreboard.database.get_all.return_value = []

        with pytest.raises(OneHeadException):
            await dpytest.message("!sb")

    @pytest.mark.asyncio
    async def test_success(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")

        scoreboard: ScoreBoard = bot.get_cog("ScoreBoard")
        scoreboard.database.get_all = Mock()
        scoreboard.database.get_all.return_value = [
            {
                "name": "RBEEZAY",
                "win": 4,
                "loss": 3,
                "mmr": 3650,
                "win_streak": 3,
                "loss_streak": 0,
                "rbucks": 0.0,
                "reports": 24,
                "commends": 26,
                "behaviour": 7400,
                "%": 57.1,
                "rating": 1550,
                "#": 6,
            },
            {
                "name": "HARRY",
                "win": 7,
                "loss": 3,
                "mmr": 4000,
                "win_streak": 1,
                "loss_streak": 0,
                "rbucks": 2050,
                "reports": 6,
                "commends": 2,
                "behaviour": 8700,
                "%": 70.0,
                "rating": 1700,
                "#": 1,
            },
            {
                "name": "PECRO",
                "win": 4,
                "loss": 7,
                "mmr": 1930,
                "win_streak": 1,
                "loss_streak": 0,
                "rbucks": 1250,
                "reports": 0,
                "commends": 0,
                "behaviour": 10000,
                "%": 36.4,
                "rating": 1350,
                "#": 18,
            },
            {
                "name": "GEE",
                "win": 4,
                "loss": 2,
                "mmr": 1720,
                "win_streak": 0,
                "loss_streak": 1,
                "rbucks": 350,
                "reports": 0,
                "commends": 0,
                "behaviour": 10000,
                "%": 66.7,
                "rating": 1600,
                "#": 5,
            },
            {
                "name": "THANOS",
                "win": 8,
                "loss": 5,
                "mmr": 1290,
                "win_streak": 0,
                "loss_streak": 1,
                "rbucks": 750,
                "reports": 0,
                "commends": 0,
                "behaviour": 10000,
                "%": 61.5,
                "rating": 1650,
                "#": 2,
            },
            {
                "name": "RUGOR",
                "win": 1,
                "loss": 0,
                "mmr": 2000,
                "win_streak": 1,
                "loss_streak": 0,
                "rbucks": 300,
                "reports": 0,
                "commends": 0,
                "behaviour": 10000,
                "%": 100.0,
                "rating": 1550,
                "#": 6,
            },
            {
                "name": "RICH",
                "win": 2,
                "loss": 1,
                "mmr": 2900,
                "win_streak": 0,
                "loss_streak": 1,
                "rbucks": 350,
                "reports": 0,
                "commends": 0,
                "behaviour": 10000,
                "%": 66.7,
                "rating": 1550,
                "#": 6,
            },
            {
                "name": "JAMES",
                "win": 7,
                "loss": 4,
                "mmr": 2000,
                "win_streak": 0,
                "loss_streak": 1,
                "rbucks": 900,
                "reports": 0,
                "commends": 0,
                "behaviour": 10000,
                "%": 63.6,
                "rating": 1650,
                "#": 2,
            },
            {
                "name": "SCOUT",
                "win": 0,
                "loss": 0,
                "mmr": 2400,
                "win_streak": 0,
                "loss_streak": 0,
                "rbucks": 100,
                "reports": 0,
                "commends": 0,
                "behaviour": 10000,
                "%": 0,
                "rating": 1500,
                "#": 10,
            },
            {
                "name": "ZEED",
                "win": 6,
                "loss": 3,
                "mmr": 2400,
                "win_streak": 0,
                "loss_streak": 2,
                "rbucks": 850,
                "reports": 0,
                "commends": 0,
                "behaviour": 10000,
                "%": 66.7,
                "rating": 1650,
                "#": 2,
            },
        ]

        await dpytest.message("!sb")
        assert (
            dpytest.verify()
            .message()
            .content(
                "**IGC Leaderboard** ```\n  #  name       win    loss      %    rating    win_streak    loss_streak    behaviour\n---  -------  -----  ------  -----  --------  ------------  -------------  -----------\n  1  HARRY        7       3   70        1700             1              0         8700\n  2  THANOS       8       5   61.5      1650             0              1        10000\n  2  JAMES        7       4   63.6      1650             0              1        10000\n  2  ZEED         6       3   66.7      1650             0              2        10000\n  5  GEE          4       2   66.7      1600             0              1        10000\n  6  RBEEZAY      4       3   57.1      1550             3              0         7400\n  6  RUGOR        1       0  100        1550             1              0        10000\n  6  RICH         2       1   66.7      1550             0              1        10000\n  9  SCOUT        0       0    0        1500             0              0        10000\n 10  PECRO        4       7   36.4      1350             1              0        10000```"
            )
        )

    @pytest.mark.asyncio
    async def test_scoreboard_length_greater_than_max_discord_message_size(self, bot: Bot) -> None:
        await add_ihl_role(bot, "IHL")

        scoreboard: ScoreBoard = bot.get_cog("ScoreBoard")
        scoreboard.database.get_all = Mock()
        scoreboard.database.get_all.return_value = [
            {
                "name": "RBEEZAY",
                "win": 4,
                "loss": 3,
                "mmr": 3650,
                "win_streak": 3,
                "loss_streak": 0,
                "rbucks": 0.0,
                "reports": 24,
                "commends": 26,
                "behaviour": 7400,
            },
            {
                "name": "HARRY",
                "win": 7,
                "loss": 3,
                "mmr": 4000,
                "win_streak": 1,
                "loss_streak": 0,
                "rbucks": 2050,
                "reports": 6,
                "commends": 2,
                "behaviour": 8700,
            },
            {
                "name": "PECRO",
                "win": 4,
                "loss": 7,
                "mmr": 1930,
                "win_streak": 1,
                "loss_streak": 0,
                "rbucks": 1250,
                "reports": 0,
                "commends": 0,
                "behaviour": 10000,
            },
            {
                "name": "GEE",
                "win": 4,
                "loss": 2,
                "mmr": 1720,
                "win_streak": 0,
                "loss_streak": 1,
                "rbucks": 350,
                "reports": 0,
                "commends": 0,
                "behaviour": 10000,
            },
            {
                "name": "THANOS",
                "win": 8,
                "loss": 5,
                "mmr": 1290,
                "win_streak": 0,
                "loss_streak": 1,
                "rbucks": 750,
                "reports": 0,
                "commends": 0,
                "behaviour": 10000,
            },
            {
                "name": "RUGOR",
                "win": 1,
                "loss": 0,
                "mmr": 2000,
                "win_streak": 1,
                "loss_streak": 0,
                "rbucks": 300,
                "reports": 0,
                "commends": 0,
                "behaviour": 10000,
            },
            {
                "name": "RICH",
                "win": 2,
                "loss": 1,
                "mmr": 2900,
                "win_streak": 0,
                "loss_streak": 1,
                "rbucks": 350,
                "reports": 0,
                "commends": 0,
                "behaviour": 10000,
            },
            {
                "name": "JAMES",
                "win": 7,
                "loss": 4,
                "mmr": 2000,
                "win_streak": 0,
                "loss_streak": 1,
                "rbucks": 900,
                "reports": 0,
                "commends": 0,
                "behaviour": 10000,
            },
            {
                "name": "SCOUT",
                "win": 0,
                "loss": 0,
                "mmr": 2400,
                "win_streak": 0,
                "loss_streak": 0,
                "rbucks": 100,
                "reports": 0,
                "commends": 0,
                "behaviour": 10000,
            },
            {
                "name": "ZEED",
                "win": 6,
                "loss": 3,
                "mmr": 2400,
                "win_streak": 0,
                "loss_streak": 2,
                "rbucks": 850,
                "reports": 0,
                "commends": 0,
                "behaviour": 10000,
            },
            {
                "name": "ZEE",
                "win": 1,
                "loss": 3,
                "mmr": 3000,
                "win_streak": 0,
                "loss_streak": 2,
                "rbucks": 500,
                "reports": 0,
                "commends": 0,
                "behaviour": 10000,
            },
            {
                "name": "JORDAN",
                "win": 1,
                "loss": 1,
                "mmr": 1000,
                "win_streak": 1,
                "loss_streak": 0,
                "rbucks": 200,
                "reports": 0,
                "commends": 0,
                "behaviour": 10000,
            },
            {
                "name": "LUKE",
                "win": 4,
                "loss": 6,
                "mmr": 2000,
                "win_streak": 2,
                "loss_streak": 0,
                "rbucks": 950,
                "reports": 0,
                "commends": 0,
                "behaviour": 10000,
            },
            {
                "name": "SPONGE",
                "win": 0,
                "loss": 1,
                "mmr": 1800,
                "win_streak": 0,
                "loss_streak": 1,
                "rbucks": 150,
                "reports": 0,
                "commends": 0,
                "behaviour": 10000,
            },
            {
                "name": "JEFFERIES",
                "win": 6,
                "loss": 6,
                "mmr": 1000,
                "win_streak": 1,
                "loss_streak": 0,
                "rbucks": 850,
                "reports": 0,
                "commends": 0,
                "behaviour": 10000,
            },
            {
                "name": "JOSH",
                "win": 1,
                "loss": 2,
                "mmr": 2240,
                "win_streak": 1,
                "loss_streak": 0,
                "rbucks": 300,
                "reports": 0,
                "commends": 0,
                "behaviour": 10000,
            },
            {
                "name": "LAURENCE",
                "win": 3,
                "loss": 7,
                "mmr": 3520,
                "win_streak": 0,
                "loss_streak": 1,
                "rbucks": 750,
                "reports": 0,
                "commends": 0,
                "behaviour": 10000,
            },
            {
                "name": "JAQ",
                "win": 0,
                "loss": 2,
                "mmr": 1000,
                "win_streak": 0,
                "loss_streak": 2,
                "rbucks": 50,
                "reports": 0,
                "commends": 0,
                "behaviour": 10000,
            },
            {
                "name": "ERIC",
                "win": 6,
                "loss": 5,
                "mmr": 4000,
                "win_streak": 2,
                "loss_streak": 0,
                "rbucks": 850,
                "reports": 0,
                "commends": 0,
                "behaviour": 10000,
            },
            {
                "name": "EDD",
                "win": 0,
                "loss": 4,
                "mmr": 3000,
                "win_streak": 0,
                "loss_streak": 4,
                "rbucks": 600,
                "reports": 0,
                "commends": 0,
                "behaviour": 10000,
            },
        ]

        await dpytest.message("!sb")
        assert (
            dpytest.verify()
            .message()
            .content(
                "**IGC Leaderboard** ```\n  #  name         win    loss      %    rating    win_streak    loss_streak    behaviour\n---  ---------  -----  ------  -----  --------  ------------  -------------  -----------\n  1  HARRY          7       3   70        1700             1              0         8700\n  2  THANOS         8       5   61.5      1650             0              1        10000\n  2  JAMES          7       4   63.6      1650             0              1        10000\n  2  ZEED           6       3   66.7      1650             0              2        10000\n  5  GEE            4       2   66.7      1600             0              1        10000\n  6  RBEEZAY        4       3   57.1      1550             3              0         7400\n  6  RUGOR          1       0  100        1550             1              0        10000\n  6  RICH           2       1   66.7      1550             0              1        10000\n  6  ERIC           6       5   54.5      1550             2              0        10000\n 10  SCOUT          0       0    0        1500             0              0        10000\n 10  JORDAN         1       1   50        1500             1              0        10000\n 10  JEFFERIES      6       6   50        1500             1              0        10000\n 13  SPONGE         0       1    0        1450             0              1        10000\n 13  JOSH           1       2   33.3      1450             1              0        10000\n 15  ZEE            1       3   25        1400             0              2        10000\n 15  LUKE           4       6   40        1400             2              0        10000\n 15  JAQ            0       2    0        1400             0              2        10000\n 18  PECRO          4       7   36.4      1350             1              0        10000\n 19  LAURENCE       3       7   30        1300             0              1        10000```"
            )
        )
        assert (
            dpytest.verify()
            .message()
            .content(
                "**IGC Leaderboard** ```\n\n 19  EDD            0       4    0        1300             0              4        10000```"
            )
        )
