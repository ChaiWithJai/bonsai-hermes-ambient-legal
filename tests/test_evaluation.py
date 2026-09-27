import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ambient
import evaluate


class EvaluationTests(unittest.TestCase):
    def test_imported_request_is_checked_and_corruption_is_detected(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(ambient, "DB", Path(directory) / "queue.sqlite"):
            item = json.loads((ambient.ROOT / "fixtures/incoming-example.json").read_text())
            ambient.submit_request(item)
            ambient.prepare_packet(item["id"], 0, "2026-09-26")
            self.assertTrue(evaluate.evaluate()["source_fields_match_registered_request"])
            with ambient.connect() as conn:
                body = json.loads(conn.execute("SELECT body FROM packets").fetchone()[0])
                body["source_clause"] = "Changed clause"
                conn.execute("UPDATE packets SET body=?", (json.dumps(body),))
            self.assertFalse(evaluate.evaluate()["source_fields_match_registered_request"])

    def test_no_packets_is_not_a_passing_source_check(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(ambient, "DB", Path(directory) / "queue.sqlite"):
            self.assertIsNone(evaluate.evaluate()["source_fields_match_registered_request"])


if __name__ == "__main__":
    unittest.main()
