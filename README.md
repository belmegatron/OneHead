# OneHead

[![codecov](https://codecov.io/gh/belmegatron/onehead/branch/develop/graph/badge.svg)](https://codecov.io/gh/belmegatron/onehead)

> A Discord bot for hosting competitive 5v5 DOTA 2 In-House League (IHL) matches with automated team balancing, player ratings, and match management.

## Features

**Persistent Results** — Match results are stored in an external database, ensuring data persists across bot restarts.

**Leaderboard System** — Track player performance with an IHL rating system and view competitive rankings.

**Behavior Tracking** — Players can commend or report others based on in-game conduct.

**Smart Team Balancing** — Teams are automatically balanced using a hybrid rating that combines DOTA MMR and IHL performance.

**Automated Channel Management** — Players are automatically moved to team-specific voice channels during matches and returned to the lobby when games end.

**Admin Controls** — Comprehensive admin commands for starting/stopping games, managing the player pool, and handling registrations.

**Role-Based Permissions** — Control bot access through Discord roles (`IHL` for players, `IHL Admin` for administrators).

## Requirements

- [Docker](https://www.docker.com/products/docker-desktop)

## Configuration

OneHead uses `config.toml` for all settings. Copy `config_example.toml` to `config.toml` and customize it for your server:

```toml
[tinydb]
path = "season_10.json"

[discord]
token = "your_discord_bot_token_here"

[discord.channels]
lobby = "Lobby"
match = "Match"
```

## Installation

Build the Docker image:

```bash
docker build -t onehead:latest <install_dir_path>
```

Run the container:

```bash
docker run -d -v /usr/local/onehead/secrets:/app/secrets --name onehead onehead:latest
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.