"""CLI untuk bot SORA89 Game Demo."""

from __future__ import annotations

import argparse
import json
import time

from config.config import load_config, ConfigurationError
from core.api_client import ApiClient
from core.auth import Authenticator
from core.session_manager import SessionManager
from core.demo_runner import DemoRunner
from core.state_monitor import StateMonitor
from core.logger import info, error


def cmd_check_env(args) -> int:
    import os
    info("Memeriksa lingkungan proyek dan kemampuan CLI")
    try:
        cfg = load_config()
        info(f"Target: {cfg.target_url}")
        info(f"Mode simulasi: {cfg.simulation_mode}")
        info(f"Kredensial: {cfg.credentials_masked}")
        info(f"Timeout: {cfg.timeout_seconds}s, max demo: {cfg.max_demo_interactions}, durasi: {cfg.max_session_duration_seconds}s")
        print(json.dumps({"ok": True, "simulation_mode": cfg.simulation_mode}, indent=2))
        return 0
    except ConfigurationError as exc:
        error(f"Konfigurasi tidak valid: {exc}")
        return 1


def cmd_run_demo(args) -> int:
    try:
        cfg = load_config()
    except ConfigurationError as exc:
        error(f"Konfigurasi tidak valid: {exc}")
        return 1

    client = ApiClient(cfg)
    auth = Authenticator(cfg, client)
    session = SessionManager(max_demo_interactions=cfg.max_demo_interactions)
    monitor = StateMonitor(cfg, client)
    runner = DemoRunner(cfg, client, session)

    # Autentikasi
    ar = auth.authenticate()
    if not ar.success:
        error(f"Autentikasi gagal: {ar.error}")
        return 2
    session.mark_authenticated(ar.authenticated)
    session.transition(session.state.__class__.CONNECTED)

    # Jalankan demo
    results = runner.run()

    # Status
    report = monitor.check(session)
    print(json.dumps({"auth_source": ar.source, "demo": runner.summary(), "status": report.__dict__}, indent=2))

    # Pembersihan
    auth.logout()
    session.transition(session.state.__class__.DISCONNECTED)
    return 0 if all(r.success for r in results) else 1


def cmd_stop(args) -> int:
    info("Penghentian & pembersihan sumber daya (tidak ada proses latar yang berjalan)")
    print(json.dumps({"ok": True, "message": "Tidak ada proses bot latar yang aktif"}, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="sora89-demo-bot", description="Bot CLI demo game (tanpa browser)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check-env", help="Periksa lingkungan")
    sub.add_parser("run-demo", help="Jalankan sesi demo (simulasi lokal)")
    sub.add_parser("stop", help="Hentikan & bersihkan")
    args = parser.parse_args()

    if args.cmd == "check-env":
        return cmd_check_env(args)
    if args.cmd == "run-demo":
        return cmd_run_demo(args)
    if args.cmd == "stop":
        return cmd_stop(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())