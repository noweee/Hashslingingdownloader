$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repo

$wingetLinks = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links"
$sevenZip = "C:\Program Files\7-Zip"
$venvScripts = Join-Path $repo ".venv\Scripts"
$extraPaths = @($venvScripts, $wingetLinks, $sevenZip) | Where-Object { Test-Path $_ }
$env:PATH = ($extraPaths + $env:PATH.Split(";")) -join ";"

function Find-Python {
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        return @{ Command = "py"; Arguments = @("-3") }
    }
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return @{ Command = $python.Source; Arguments = @() }
    }
    throw "Python 3 was not found. Install Python 3.12+ first, then run this script again."
}

function Require-Command($Name, $InstallHint) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name was not found. $InstallHint"
    }
}

Require-Command "rclone" "Install rclone and run 'rclone config' before starting the bot."
Require-Command "ffmpeg" "Install FFmpeg and make sure it is available in PATH."

if (-not (Test-Path (Join-Path $venvScripts "python.exe"))) {
    $pythonCmd = Find-Python
    Write-Host "Creating Python virtual environment..."
    & $pythonCmd.Command @($pythonCmd.Arguments) -m venv "$repo\.venv"
}

Write-Host "Installing/updating Python packages..."
& "$repo\.venv\Scripts\python.exe" -m pip install --upgrade pip
& "$repo\.venv\Scripts\python.exe" -m pip install -r "$repo\requirements.txt"

$envFile = Join-Path $repo ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) {
            return
        }
        $parts = $line.Split("=", 2)
        [Environment]::SetEnvironmentVariable($parts[0].Trim(), $parts[1].Trim(), "Process")
    }
} else {
    throw ".env was not found. Copy .env.example to .env and fill in your Discord, rclone, and ShrinkEarn settings."
}

& "$repo\.venv\Scripts\python.exe" "$repo\bot.py"
