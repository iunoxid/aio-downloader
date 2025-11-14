import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None  # type: ignore


@dataclass
class Settings:
    telegram_bot_token: str
    downloader_api_base_url: str
    downloader_api_key: str | None
    max_upload_bytes: int
    max_concurrent_per_user: int
    http_connect_timeout: int
    http_read_timeout: int
    http_total_timeout: int
    endpoints_per_platform: Dict[str, str] = field(default_factory=dict)


def getenv_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _load_yaml_config() -> tuple[str, Dict[str, str]]:
    """Load endpoints from config.yml if present.
    Returns (default_base_url, per_platform_map).
    """
    default_url = os.getenv("DOWNLOADER_API_BASE_URL", "")
    per_platform: Dict[str, str] = {}
    cfg_path = Path("config.yml")
    if cfg_path.exists() and yaml is not None:
        try:
            with cfg_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            endpoints = (data.get("endpoints") or {}) if isinstance(data, dict) else {}
            # Support either 'default' or 'default_base_url'
            default_url = endpoints.get("default") or endpoints.get("default_base_url") or default_url
            per = endpoints.get("per_platform") or {}
            if isinstance(per, dict):
                # normalize keys to lower
                for k, v in per.items():
                    if isinstance(k, str) and isinstance(v, str) and v:
                        per_platform[k.lower()] = v
        except Exception:
            # Ignore YAML errors and fallback to env-only
            pass
    return default_url, per_platform


def load_settings() -> Settings:
    default_url, per_platform = _load_yaml_config()
    return Settings(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        downloader_api_base_url=default_url,
        downloader_api_key=os.getenv("DOWNLOADER_API_KEY"),
        max_upload_bytes=getenv_int("MAX_UPLOAD_TO_TELEGRAM_BYTES", 50 * 1024 * 1024),
        max_concurrent_per_user=getenv_int("MAX_CONCURRENT_PER_USER", 3),
        http_connect_timeout=getenv_int("HTTP_CONNECT_TIMEOUT", 10),
        http_read_timeout=getenv_int("HTTP_READ_TIMEOUT", 60),
        http_total_timeout=getenv_int("HTTP_TOTAL_TIMEOUT", 120),
        endpoints_per_platform=per_platform,
    )
