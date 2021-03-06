# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] 
- Add auto-kick feature for players who are AFK and signed up.
- Add separate scoreboard's for different games e.g. CSGO.

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