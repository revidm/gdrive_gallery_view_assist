from dataclasses import dataclass
import json
import os


OPTIONS_PATH = "/data/options.json"


@dataclass
class Settings:
    client_id: str
    client_secret: str
    refresh_token: str
    drive_folder_id: str
    drive_include_shared: bool
    drive_recursive: bool
    exclude_patterns: str
    cache_images: bool
    cache_max_items: int
    cache_max_mb: int
    prefetch_next: bool
    daily_shuffle: bool
    port: int
    refresh_interval_minutes: int
    max_items: int
    mode: str


def _load_options() -> dict:
    if not os.path.exists(OPTIONS_PATH):
        return {}
    with open(OPTIONS_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _get_value(
    options: dict, key: str, env_name: str, default: str | None = None
) -> str:
    if key in options and options[key] is not None:
        return str(options[key])
    value = os.getenv(env_name)
    if value is None:
        if default is None:
            raise RuntimeError(f"Missing required config value: {key}")
        return default
    return value


def load_settings() -> Settings:
    options = _load_options()
    return Settings(
        client_id=_get_value(options, "client_id", "GPHOTOS_CLIENT_ID"),
        client_secret=_get_value(options, "client_secret", "GPHOTOS_CLIENT_SECRET"),
        refresh_token=_get_value(options, "refresh_token", "GPHOTOS_REFRESH_TOKEN"),
        drive_folder_id=_get_value(options, "drive_folder_id", "DRIVE_FOLDER_ID", ""),
        drive_include_shared=_get_value(
            options, "drive_include_shared", "DRIVE_INCLUDE_SHARED", "false"
        ).lower()
        == "true",
        drive_recursive=_get_value(
            options, "drive_recursive", "DRIVE_RECURSIVE", "false"
        ).lower()
        == "true",
        exclude_patterns=_get_value(
            options, "exclude_patterns", "EXCLUDE_PATTERNS", ""
        ),
        cache_images=_get_value(
            options, "cache_images", "CACHE_IMAGES", "false"
        ).lower()
        == "true",
        cache_max_items=int(
            _get_value(options, "cache_max_items", "CACHE_MAX_ITEMS", "0")
        ),
        cache_max_mb=int(_get_value(options, "cache_max_mb", "CACHE_MAX_MB", "0")),
        prefetch_next=_get_value(
            options, "prefetch_next", "PREFETCH_NEXT", "false"
        ).lower()
        == "true",
        daily_shuffle=_get_value(
            options, "daily_shuffle", "DAILY_SHUFFLE", "false"
        ).lower()
        == "true",
        port=int(_get_value(options, "port", "PORT", "8099")),
        refresh_interval_minutes=int(
            _get_value(
                options, "refresh_interval_minutes", "REFRESH_INTERVAL_MINUTES", "30"
            )
        ),
        max_items=int(_get_value(options, "max_items", "MAX_ITEMS", "500")),
        mode=_get_value(options, "mode", "MODE", "random"),
    )
