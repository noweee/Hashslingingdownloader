#!/usr/bin/env bash
set -euo pipefail

BOT_DIR="${BOT_DIR:-/srv/server/bot}"
MC_DIR="${MC_DIR:-/srv/server/minecraft}"
BOT_SCREEN="${BOT_SCREEN:-hsd-bot}"
MC_SCREEN="${MC_SCREEN:-hsd-mc}"

usage() {
    cat <<EOF
Hash Slinging Server control

Usage:
  ./serverctl.sh start all
  ./serverctl.sh restart all
  ./serverctl.sh stop all

  ./serverctl.sh start bot
  ./serverctl.sh restart bot
  ./serverctl.sh stop bot

  ./serverctl.sh start mc
  ./serverctl.sh restart mc
  ./serverctl.sh stop mc

  ./serverctl.sh status

Shortcuts:
  ./serverctl.sh up       start all
  ./serverctl.sh reboot   restart all
  ./serverctl.sh down     stop all
EOF
}

screen_exists() {
    screen -ls | grep -q "[.]$1[[:space:]]"
}

require_screen() {
    if ! command -v screen >/dev/null 2>&1; then
        echo "screen is not installed. Run: sudo apt install -y screen"
        exit 1
    fi
}

start_bot() {
    require_screen
    if screen_exists "$BOT_SCREEN"; then
        echo "Bot is already running in screen: $BOT_SCREEN"
        return
    fi
    if [ ! -d "$BOT_DIR" ]; then
        echo "Bot folder not found: $BOT_DIR"
        exit 1
    fi
    if [ ! -f "$BOT_DIR/.env" ]; then
        echo "Bot .env not found: $BOT_DIR/.env"
        exit 1
    fi
    if [ ! -f "$BOT_DIR/.venv/bin/activate" ]; then
        echo "Bot virtual environment not found: $BOT_DIR/.venv"
        exit 1
    fi

    screen -dmS "$BOT_SCREEN" bash -lc "cd '$BOT_DIR' && set -a && source .env && set +a && source .venv/bin/activate && python bot.py"
    echo "Started bot in screen: $BOT_SCREEN"
}

stop_bot() {
    if screen_exists "$BOT_SCREEN"; then
        screen -S "$BOT_SCREEN" -X stuff $'\003'
        sleep 2
        screen -S "$BOT_SCREEN" -X quit >/dev/null 2>&1 || true
        echo "Stopped bot screen: $BOT_SCREEN"
    else
        echo "Bot screen is not running."
    fi

    pkill -f "$BOT_DIR/bot.py" >/dev/null 2>&1 || true
}

restart_bot() {
    stop_bot
    sleep 2
    start_bot
}

start_mc() {
    require_screen
    if screen_exists "$MC_SCREEN"; then
        echo "Minecraft is already running in screen: $MC_SCREEN"
        return
    fi
    if [ ! -d "$MC_DIR" ]; then
        echo "Minecraft folder not found: $MC_DIR"
        exit 1
    fi
    if [ ! -x "$MC_DIR/start.sh" ]; then
        echo "Minecraft start script not found or not executable: $MC_DIR/start.sh"
        echo "Run: chmod +x $MC_DIR/start.sh"
        exit 1
    fi

    screen -dmS "$MC_SCREEN" bash -lc "cd '$MC_DIR' && ./start.sh"
    echo "Started Minecraft in screen: $MC_SCREEN"
}

stop_mc() {
    if screen_exists "$MC_SCREEN"; then
        screen -S "$MC_SCREEN" -X stuff $'stop\r'
        echo "Sent Minecraft stop command."
        sleep 8
        screen -S "$MC_SCREEN" -X quit >/dev/null 2>&1 || true
        echo "Stopped Minecraft screen: $MC_SCREEN"
    else
        echo "Minecraft screen is not running."
    fi
}

restart_mc() {
    stop_mc
    sleep 3
    start_mc
}

start_all() {
    start_mc
    start_bot
}

stop_all() {
    stop_bot
    stop_mc
}

restart_all() {
    stop_all
    sleep 3
    start_all
}

status() {
    echo "Screens:"
    screen -ls || true
    echo
    echo "Minecraft port:"
    ss -ltnp 2>/dev/null | grep ':25565' || echo "Port 25565 is not listening."
    echo
    echo "Bot process:"
    pgrep -af "$BOT_DIR/bot.py" || echo "Bot process not found."
}

action="${1:-}"
target="${2:-}"

case "$action:$target" in
    start:all) start_all ;;
    restart:all) restart_all ;;
    stop:all) stop_all ;;
    start:bot) start_bot ;;
    restart:bot) restart_bot ;;
    stop:bot) stop_bot ;;
    start:mc|start:minecraft) start_mc ;;
    restart:mc|restart:minecraft) restart_mc ;;
    stop:mc|stop:minecraft) stop_mc ;;
    up:) start_all ;;
    reboot:) restart_all ;;
    down:) stop_all ;;
    status:) status ;;
    *) usage; exit 1 ;;
esac
