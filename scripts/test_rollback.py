"""Exercise downgrade on synthetic data only."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class RollbackTest(unittest.TestCase):
    def test_dry_run_write_backup_and_idempotence(self):
        script = Path(__file__).with_name("rollback_profiles.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profiles = root / "agent-profiles"
            profiles.mkdir()
            old = {"agent_kind": "openhands", "name": "corpus", "system_prompt": "Corpus only.",
                   "id": "identity", "revision": 7, "mcp_server_refs": ["corpus"], "unknown_future": {"x": 1}}
            path = profiles / "corpus.json"
            original = json.dumps(old).encode()
            path.write_bytes(original)
            acp = profiles / "acp.json"
            acp.write_text('{"agent_kind":"acp","name":"external"}')
            subprocess.run([sys.executable, str(script), str(profiles)], check=True)
            self.assertEqual(path.read_bytes(), original)
            subprocess.run([sys.executable, str(script), str(profiles), "--write"], check=True)
            restored = json.loads(path.read_text())
            del old["system_prompt"]
            self.assertEqual(restored, old)
            backup = list(root.glob("system-prompt-rollback-*"))
            self.assertEqual(len(backup), 1)
            self.assertEqual((backup[0] / path.name).read_bytes(), original)
            self.assertEqual(backup[0].stat().st_mode & 0o777, 0o700)
            subprocess.run([sys.executable, str(script), str(profiles), "--write"], check=True)
            self.assertEqual(len(list(root.glob("system-prompt-rollback-*"))), 1)
            self.assertEqual(acp.read_text(), '{"agent_kind":"acp","name":"external"}')


if __name__ == "__main__":
    unittest.main()
