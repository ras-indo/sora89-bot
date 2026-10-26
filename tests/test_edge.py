import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import BotConfig
from core.api_client import ApiClient
from core.session_manager import SessionManager, SessionState
from core.demo_runner import DemoRunner
from core.state_monitor import StateMonitor


class TestDemoRunnerEdgeCases(unittest.TestCase):
    def setUp(self):
        os.environ["SORA89_SIMULATION_MODE"] = "true"
        self.cfg = BotConfig.from_env()
        self.client = ApiClient(self.cfg)
        self.session = SessionManager(max_demo_interactions=3)
        self.session.mark_authenticated(True) if hasattr(self.session, "mark_authenticated") else None
        self.session.transition(SessionState.CONNECTED)
        self.runner = DemoRunner(self.cfg, self.client, self.session)

    def test_demo_limit_respected(self):
        results = self.runner.run(max_interactions=10)
        self.assertEqual(len(results), 3)
        self.assertTrue(all(r.success for r in results))

    def test_state_monitor_reports_api_reachable(self):
        monitor = StateMonitor(self.cfg, self.client)
        report = monitor.check(self.session)
        self.assertTrue(report.api_reachable)
        self.assertEqual(report.last_status_code, 200)


if __name__ == "__main__":
    unittest.main()