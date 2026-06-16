from pathlib import Path


AUDIO_EXTENSIONS = {".flac", ".m4a", ".mp3", ".ogg", ".opus", ".wav", ".aac", ".alac"}


def audio_files(temp_path):
    return [
        path
        for path in Path(temp_path).rglob("*")
        if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS
    ]


def count_audio_files(temp_path):
    return len(audio_files(temp_path))


def detect_audio_quality(temp_path):
    try:
        from mutagen import File
    except Exception:
        return "Could not inspect file quality."

    for path in audio_files(temp_path):
        audio = File(path)
        info = getattr(audio, "info", None)
        if info is None:
            return path.suffix.lower().lstrip(".").upper()
        sample_rate = getattr(info, "sample_rate", None)
        bits = getattr(info, "bits_per_sample", None)
        bitrate = getattr(info, "bitrate", None)
        parts = [path.suffix.lower().lstrip(".").upper()]
        if bits:
            parts.append(f"{bits}-bit")
        if sample_rate:
            parts.append(f"{round(sample_rate / 1000, 1)} kHz")
        if bitrate and not bits:
            parts.append(f"{round(bitrate / 1000)} kbps")
        return " / ".join(parts)
    return "No audio file detected."
