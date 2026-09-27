import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from import_commitment import request_from_commitment


class ConnectedIntakeTests(unittest.TestCase):
    def setUp(self):
        self.row = {
            "id": "APL-008", "revision": 1, "source_kind": "google_drive_api",
            "source_file": "order-form.md", "source_section": "2.1",
            "customer": "Sample client", "obligation": "Confirm site leads.",
            "clause": "Confirm primary and backup site leads.", "status": "open",
            "due_date": "", "owner": "Khizar", "evidence_needed": "Written confirmation",
        }

    def test_preserves_unknown_date_owner_clause_and_revision(self):
        request = request_from_commitment(self.row, "AMB-108")
        self.assertIsNone(request["due"])
        self.assertEqual(request["owner"], "Khizar")
        self.assertEqual(request["clause"], self.row["clause"])
        self.assertIn("APL-008 revision 1", request["source"])
        self.assertEqual(request["dependency"], "Written confirmation")

    def test_rejects_local_fallback_as_connected_intake(self):
        self.row["source_kind"] = "local_copy_of_drive_document"
        with self.assertRaisesRegex(ValueError, "Drive API"):
            request_from_commitment(self.row, "AMB-108")

    def test_rejects_completed_commitment(self):
        self.row["status"] = "complete"
        with self.assertRaisesRegex(ValueError, "already complete"):
            request_from_commitment(self.row, "AMB-108")


if __name__ == "__main__":
    unittest.main()
