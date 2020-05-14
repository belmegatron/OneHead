# **OneHead**

OneHead is a Discord Bot for hosting 5v5 Competitive DOTA 2 games.

It has been designed to be hosted on AWS and store all player data in an AWS DynamoDB.
## Requirements
- An AWS Account.
- Docker.
- DynamoDB hosted on AWS.

## Configuration

### AWS

#### Hosting the Container
The simplest way to host this on AWS is to upload the Docker image
to ECR and then create/host a container using FARGATE.

 
## Build

`docker build -t onehead:latest <install_dir path>`

## Run

`docker run -d onehead:latest`