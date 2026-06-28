import json
import os
from pathlib import Path


def _as_int(value, name, required=False):
    if value in (None, ""):
        if required:
            raise ValueError(f"{name} is required")
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a Discord numeric ID") from exc


def _as_positive_int(value, name, default):
    if value in (None, ""):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a number") from exc
    if parsed <= 0:
        raise ValueError(f"{name} must be greater than 0")
    return parsed


def load_config():
    config_path = Path("config.json")
    if not config_path.is_file():
        raise SystemExit("'config.json' not found! Please add it and try again.")

    with config_path.open() as file:
        config = json.load(file)

    config["token"] = os.getenv("DISCORD_BOT_TOKEN", config.get("token", ""))
    config["application_id"] = os.getenv("DISCORD_APPLICATION_ID", config.get("application_id", ""))
    config["request_channel"] = _as_int(
        os.getenv("DISCORD_REQUEST_CHANNEL", config.get("request_channel")),
        "request_channel",
        required=True,
    )
    config["upload_channel"] = _as_int(
        os.getenv("DISCORD_UPLOAD_CHANNEL", config.get("upload_channel")),
        "upload_channel",
        required=True,
    )
    config["log_channel"] = _as_int(os.getenv("DISCORD_LOG_CHANNEL", config.get("log_channel")), "log_channel")
    config["supporter_channel"] = _as_int(
        os.getenv("DISCORD_SUPPORTER_CHANNEL", config.get("supporter_channel")),
        "supporter_channel",
    )
    bot_folder = os.getenv("BOT_FOLDER", config.get("bot_folder") or str(Path.cwd()))
    config["bot_folder"] = str(Path(bot_folder).resolve()) + os.sep

    rclone_drives = os.getenv("RCLONE_DRIVES")
    if rclone_drives:
        config["rclone_drives"] = [drive.strip() for drive in rclone_drives.split(",") if drive.strip()]
    elif not config.get("rclone_drives"):
        config["rclone_drives"] = ["gd"]
    config["rclone_upload_path"] = os.getenv("RCLONE_UPLOAD_PATH", config.get("rclone_upload_path", "")).strip("/")
    config["shrinkearn_api_key"] = os.getenv("SHRINKEARN_API_KEY", config.get("shrinkearn_api_key", "")).strip()
    config["shrinkearn_api_url"] = os.getenv("SHRINKEARN_API_URL", config.get("shrinkearn_api_url", "https://shrinkearn.com/api")).strip()
    config["minecraft_host"] = os.getenv("MINECRAFT_HOST", config.get("minecraft_host", "127.0.0.1")).strip()
    config["minecraft_port"] = _as_positive_int(
        os.getenv("MINECRAFT_PORT", config.get("minecraft_port", 25565)),
        "minecraft_port",
        25565,
    )
    config["minecraft_name"] = os.getenv("MINECRAFT_NAME", config.get("minecraft_name", "Minecraft Server")).strip()
    config["minecraft_status_interval"] = _as_positive_int(
        os.getenv("MINECRAFT_STATUS_INTERVAL", config.get("minecraft_status_interval", 60)),
        "minecraft_status_interval",
        60,
    )

    if not config["token"]:
        raise ValueError("Discord bot token is missing. Set DISCORD_BOT_TOKEN or config.json token.")

    return config


def channel_mention(channel_id):
    return f"<#{channel_id}>" if channel_id else "the configured channel"
