# Hash Slinging Downloader Server Setup

This guide moves Hash Slinging Downloader to another Windows computer so your main PC can be turned off.

## What Goes To GitHub

Commit the bot code, helper files, requirements, docs, and scripts.

Do not commit these local/private files:

- `.env`
- `.venv/`
- `download/`
- `daily_counters.json`
- `upload_registry.json`
- `last_upload.json`
- `*_log.txt`
- `rclone_logs.txt`
- any storage auth config
- any account/session config containing tokens

The repository is configured to ignore those files.

## Required Apps On The Old Laptop

Install these before cloning the bot:

1. Git for Windows
   - Download: https://git-scm.com/download/win

2. Python 3.12 or newer
   - Download: https://www.python.org/downloads/windows/
   - During install, check `Add python.exe to PATH`.

3. FFmpeg
   - Required for audio processing.

```powershell
winget install Gyan.FFmpeg
```

4. rclone
   - Required for storage upload, link creation, and automatic deletion.

```powershell
winget install Rclone.Rclone
```

5. 7-Zip
   - Useful for archive handling and server maintenance.

```powershell
winget install 7zip.7zip
```

6. Microsoft Visual C++ Redistributable
   - Some Python/audio packages may need it.

```powershell
winget install Microsoft.VCRedist.2015+.x64
```

After installing, close PowerShell and open a new PowerShell window.

Check the tools:

```powershell
git --version
python --version
ffmpeg -version
rclone version
```

## Create Your GitHub Repository

Create a private GitHub repository under your own account.

Then from this computer, set your private repository as the remote:

```powershell
git remote set-url origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

## Clone On The Old Laptop

On the old laptop:

```powershell
cd $env:USERPROFILE\Documents
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git "Hash Slinging Downloader"
cd "Hash Slinging Downloader"
```

## Create The Local .env File

Copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
notepad .env
```

Fill these values:

```env
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_APPLICATION_ID=your_discord_application_id
DISCORD_REQUEST_CHANNEL=your_request_channel_id
DISCORD_UPLOAD_CHANNEL=your_upload_channel_id
DISCORD_LOG_CHANNEL=your_log_channel_id
DISCORD_SUPPORTER_CHANNEL=your_supporter_info_channel_id
BOT_FOLDER=C:\Users\YOUR_WINDOWS_USER\Documents\Hash Slinging Downloader
RCLONE_DRIVES=gd
RCLONE_UPLOAD_PATH=
SHRINKEARN_API_KEY=your_shrinkearn_api_key
SHRINKEARN_API_URL=https://shrinkearn.com/api
```

Notes:

- `BOT_FOLDER` should be the full folder where the repo is cloned.
- Keep `RCLONE_DRIVES=gd` if your rclone remote is named `gd`.
- Leave `RCLONE_UPLOAD_PATH=` blank if files should upload to the root of that remote.

## Set Up Storage With rclone

Run:

```powershell
rclone config
```

Use these choices:

- New remote: `n`
- Name: `gd`
- Storage: the cloud storage provider you use for this bot
- Scope: full storage access
- Service account file: leave blank
- Advanced config: no
- Auto authenticate in browser: yes
- Shared/team storage: usually no, unless you specifically use one
- Keep remote: yes

Test it:

```powershell
rclone lsf gd:
```

If that lists files or returns without an auth error, storage is ready.

## Set Up The Download Account Session

The downloader backend keeps its own account/session file on each Windows user profile. Do not commit that file.

Fastest migration method:

1. On this computer, open the working backend config from your Windows user profile.
2. On the old laptop, open the same backend config path for that Windows user.
3. Copy only the working account/session settings.

If you prefer a fresh login, start the bot once and follow the terminal login prompts from the backend tool.

## First Run

From the cloned repo on the old laptop:

```powershell
.\run-bot.ps1
```

The script will:

- check for `rclone`
- check for `ffmpeg`
- create `.venv` if missing
- install Python packages from `requirements.txt`
- load `.env`
- start the Discord bot

When it says the bot is ready, test in Discord:

```text
h!ping
h!dl <link>
```

## Keeping It Running

For a simple server setup:

1. Plug in the old laptop.
2. Disable sleep while plugged in.
3. Start PowerShell.
4. Go to the bot folder.
5. Run:

```powershell
.\run-bot.ps1
```

Windows sleep setting:

```powershell
powercfg /change standby-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
```

## Updating The Old Laptop Later

When you change the bot on your main PC and push to GitHub, update the old laptop with:

```powershell
cd "$env:USERPROFILE\Documents\Hash Slinging Downloader"
git pull
.\run-bot.ps1
```

## Quick Troubleshooting

If `rclone` is missing:

```powershell
winget install Rclone.Rclone
```

If `ffmpeg` is missing:

```powershell
winget install Gyan.FFmpeg
```

If downloads fail:

- Check the backend account/session config on the old laptop.
- Make sure the old laptop has the same working account/session settings.

If Discord does not respond:

- Check `.env`.
- Make sure `DISCORD_BOT_TOKEN` is correct.
- Make sure the bot has permission to view/send/manage channels.
- Make sure Message Content Intent is enabled in the Discord Developer Portal.

If storage upload/delete fails:

- Run `rclone lsf gd:`.
- If it asks for login or fails, run `rclone config` again.
