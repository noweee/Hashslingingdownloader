# Push The Bot To Your GitHub Repo

Use this when you want to move the project into your own GitHub repository and later clone it on another Windows machine.

## 1. Create your GitHub repo

1. Sign in to GitHub.
2. Create a new repository under your account.
3. Use a private repo if you want the bot files kept private.
4. Do not add a README, license, or `.gitignore` from GitHub if this repo already has them.

## 2. Check your local repo

Make sure you are inside the bot folder:

```powershell
git status --short
```

Review the changes and make sure no secrets are sitting in tracked files.

Files that should stay local:

- `.env`
- `.venv/`
- `download/`
- `daily_counters.json`
- `upload_registry.json`
- `last_upload.json`
- log files
- account/session files

## 3. Point the repo at your GitHub repo

Replace the remote URL with your own repo:

```powershell
git remote set-url origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git remote -v
```

## 4. Stage and commit the project

```powershell
git add .
git commit -m "Prepare Hash Slinging Downloader for GitHub"
```

If Git asks for your identity, set it once:

```powershell
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

## 5. Push to GitHub

```powershell
git push -u origin main
```

If your default branch is not `main`, check it first:

```powershell
git branch
```

Then push that branch name instead.

## 6. Clone on the other computer

On the old laptop or server machine:

```powershell
cd $env:USERPROFILE\Documents
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git "Hash Slinging Downloader"
cd "Hash Slinging Downloader"
```

## 7. Set up the local config

Copy the environment template and fill in your local values:

```powershell
Copy-Item .env.example .env
notepad .env
```

Then set the Discord token, channel IDs, storage settings, and any local secrets.

## 8. Start the bot

```powershell
.\run-bot.ps1
```

That script will create the virtual environment if needed, install packages, load `.env`, and launch the bot.

