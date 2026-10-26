"""Klien HTTP non-browser untuk komunikasi dengan API resmi atau simulator lokal.

Tidak ada browser, tidak ada headless browser, tidak ada Playwright/Puppeteer/Selenium.
Menggunakan curl_cffi untuk TLS fingerprinting + cookie priming untuk melewati proteksi berbasis browser fingerprint.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from config.config import BotConfig
from core.logger import debug, error, info, warning


@dataclass
class ApiResponse:
    status_code: int
    ok: bool
    headers: Dict[str, str]
    body: Any
    raw_text: str
    elapsed_seconds: float
    error: Optional[str] = None


class ApiClient:
    def __init__(self, config: BotConfig) -> None:
        self.config = config
        self._last_response: Optional[ApiResponse] = None
        self._real_ip = None
        self._session = None
        # Resolve real IP via DoH to bypass DNS hijack
        self._resolve_real_ip()

    def _resolve_real_ip(self):
        try:
            import urllib.request, ssl
            ctx = ssl.create_default_context()
            req = urllib.request.Request(
                'https://dns.google/resolve?name=sora89juli.com&type=A',
                headers={'accept': 'application/dns-json', 'user-agent': 'curl/8'}
            )
            r = urllib.request.urlopen(req, context=ctx, timeout=10).read()
            data = json.loads(r)
            if data.get('Answer'):
                self._real_ip = data['Answer'][0]['data']
                debug(f"Resolved real IP via DoH: {self._real_ip}")
        except Exception as e:
            debug(f"DoH resolution failed: {e}")

    def _get_session(self):
        if self._session is None:
            try:
                from curl_cffi import requests as cffi_requests
                self._session = cffi_requests.Session(impersonate="chrome110")
                self._session.headers.update({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                })
            except Exception as e:
                error(f"curl_cffi import failed: {e}")
                raise
        return self._session

    def _make_url(self, path: str):
        if self._real_ip and self.config.target_url.startswith("https://"):
            # Use real IP but keep Host header
            return self.config.target_url.replace("https://sora89juli.com", f"https://{self._real_ip}").rstrip("/") + path
        return self.config.target_url.rstrip("/") + path

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        retries: Optional[int] = None,
    ) -> ApiResponse:
        if self.config.simulation_mode:
            return self._simulate_request(method, path)

        session = self._get_session()
        url = self._make_url(path)
        timeout = timeout or self.config.timeout_seconds
        retries = self.config.max_retries if retries is None else retries
        attempt = 0

        req_headers = headers or {}
        if self._real_ip:
            req_headers["Host"] = "sora89juli.com"

        # Prime cookies if not primed
        if not session.cookies:
            try:
                debug("Priming session for Cloudflare cookies")
                session.get(
                    self._make_url("/"),
                    headers={"Host": "sora89juli.com"} if self._real_ip else {},
                    timeout=timeout,
                    allow_redirects=True
                )
            except Exception as e:
                debug(f"Priming failed: {e}")

        while True:
            attempt += 1
            start = time.monotonic()
            try:
                debug(f"{method} {url} (attempt {attempt})")
                resp = session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_body,
                    headers=req_headers,
                    timeout=timeout,
                    allow_redirects=False,
                )
                elapsed = time.monotonic() - start
                body = self._parse_body(resp)
                api_resp = ApiResponse(
                    status_code=resp.status_code,
                    ok=200 <= resp.status_code < 300,
                    headers=dict(resp.headers),
                    body=body,
                    raw_text=resp.text,
                    elapsed_seconds=round(elapsed, 4),
                )
                self._last_response = api_resp
                info(f"{method} {path} -> {resp.status_code} ({elapsed:.3f}s)")
                return api_resp
            except Exception as exc:
                elapsed = time.monotonic() - start
                error(f"{method} {path} request error: {exc}")
                if attempt <= retries and method.upper() == "GET":
                    warning(f"Retry GET {path} ({attempt}/{retries})")
                    time.sleep(self.config.retry_delay_seconds * attempt)
                    continue
                self._last_response = ApiResponse(
                    status_code=0,
                    ok=False,
                    headers={},
                    body=None,
                    raw_text="",
                    elapsed_seconds=round(elapsed, 4),
                    error=str(exc),
                )
                return self._last_response

    def _simulate_request(self, method: str, path: str) -> ApiResponse:
        time.sleep(0.02)
        if path == "/api/status":
            body = {"status": "ok", "mode": "demo", "online": False}
            return ApiResponse(
                status_code=200,
                ok=True,
                headers={"Content-Type": "application/json"},
                body=body,
                raw_text=json.dumps(body),
                elapsed_seconds=0.02,
            )
        if path == "/api/demo/spin":
            body = {"result": "demo_spin", "reward": "demo", "balance": "0.00", "currency": "DEMO"}
            return ApiResponse(
                status_code=200,
                ok=True,
                headers={"Content-Type": "application/json"},
                body=body,
                raw_text=json.dumps(body),
                elapsed_seconds=0.02,
            )
        body = {"status": "ok", "path": path, "mode": "simulator"}
        return ApiResponse(
            status_code=200,
            ok=True,
            headers={"Content-Type": "application/json"},
            body=body,
            raw_text=json.dumps(body),
            elapsed_seconds=0.02,
        )

    def get(self, path: str, **kwargs) -> ApiResponse:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> ApiResponse:
        return self.request("POST", path, **kwargs)

    def _parse_body(self, resp) -> Any:
        ct = getattr(resp.headers, "get", lambda k, d=None: None)("Content-Type", "") or ""
        try:
            if "application/json" in ct:
                return resp.json()
        except Exception:
            pass
        try:
            return resp.text
        except Exception:
            return ""

    @property
    def last_response(self) -> Optional[ApiResponse]:
        return self._last_response