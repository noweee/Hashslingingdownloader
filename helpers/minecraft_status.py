import asyncio
import json
import platform
import struct
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MinecraftStatus:
    online: bool
    latency_ms: int | None = None
    version: str | None = None
    players_online: int | None = None
    players_max: int | None = None
    error: str | None = None


def _pack_varint(value):
    data = bytearray()
    while True:
        temp = value & 0x7F
        value >>= 7
        if value:
            temp |= 0x80
        data.append(temp)
        if not value:
            return bytes(data)


async def _read_varint(reader):
    value = 0
    for index in range(5):
        byte = await reader.readexactly(1)
        value |= (byte[0] & 0x7F) << (7 * index)
        if not byte[0] & 0x80:
            return value
    raise ValueError("VarInt is too large")


def _pack_string(value):
    encoded = value.encode("utf-8")
    return _pack_varint(len(encoded)) + encoded


def _pack_packet(packet_id, payload=b""):
    packet = _pack_varint(packet_id) + payload
    return _pack_varint(len(packet)) + packet


async def query_minecraft_status(host, port, timeout=3):
    start = time.perf_counter()
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
    except OSError as exc:
        return MinecraftStatus(online=False, error=str(exc))
    except asyncio.TimeoutError:
        return MinecraftStatus(online=False, error="Connection timed out")

    try:
        handshake = (
            _pack_varint(765)
            + _pack_string(host)
            + struct.pack(">H", port)
            + _pack_varint(1)
        )
        writer.write(_pack_packet(0, handshake))
        writer.write(_pack_packet(0))
        await writer.drain()

        await asyncio.wait_for(_read_varint(reader), timeout=timeout)
        packet_id = await asyncio.wait_for(_read_varint(reader), timeout=timeout)
        if packet_id != 0:
            raise ValueError("Unexpected Minecraft status response")
        response_length = await asyncio.wait_for(_read_varint(reader), timeout=timeout)
        response = await asyncio.wait_for(reader.readexactly(response_length), timeout=timeout)
        data = json.loads(response.decode("utf-8"))
        latency_ms = round((time.perf_counter() - start) * 1000)
        players = data.get("players", {})
        version = data.get("version", {})
        return MinecraftStatus(
            online=True,
            latency_ms=latency_ms,
            version=version.get("name"),
            players_online=players.get("online"),
            players_max=players.get("max"),
        )
    except (OSError, asyncio.TimeoutError, ValueError, json.JSONDecodeError) as exc:
        return MinecraftStatus(online=False, error=str(exc))
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except OSError:
            pass


def format_duration(seconds):
    seconds = max(0, int(seconds))
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)


def system_uptime_seconds():
    if platform.system() == "Linux":
        uptime_path = Path("/proc/uptime")
        if uptime_path.is_file():
            return float(uptime_path.read_text(encoding="ascii").split()[0])
    if platform.system() == "Windows":
        return time.monotonic()
    return None


def format_system_uptime():
    uptime = system_uptime_seconds()
    if uptime is None:
        return "Unknown"
    return format_duration(uptime)
