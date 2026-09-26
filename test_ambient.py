import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("ambient", ROOT / "ambient.py")
ambient = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ambient)


class AmbientTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        ambient.DB = Path(self.tmp.name) / "ambient.sqlite"

    def tearDown(self):
        self.tmp.cleanup()

    def test_unattended_pass_is_idempotent_and_source_grounded(self):
        first = ambient.tick("2026-09-26")
        self.assertEqual(first["new_packets"], 4)
        self.assertEqual(first["awaiting_counsel"], 4)
        by_id = {p["item_id"]: p for p in first["packets"]}
        self.assertEqual(by_id["AMB-003"]["due"], "2026-10-06")
        self.assertIn("replacing MSA", by_id["AMB-003"]["source"])
        self.assertIsNone(by_id["AMB-004"]["due"])
        self.assertIn("Unknown", by_id["AMB-004"]["due_display"])
        self.assertEqual(ambient.tick("2026-09-26")["new_packets"], 0)
        with ambient.connect() as conn:
            self.assertEqual(conn.execute("SELECT count(*) FROM audit WHERE action='packet_prepared'").fetchone()[0], 4)

    def test_stale_revision_cannot_create_packet(self):
        with self.assertRaisesRegex(ValueError, "changed"):
            ambient.prepare_packet("AMB-001", 7, "2026-09-26")
        self.assertEqual(ambient.list_packets()["count"], 0)

    def test_model_draft_requires_review_and_cannot_silently_replace(self):
        packet = ambient.prepare_packet("AMB-002", 0, "2026-09-26")
        draft = "Coverage should include a named primary and backup for the stated weekday hours. Neither has accepted yet."
        saved = ambient.save_draft(packet["packet_id"], 0, draft)
        self.assertTrue(saved["saved"])
        self.assertFalse(saved["external_message_sent"])
        self.assertFalse(ambient.save_draft(packet["packet_id"], 0, draft)["saved"])
        with self.assertRaisesRegex(ValueError, "already exists"):
            ambient.save_draft(packet["packet_id"], 0, draft + " Change.")
        with self.assertRaisesRegex(ValueError, "reviewer"):
            ambient.review_packet(packet["packet_id"], "", "approve_draft", "Fine")
        review = ambient.review_packet(packet["packet_id"], "Demo counsel", "approve_draft", "Approved as a draft only")
        self.assertFalse(review["external_message_sent"])
        self.assertFalse(review["owner_changed"])
        with self.assertRaisesRegex(ValueError, "already reviewed"):
            ambient.review_packet(packet["packet_id"], "Demo counsel", "approve_draft", "Repeat")
        with self.assertRaisesRegex(ValueError, "already reviewed"):
            ambient.save_draft(packet["packet_id"], 0, draft + " Other")

    def test_mcp_round_trip_and_deterministic_tick_cli(self):
        env = dict(os.environ, AMBIENT_DB=str(Path(self.tmp.name) / "mcp.sqlite"))
        calls = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05"}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "scan_queue", "arguments": {"as_of": "2026-09-26"}}},
        ]
        result = subprocess.run([sys.executable, str(ROOT / "ambient.py"), "mcp"], input="\n".join(json.dumps(c) for c in calls) + "\n", text=True, capture_output=True, env=env, check=True)
        lines = [json.loads(x) for x in result.stdout.splitlines()]
        self.assertEqual(len(lines), 3)
        self.assertEqual(len(lines[1]["result"]["tools"]), 4)
        self.assertNotIn("review_packet", [tool["name"] for tool in lines[1]["result"]["tools"]])
        self.assertEqual(json.loads(lines[2]["result"]["content"][0]["text"])["count"], 4)
        tick = subprocess.run([sys.executable, str(ROOT / "ambient.py"), "tick", "--as-of", "2026-09-26"], text=True, capture_output=True, env=env, check=True)
        self.assertEqual(json.loads(tick.stdout)["new_packets"], 4)

    def test_profile_reads_the_database_used_by_cli_submission(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            database = home / "state" / "requests.sqlite"
            profile = home / ".hermes" / "profiles" / "setup-check"
            env = dict(os.environ, HOME=str(home), AMBIENT_DB=str(database))
            subprocess.run([sys.executable, str(ROOT / "ambient.py"), "submit",
                            "--file", str(ROOT / "incoming-example.json")],
                           env=env, capture_output=True, text=True, check=True)
            subprocess.run([sys.executable, str(ROOT / "setup.py"), "--out", str(profile)],
                           env=env, capture_output=True, text=True, check=True)
            server = json.loads((profile / "config.yaml").read_text())["mcp_servers"]["ambient_legal"]
            self.assertEqual(server["env"]["AMBIENT_DB"], str(database.resolve()))
            child_env = dict(os.environ)
            child_env.pop("AMBIENT_DB", None)
            child_env.update(server["env"])
            request = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": "scan_queue", "arguments": {"as_of": "2026-09-26"}}}
            result = subprocess.run([server["command"], *server["args"]], cwd=home,
                                    env=child_env, input=json.dumps(request)+"\n",
                                    capture_output=True, text=True, check=True)
            response = json.loads(result.stdout)["result"]
            self.assertFalse(response.get("isError"), response)
            self.assertEqual(json.loads(response["content"][0]["text"])["count"], 5)

    def test_new_request_enters_next_pass_without_overwriting_prior_work(self):
        first = ambient.tick("2026-09-26")
        self.assertEqual(first["new_packets"], 4)
        example = json.loads((ROOT / "incoming-example.json").read_text())
        self.assertTrue(ambient.submit_request(example)["accepted"])
        with self.assertRaisesRegex(ValueError, "already exists"):
            ambient.submit_request(example)
        next_pass = ambient.tick("2026-09-26")
        self.assertEqual(next_pass["new_packets"], 1)
        self.assertEqual(next_pass["packets"][0]["item_id"], "AMB-005")
        self.assertEqual(ambient.list_packets()["count"], 5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
