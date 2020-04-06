# **OneHead**

OneHead is an IHL Discord Bot for hosting Dota 2 IHL Games.

## Requirements

* Docker

## Deploy with Docker

`cd <OneHead Directory>`

`docker build --build-arg GIT_OAUTH_KEY=<key> -t onehead:latest .`

`docker run -d onehead:latest`