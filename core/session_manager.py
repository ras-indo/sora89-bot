"""Pengelola siklus hidup sesi dengan state machine yang konsisten.

Status yang didukung:
  DISCONNECTED -> CONNECTED -> DEMO_ACTIVE -> DISCONNECTED
Tidak ada pemalsuan status online atau heartbeat palsu.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from core.logger import info


class SessionState(Enum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTED = "CONNECTED"
    DEMO_ACTIVE = "DEMO_ACTIVE"


# Transisi yang diizinkan: state -> set(state yang boleh dituju)
ALLOWED_TRANSITIONS = {
    SessionState.DISCONNECTED: {SessionState.CONNECTED},
    SessionState.CONNECTED: {SessionState.DEMO_ACTIVE, SessionState.DISCONNECTED},
    SessionState.DEMO_ACTIVE: {SessionState.CONNECTED, SessionState.DISCONNECTED},
}


@dataclass
class SessionSnapshot:
    state: SessionState
    started_at: Optional[float]
    authenticated: bool
    demo_interactions: int
    max_demo_interactions: int
    elapsed_seconds: float


class SessionManager:
    def __init__(self, max_demo_interactions: int = 5) -> None:
        self.state = SessionState.DISCONNECTED
        self.started_at: Optional[float] = None
        self.authenticated = False
        self.demo_interactions = 0
        self.max_demo_interactions = max_demo_interactions

    def transition(self, new_state: SessionState) -> bool:
        """Transisi state; return False jika transisi tidak diizinkan."""
        if new_state in ALLOWED_TRANSITIONS.get(self.state, set()):
            info(f"Session state: {self.state.value} -> {new_state.value}")
            self.state = new_state
            if new_state == SessionState.CONNECTED and self.started_at is None:
                self.started_at = time.monotonic()
            return True
        info(f"Transisi state tidak diizinkan: {self.state.value} -> {new_state.value}")
        return False

    def mark_authenticated(self, authenticated: bool) -> None:
        self.authenticated = authenticated

    def increment_demo(self) -> int:
        if self.demo_interactions < self.max_demo_interactions:
            self.demo_interactions += 1
        return self.demo_interactions

    def demo_limit_reached(self) -> bool:
        return self.demo_interactions >= self.max_demo_interactions

    def elapsed(self) -> float:
        if self.started_at is None:
            return 0.0
        return round(time.monotonic() - self.started_at, 4)

    def snapshot(self) -> SessionSnapshot:
        return SessionSnapshot(
            state=self.state,
            started_at=self.started_at,
            authenticated=self.authenticated,
            demo_interactions=self.demo_interactions,
            max_demo_interactions=self.max_demo_interactions,
            elapsed_seconds=self.elapsed(),
        )

    def reset(self) -> None:
        self.state = SessionState.DISCONNECTED
        self.started_at = None
        self.authenticated = False
        self.demo_interactions = 0