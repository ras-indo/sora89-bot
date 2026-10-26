import unittest
import os
import sys

# Tambahkan direktori proyek ke path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import BotConfig, load_config, ConfigurationError
from core.session_manager import SessionManager, SessionState
from core.api_client import ApiClient
from core.auth import Authenticator


class TestConfig(unittest.TestCase):
    def test_config_defaults_simulation(self):
        cfg = BotConfig.from_env()
        self.assertTrue(cfg.simulation_mode)
        self.assertEqual(cfg.max_demo_interactions, 5)
        self.assertEqual(cfg.max_session_duration_seconds, 600)
        self.assertEqual(cfg.max_retries, 2)

    def test_invalid_url_raises(self):
        os.environ["SORA89_TARGET_URL"] = "ftp://example.com"
        with self.assertRaises(ConfigurationError):
            BotConfig.from_env()
        os.environ.pop("SORA89_TARGET_URL", None)


class TestSessionManager(unittest.TestCase):
    def test_allowed_transitions(self):
        sm = SessionManager(max_demo_interactions=5)
        self.assertEqual(sm.state, SessionState.DISCONNECTED)
        self.assertTrue(sm.transition(SessionState.CONNECTED))
        self.assertEqual(sm.state, SessionState.CONNECTED)
        self.assertTrue(sm.transition(SessionState.DEMO_ACTIVE))
        self.assertEqual(sm.state, SessionState.DEMO_ACTIVE)
        self.assertTrue(sm.transition(SessionState.DISCONNECTED))
        self.assertEqual(sm.state, SessionState.DISCONNECTED)

    def test_disallowed_transition(self):
        sm = SessionManager(max_demo_interactions=5)
        self.assertFalse(sm.transition(SessionState.DEMO_ACTIVE))  # tidak bisa langsung ke DEMO_ACTIVE


class TestAuthSimulator(unittest.TestCase):
    def test_auth_simulation_success(self):
        cfg = BotConfig.from_env()
        self.assertTrue(cfg.simulation_mode)
        client = ApiClient(cfg)
        auth = Authenticator(cfg, client)
        res = auth.authenticate()
        self.assertTrue(res.success)
        self.assertTrue(res.authenticated)
        self.assertEqual(res.source, "local_simulator")


if __name__ == "__main__":
    unittest.main()