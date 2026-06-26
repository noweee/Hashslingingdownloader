import os
import re
import shutil
from pathlib import Path


def streamrip_config_path():
    if os.name == "nt":
        return Path(os.getenv("APPDATA", "")) / "streamrip" / "config.toml"
    xdg_config = os.getenv("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "streamrip" / "config.toml"
    return Path.home() / ".config" / "streamrip" / "config.toml"


def set_qobuz_quality(quality):
    quality_value = int(quality)
    if quality_value not in {1, 2, 3, 4}:
        raise ValueError("Qobuz quality must be 1, 2, 3, or 4.")

    path = streamrip_config_path()
    text = path.read_text()
    updated = re.sub(
        r"(\[qobuz\][\s\S]*?quality\s*=\s*)\d+",
        rf"\g<1>{quality_value}",
        text,
        count=1,
    )
    path.write_text(updated)


def make_request_streamrip_env(temp_path, quality=None):
    temp_path = Path(temp_path)
    appdata = temp_path.parent / ".streamrip_appdata" / temp_path.name
    config_dir = appdata / "streamrip"
    config_dir.mkdir(parents=True, exist_ok=True)
    request_config = config_dir / "config.toml"

    source = streamrip_config_path()
    if source.is_file():
        shutil.copyfile(source, request_config)
    else:
        request_config.write_text("[downloads]\nfolder = \"\"\n[qobuz]\nquality = 1\n")

    text = request_config.read_text()
    folder = str(Path(temp_path).resolve()).replace("\\", "/") + "/"
    text = re.sub(r'(\[downloads\][\s\S]*?folder\s*=\s*)".*?"', rf'\g<1>"{folder}"', text, count=1)
    if quality is not None:
        quality_value = int(quality)
        text = re.sub(r"(\[qobuz\][\s\S]*?quality\s*=\s*)\d+", rf"\g<1>{quality_value}", text, count=1)
    request_config.write_text(text)

    env = os.environ.copy()
    env["APPDATA"] = str(appdata)
    env["XDG_CONFIG_HOME"] = str(appdata)
    return env
