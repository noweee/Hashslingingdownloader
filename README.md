# Hash Slinging Downloader

Hash Slinging Downloader is a private Discord download assistant for the Hash Slinging Downloader Community.

The bot accepts download requests in Discord, prepares the package, uploads it to configured storage, and sends the requester a private delivery link. Runtime secrets, account sessions, logs, and generated downloads stay local and should not be committed.

## Windows Server Setup

For the full old-laptop/server setup, follow:

[SETUP_OLD_LAPTOP.md](SETUP_OLD_LAPTOP.md)

## Quick Start

```powershell
Copy-Item .env.example .env
notepad .env
.\run-bot.ps1
```

`run-bot.ps1` will create the Python virtual environment if needed, install Python packages, load `.env`, and start the bot.

## Local Files Not For GitHub

Keep these on the machine only:

- `.env`
- `.venv/`
- `download/`
- local account/session config files
- log files
- daily counters and upload registry files

## Discord Command

```text
h!dl <link>
```

Quality, limits, and delivery method are decided from the requester's Discord roles.
