"""State monitor: memeriksa status dan hasil operasi berdasarkan bukti aktual.

Tidak menyatakan sukses tanpa bukti.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from config.config import BotConfig
from core.api_client import ApiClient
from core.logger import info


@dataclass
class StatusReport:
    state: str
    authenticated: bool
    demo_interactions: int
    max_demo_interactions: int
    elapsed_seconds: float
    api_reachable: bool
    last_status_code: int
    errors: List[str] = field(default_factory=list)


class StateMonitor:
    def __init__(self, config: BotConfig, client: ApiClient) -> None:
        self.config = config
        self.client = client

    def check(self, session) -> StatusReport:
        # Probe status endpoint jika tersedia (non-destruktif, read-only).
        resp = self.client.get("/api/status", retries=0)
        api_reachable = resp.status_code != 0
        errors: List[str] = []
        if not api_reachable:
            errors.append("API tidak dapat dijangkau (status_code=0)")
        if resp.error:
            errors.append(resp.error)

        snap = session.snapshot()
        report = StatusReport(
            state=snap.state.value,
            authenticated=snap.authenticated,
            demo_interactions=snap.demo_interactions,
            max_demo_interactions=snap.max_demo_interactions,
            elapsed_seconds=snap.elapsed_seconds,
            api_reachable=api_reachable,
            last_status_code=resp.status_code,
            errors=errors,
        )
        info(f"Status: {report.state}, demo={report.demo_interactions}/{report.max_demo_interactions}, api_reachable={api_reachable}")
        return report

    def as_dict(self, report: StatusReport) -> Dict[str, Any]:
        return report.__dict__