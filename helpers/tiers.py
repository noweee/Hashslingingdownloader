from dataclasses import dataclass


TIER_ORDER = ["free", "booster", "subscriber", "supporter", "lifetime"]


@dataclass(frozen=True)
class Tier:
    key: str
    label: str
    roles: tuple
    quality_label: str
    qobuz_quality: int
    daily_cap: int | None
    max_batch_tracks: int | None
    allow_albums: bool
    allow_playlists: bool
    allow_artist_archives: bool
    ad_supported: bool
    priority: int


TIERS = {
    "free": Tier(
        key="free",
        label="Free Tier",
        roles=(),
        quality_label="Lossy",
        qobuz_quality=1,
        daily_cap=5,
        max_batch_tracks=1,
        allow_albums=False,
        allow_playlists=False,
        allow_artist_archives=False,
        ad_supported=True,
        priority=0,
    ),
    "booster": Tier(
        key="booster",
        label="Boosters Tier",
        roles=("Booster", "Server Booster", "Nitro Booster"),
        quality_label="Lossy",
        qobuz_quality=1,
        daily_cap=50,
        max_batch_tracks=5,
        allow_albums=True,
        allow_playlists=True,
        allow_artist_archives=False,
        ad_supported=False,
        priority=1,
    ),
    "subscriber": Tier(
        key="subscriber",
        label="Subscribers Tier",
        roles=("Subscriber",),
        quality_label="Lossless 16-bit FLAC",
        qobuz_quality=2,
        daily_cap=250,
        max_batch_tracks=None,
        allow_albums=True,
        allow_playlists=True,
        allow_artist_archives=False,
        ad_supported=False,
        priority=2,
    ),
    "supporter": Tier(
        key="supporter",
        label="Supporters Tier",
        roles=("Supporter",),
        quality_label="Hi-Res Lossless 24-bit/96kHz when available",
        qobuz_quality=3,
        daily_cap=None,
        max_batch_tracks=None,
        allow_albums=True,
        allow_playlists=True,
        allow_artist_archives=False,
        ad_supported=False,
        priority=3,
    ),
    "lifetime": Tier(
        key="lifetime",
        label="Lifetime Pass",
        roles=("Lifetime Pass",),
        quality_label="Highest available / Atmos when supported",
        qobuz_quality=4,
        daily_cap=None,
        max_batch_tracks=None,
        allow_albums=True,
        allow_playlists=True,
        allow_artist_archives=True,
        ad_supported=False,
        priority=4,
    ),
}


QUALITY_CHOICES = {
    "lossy": ("Lossy", 1),
    "16": ("Lossless 16-bit FLAC", 2),
    "16bit": ("Lossless 16-bit FLAC", 2),
    "cd": ("Lossless 16-bit FLAC", 2),
    "24": ("Hi-Res Lossless", 3),
    "24bit": ("Hi-Res Lossless", 3),
    "hires": ("Hi-Res Lossless", 3),
    "atmos": ("Dolby Atmos when available", 4),
    "dolby": ("Dolby Atmos when available", 4),
    "highest": ("Highest available", 4),
    "max": ("Highest available", 4),
}


def member_tier(member):
    role_names = {role.name for role in getattr(member, "roles", [])}
    if "Lifetime Pass" in role_names:
        return TIERS["lifetime"]
    if "Supporter" in role_names:
        return TIERS["supporter"]
    if "Subscriber" in role_names:
        return TIERS["subscriber"]
    if role_names.intersection(TIERS["booster"].roles) or getattr(member, "premium_since", None):
        return TIERS["booster"]
    return TIERS["free"]


def requested_quality(quality_name, tier):
    if not quality_name:
        return tier.quality_label, tier.qobuz_quality
    choice = QUALITY_CHOICES.get(quality_name.lower())
    if not choice:
        raise ValueError("Unknown quality. Use lossy, 16, 24, or atmos.")
    label, qobuz_quality = choice
    if tier.key != "lifetime" and qobuz_quality > tier.qobuz_quality:
        return None
    return label, qobuz_quality


def describe_tier(tier):
    cap = "Unlimited" if tier.daily_cap is None else str(tier.daily_cap)
    batch = "unlimited" if tier.max_batch_tracks is None else str(tier.max_batch_tracks)
    delivery = "standard link" if tier.ad_supported else "direct link"
    return f"{tier.label}: {tier.quality_label}, daily cap {cap}, batch limit {batch}, delivery {delivery}"
