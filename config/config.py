"""Konfigurasi dan validasi bot SORA89 Game Demo.

Semua nilai dibaca dari environment variable atau nilai default aman.
Kredensial asli TIDAK ditanamkan di source code.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


class ConfigurationError(Exception):
    """Dilempar saat konfigurasi tidak valid dan eksekusi harus dihentikan."""


@dataclass(frozen=True)
class BotConfig:
    target_url: str
    username: Optional[str]
    password: Optional[str]
    timeout_seconds: int
    max_demo_interactions: int
    max_session_duration_seconds: int
    max_retries: int
    retry_delay_seconds: float
    simulation_mode: bool
    log_level: str

    @classmethod
    def from_env(cls) -> "BotConfig":
        """Baca konfigurasi dari environment dengan validasi."""
        target_url = os.getenv("SORA89_TARGET_URL", "https://sora89juli.com/")
        username = os.getenv("SORA89_USERNAME")
        password = os.getenv("SORA89_PASSWORD")

        try:
            timeout_seconds = int(os.getenv("SORA89_TIMEOUT", "30"))
            max_demo_interactions = int(os.getenv("SORA89_MAX_DEMO_INTERACTIONS", "5"))
            max_session_duration = int(os.getenv("SORA89_MAX_SESSION_DURATION", "600"))
            max_retries = int(os.getenv("SORA89_MAX_RETRIES", "2"))
            retry_delay = float(os.getenv("SORA89_RETRY_DELAY", "1.0"))
        except ValueError as exc:
            raise ConfigurationError(f"Nilai konfigurasi numerik tidak valid: {exc}") from exc

        log_level = os.getenv("SORA89_LOG_LEVEL", "INFO").upper()
        simulation_mode = os.getenv("SORA89_SIMULATION_MODE", "true").lower() == "true"

        # Validasi
        if not target_url.startswith(("http://", "https://")):
            raise ConfigurationError(f"Target URL tidak valid: {target_url}")
        if timeout_seconds <= 0 or timeout_seconds > 300:
            raise ConfigurationError("timeout_seconds harus antara 1 dan 300 detik")
        if not 1 <= max_demo_interactions <= 50:
            raise ConfigurationError("max_demo_interactions harus antara 1 dan 50")
        if max_session_duration <= 0:
            raise ConfigurationError("max_session_duration_seconds harus > 0")
        if max_retries < 0 or max_retries > 10:
            raise ConfigurationError("max_retries harus antara 0 dan 10")
        if retry_delay < 0:
            raise ConfigurationError("retry_delay_seconds tidak boleh negatif")
        if log_level not in ("DEBUG", "INFO", "WARNING", "ERROR"):
            raise ConfigurationError(f"Tingkat logging tidak valid: {log_level}")

        return cls(
            target_url=target_url,
            username=username,
            password=password,
            timeout_seconds=timeout_seconds,
            max_demo_interactions=max_demo_interactions,
            max_session_duration_seconds=max_session_duration,
            max_retries=max_retries,
            retry_delay_seconds=retry_delay,
            simulation_mode=simulation_mode,
            log_level=log_level,
        )

    @property
    def credentials_present(self) -> bool:
        return bool(self.username and self.password)

    @property
    def credentials_masked(self) -> str:
        """Representasi aman untuk log: username terlihat, password disembunyikan."""
        user = self.username or "(tidak diatur)"
        pw = "(terkonfigurasi)" if self.password else "(tidak diatur)"
        return f"username={user}, password={pw}"


def load_config() -> BotConfig:
    try:
        return BotConfig.from_env()
    except ConfigurationError:
        raise