# **OneHead**

OneHead is a Discord Bot for hosting 5vs5 competitive DOTA 2 games in an In-House League (IHL).

## Features

- ### Persistent Results
    Results are stored in an external database. They will therefore be persisted, even when OneHead is no longer running.
- ### Leaderboard
    Players can view a leaderboard which is based on an IHL Rating.
- ### Team Balancing
    - #### Rating-based
        Teams are balanced by an internal rating which incorporates both the player's DOTA MMR and their IHL rating.
    - #### Captains
        Players nominate two captains who will in turn pick players to join their team.
- ### Automated Discord Channel Admin
    OneHead automatically handles moving players to separate channels at the start of a game and moves them back to a shared lobby upon game completion.
- ### Admin Commands
    Admins are able to simply start/stop games in addition to removing players from the signup pool, or deregister them entirely.
- ### Discord Role-Based Permissions
    The use of the bot can be controlled by assigning Discord Roles to players who want to interact
    with the bot. There are currently two roles - "IHL" and "IHL Admin".


## Requirements

- [Docker](https://www.docker.com/products/docker-desktop)

### Amazon Web Services (AWS)

 If you do not have an account, register [here](https://aws.amazon.com/console/).

#### Required

- [AWS CLI](https://aws.amazon.com/cli/) - Required for authenticating to AWS and if needed, pushing Docker Images to
your Elastic Container Registry (ECR).
- [DynamoDB](https://aws.amazon.com/dynamodb/) - AWS Free Tier!

#### Optional (Remote Hosting Only)
- [Identity and Access Management (IAM)](https://aws.amazon.com/iam/)
- [Elastic Container Registry (ECR)](https://aws.amazon.com/ecr/)
- [Elastic Container Service (ECS)](https://aws.amazon.com/ecs/)

## Configure

All OneHead settings that can be configured are stored in `config.json`. This 
will be copied over to your container during `docker build` process.

An example has been provided in `config_example.json`. This can be used
as the basis for your own `config.json`.

## Setup Guide

Coming Soon!
 
## Build

`docker build -t onehead:latest <install_dir path>`


## Run

`docker run -d -v ${HOME}/.aws/credentials:/root/.aws/credentials:ro onehead:latest`
