# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.35.1] - 2022-05-11

### Changed
- No longer able to accidentally issue multiple calls to !start/!stop/!result.

## [1.35] - 2022-05-11

### Changed
- Simplified code used to balance teams, now always balances using adjusted MMR.

## [1.34] - 2022-05-04

### Changed
- Users can only signup/signout once every 30s in order to prevent spamming OneHead post-game.
- Users cannot signup/signout while a game is in progress.

## [1.33] - 2022-05-04

### Added
- Members signed up to play a game are automatically signed out if they move/are moved to the AFK channel.

## [1.32] - 2022-04-14

### Changed
- DynamoDB field names can't contain spaces, added '_' into streak fields.

## [1.31] - 2022-04-14

### Added
- Added a loss streak field that keeps track of the current loss streak.

### Changed
- Renamed 'streak' field to 'win streak'.
- Scoreboard now split over multiple messages if it exceeds the max message length enforced by Discord.

## [1.30] - 2022-04-06

### Added
- Added a streak field to the scoreboard that keeps track of the current win streak.

## [1.29] - 2022-04-03

### Changed
- A w/l results in a +/- 50 rating score (previously this was 25).

## [1.28] - 2022-03-06

### Changed
- The register command only accepts an MMR greater or equal to 1000.

## [1.26] - 2022-02-12

### Changed
- Python 3 cosmetic changes: f-strings, type hinting etc.

## [1.25] - 2022-02-09

### Changed
- Tidied up Dockerfile.

## [1.24] - 2022-02-08

### Changed
- Updated requirements.txt, removed mock dependency and bumped Python version requirement.

## [1.23] - 2021-03-19

### Added
- Added !mh command to provide other players with inspirational mental health quotes.
- Added !mmr command to show the MMR that is used internally for balancing teams.

## [1.22] - 2021-02-11

### Changed
- !summon command now mentions by role instead of by user to comply with Discord 1.5 changes and the addition of 'intents'.
- !signup command output tidied up.

## [1.21] - 2021-02-08

### Changed
- Fixed bug where stale reference to OneHeadPreGame object was present in the OneHeadBalance object. This was causing
  players who were not signed up to be present in the lineups produced when a game was started.

## [1.20] - 2021-02-07

### Changed
- Tidying up of imports and file names.
- Fixed bug with multiple instances of OneHead objects existing, all objects are now cogs and referenced through the 
  global commands.Bot object.

## [1.19] - 2020-05-21

### Added
- Added config.json and config_example.json to enable the user to configure their bot.
- Updated README.md with information on requirements, features and config.json

### Removed
- Removed .env file and python-dotenv dependency.

## [1.18] - 2020-05-14

### Added
- Added /src directory and moved onehead_*.py file there.
- Added supporting docstrings/comments throughout.

### Changed
- Updated README.MD to reflect changes to docker build command.
- Refactored code in OneHeadBalance.
- Moved OneHeadChannels into separate file for consistency.

### Removed
- Removed need for OAUTH key during build process.
- Removed code duplication in OneHeadCore/OneHeadChannels.
- Removed need to explicitly reference OneHead version number when calling pip install inside Dockerfile.


## [1.17] - 2020-05-11

### Changed
- Switched to using a CHANGELOG.md file with a full changelog rather than only showing the most recent change(s).
- The !version command will now provide a link to CHANGELOG.md

## [1.16] - 2020-05-10
### Added
- All user commands now require IHL discord role.
### Changed
- Fixed the 'deregister' command, can now remove a player from the IHL database by typing !deregister \<name\>.


## [1.15] - 2020-05-05
### Changed
- Balancing teams now factors in both IHL rating and MMR. This is done by adding the difference between your IHL rating 
    and baseline rating (1500) to your MMR.
    
    e.g. IHL Rating = 1900 and MMR = 5000. Adjusted rating = 5000 + 400 == 5400.

## [1.14] - 2020-04-29
### Changed
- If there are more than 10 signups, players will be randomly selected to be placed on the bench. This will mean that
    they will not be able to play.
    
## [1.13] - 2020-04-29
### Changed
- Fixed bug when performing check to see if IHL Discord Channels already exist. This stopped players from being 
    moved channel and also resulted in duplicate channels.

## [1.12] - 2020-04-28
### Removed
- IHL Channels are no longer deleted upon stopping a game.

## [1.11] - 2020-04-20

### Added
- Patch note summary now available when using the !version command.
### Changed
- Picks and Nominations during a CM game are now case insensitive.
- Time to pick during a CM game has been increased from 20s to 30s.

## [1.10] - 2020-04-15

### Added
- Added Captain's Mode. Can be initiated by typing '!start cm'.
    Captains are nominated using the '!nominate' command and picks are made by the nominated captains using the '!pick'
    command.

## [1.0] - 2020-04-12

### Added
- Added version.py for storing version information.
- Added version command which displays the current version of OneHead.
- Added a remove command which allows an IHL Admin to remove a player from the signup pool.

### Changed
- Signups now reset after a game has finished.
