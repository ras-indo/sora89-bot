"""Autentikasi melalui mekanisme resmi (atau simulasi lokal saat target tidak tersedia).

Kredensial dibaca dari environment, TIDAK ditanamkan di source code.
Tidak ada upaya melewati autentikasi, CAPTCHA, MFA, atau kontrol anti-otomasi.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

from config.config import BotConfig
from core.api_client import ApiClient
from core.logger import debug, error, info


@dataclass
class AuthResult:
    success: bool
    authenticated: bool
    token: Optional[str]
    session_cookie: Optional[str]
    error: Optional[str]
    elapsed_seconds: float
    source: str


class Authenticator:
    def __init__(self, config: BotConfig, client: ApiClient) -> None:
        self.config = config
        self.client = client
        self.token: Optional[str] = None
        self.session_cookie: Optional[str] = None
        self.authenticated = False
        self.auth_error: Optional[str] = None

    def authenticate(self) -> AuthResult:
        start = time.monotonic()

        if self.config.simulation_mode:
            return self._simulate_auth(start)

        if not self.config.credentials_present:
            elapsed = time.monotonic() - start
            msg = "Kredensial tidak tersedia (SORA89_USERNAME / SORA89_PASSWORD)"
            error(msg)
            return AuthResult(False, False, None, None, msg, round(elapsed, 4), "official_api")

        payload = {
            "username": self.config.username,
            "password": self.config.password,
        }
        resp = self.client.post("/api/auth/login", json_body=payload)
        elapsed = time.monotonic() - start

        if resp.ok and isinstance(resp.body, dict):
            self.token = resp.body.get("token") or resp.body.get("access_token")
            self.session_cookie = resp.body.get("session_cookie") or resp.headers.get("Set-Cookie")
            self.authenticated = bool(self.token)
            info("Autentikasi resmi berhasil")
            return AuthResult(True, True, self.token, self.session_cookie, None, round(elapsed, 4), "official_api")

        self.auth_error = resp.error or f"HTTP {resp.status_code}"
        error(f"Autentikasi resmi gagal: {self.auth_error}")
        return AuthResult(False, False, None, None, self.auth_error, round(elapsed, 4), "official_api")

    def _simulate_auth(self, start: float) -> AuthResult:
        time.sleep(0.05)
        elapsed = time.monotonic() - start
        self.token = "sim_token_local_demo"
        self.session_cookie = "sim_session=local_demo; Path=/; HttpOnly"
        self.authenticated = True
        info("Autentikasi simulasi berhasil (mode lokal, bukan target nyata)")
        return AuthResult(
            success=True,
            authenticated=True,
            token=self.token,
            session_cookie=self.session_cookie,
            error=None,
            elapsed_seconds=round(elapsed, 4),
            source="local_simulator",
        )

    def logout(self) -> None:
        if self.config.simulation_mode:
            info("Logout simulasi (mode lokal)")
        else:
            try:
                self.client.post("/api/auth/logout")
            except Exception as exc:
                debug(f"Logout best-effort error: {exc}")
        self.token = None
        self.session_cookie = None
        self.authenticated = False