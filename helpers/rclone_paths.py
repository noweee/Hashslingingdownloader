def remote_path(remote, upload_path="", filename=""):
    parts = [part.strip("/") for part in (upload_path, filename) if part]
    path = "/".join(parts)
    return f"{remote}:{path}" if path else f"{remote}:"
