"""Demo runner: mengeksekusi interaksi demo yang diizinkan dengan batas yang jelas.

Tidak menjalankan taruhan uang asli, deposit, withdraw, pembelian, klaim bonus,
atau operasi finansial lainnya.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List, Optional

from config.config import BotConfig
from core.api_client import ApiClient
from core.logger import info
from core.session_manager import SessionManager


@dataclass
class DemoInteractionResult:
    index: int
    operation: str
    success: bool
    status_code: int
    elapsed_seconds: float
    error: Optional[str] = None


class DemoRunner:
    def __init__(self, config: BotConfig, client: ApiClient, session: SessionManager) -> None:
        self.config = config
        self.client = client
        self.session = session
        self.results: List[DemoInteractionResult] = []

    def run(self, max_interactions: Optional[int] = None) -> List[DemoInteractionResult]:
        max_n = max_interactions if max_interactions is not None else self.config.max_demo_interactions
        max_n = min(max_n, self.config.max_demo_interactions)

        # Transisi ke DEMO_ACTIVE jika saat ini CONNECTED
        if self.session.state.value == "CONNECTED":
            self.session.transition(self.session.state.__class__.DEMO_ACTIVE)

        for i in range(1, max_n + 1):
            if self.session.demo_limit_reached():
                info("Batas interaksi demo tercapai, berhenti")
                break
            if self.session.elapsed() > self.config.max_session_duration_seconds:
                info("Batas durasi sesi tercapai, berhenti")
                break

            result = self._single_interaction(i)
            self.results.append(result)
            self.session.increment_demo()

            if not result.success:
                info(f"Interaksi {i} gagal: {result.error}; hentikan sesi demo")
                break

        return self.results

    def _single_interaction(self, index: int) -> DemoInteractionResult:
        start = time.monotonic()
        # Operasi demo yang diizinkan: "spin_demo" (tanpa uang asli).
        resp = self.client.get("/api/demo/spin")
        elapsed = time.monotonic() - start
        return DemoInteractionResult(
            index=index,
            operation="spin_demo",
            success=resp.ok,
            status_code=resp.status_code,
            elapsed_seconds=round(elapsed, 4),
            error=resp.error,
        )

    def summary(self) -> dict:
        total = len(self.results)
        ok = sum(1 for r in self.results if r.success)
        return {
            "total": total,
            "success": ok,
            "failed": total - ok,
            "interactions": [r.__dict__ for r in self.results],
        }