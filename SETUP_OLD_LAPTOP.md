# Old Laptop Server Setup

This guide is for moving the bot to another Windows computer so your main PC can be turned off.

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
- any rclone config file
- any Streamrip/Qobuz config containing account tokens

The repository is now set up to ignore those.

## Required Apps On The Old Laptop

Install these before cloning the bot:

1. Git for Windows
   - Download: https://git-scm.com/download/win

2. Python 3.12 or newer
   - Download: https://www.python.org/downloads/windows/
   - During install, check `Add python.exe to PATH`.

3. FFmpeg
   - Required by SpotDL and audio tools.
   - Easy install with winget:

```powershell
winget install Gyan.FFmpeg
```

4. rclone
   - Required for Google Drive upload/delete/link creation.

```powershell
winget install Rclone.Rclone
```

5. 7-Zip
   - Useful for archives and compatibility with the existing bot environment.

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

Your current `origin` points to the original public project, not your personal copy. Create your own private GitHub repository first.

Recommended: make it private because this bot is tied to your server setup.

Then from this computer, set your repository as the remote:

```powershell
git remote set-url origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git add .
git commit -m "Prepare portable Discord downloader server setup"
git push -u origin main
```

If your branch is named `master`, use this instead:

```powershell
git push -u origin master
```

## Clone On The Old Laptop

On the old laptop:

```powershell
cd $env:USERPROFILE\Documents
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git "SBPH Steal"
cd "SBPH Steal"
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
DISCORD_DECODE_CHANNEL=your_decode_info_channel_id
BOT_FOLDER=C:\Users\YOUR_WINDOWS_USER\Documents\SBPH Steal
RCLONE_DRIVES=gd
RCLONE_UPLOAD_PATH=
SHRINKEARN_API_KEY=your_shrinkearn_api_key
SHRINKEARN_API_URL=https://shrinkearn.com/api
```

Notes:

- `BOT_FOLDER` should be the full folder where the repo is cloned.
- Keep `RCLONE_DRIVES=gd` if your rclone remote is named `gd`.
- Leave `RCLONE_UPLOAD_PATH=` blank if files should upload to the root of that Drive remote.

## Set Up Google Drive With rclone

Run:

```powershell
rclone config
```

Use these choices:

- New remote: `n`
- Name: `gd`
- Storage: Google Drive
- Scope: full Drive access
- Service account file: leave blank
- Advanced config: no
- Auto authenticate in browser: yes
- Shared Drive: usually no, unless you specifically use a Shared Drive
- Keep remote: yes

Test it:

```powershell
rclone lsf gd:
```

If that lists files or returns without an auth error, rclone is ready.

## Set Up Qobuz / Streamrip

Run:

```powershell
rip config --open
```

If that only opens Notepad, that is fine. The config lives at:

```text
C:\Users\YOUR_WINDOWS_USER\AppData\Roaming\streamrip\config.toml
```

Make sure Qobuz login/token settings are configured the same way they are on this computer.

Fastest migration method:

1. On this computer, open:

```text
C:\Users\Admin\AppData\Roaming\streamrip\config.toml
```

2. On the old laptop, open:

```text
C:\Users\YOUR_WINDOWS_USER\AppData\Roaming\streamrip\config.toml
```

3. Copy the Qobuz-related settings from this computer to the old laptop.

Do not commit `config.toml` to GitHub.

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
h!dl <spotify-link>
h!dl <qobuz-link>
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
cd "$env:USERPROFILE\Documents\SBPH Steal"
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

If Qobuz fails:

- Check `C:\Users\YOUR_WINDOWS_USER\AppData\Roaming\streamrip\config.toml`.
- Make sure the old laptop has the same working Qobuz auth settings.

If Discord does not respond:

- Check `.env`.
- Make sure `DISCORD_BOT_TOKEN` is correct.
- Make sure the bot has permission to view/send/manage channels.
- Make sure Message Content Intent is enabled in the Discord Developer Portal.

If Google Drive upload/delete fails:

- Run `rclone lsf gd:`.
- If it asks for login or fails, run `rclone config` again.
