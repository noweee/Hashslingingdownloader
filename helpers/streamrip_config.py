import os
import re
from pathlib import Path


def streamrip_config_path():
    return Path(os.getenv("APPDATA", "")) / "streamrip" / "config.toml"


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
