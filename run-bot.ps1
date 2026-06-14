$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repo

$wingetLinks = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links"
$sevenZip = "C:\Program Files\7-Zip"
$venvScripts = Join-Path $repo ".venv\Scripts"
$extraPaths = @($venvScripts, $wingetLinks, $sevenZip) | Where-Object { Test-Path $_ }
$env:PATH = ($extraPaths + $env:PATH.Split(";")) -join ";"

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
}

& "$repo\.venv\Scripts\python.exe" "$repo\bot.py"
