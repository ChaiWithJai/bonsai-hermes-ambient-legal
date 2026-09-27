import fcntl
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import run_review


class ReviewInterruptionTest(unittest.TestCase):
    def test_interruption_is_saved_and_item_lock_is_released(self):
        with tempfile.TemporaryDirectory() as tmp:
            runs = Path(tmp)
            with patch.object(run_review, 'cursor', return_value=0), patch.object(run_review, 'run_owned', side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt):
                    run_review.run_review({'id': 'AMB-003', 'revision': 0}, '2026-09-26', 'unused-test-profile', runs)
            records = list(runs.glob('*.json'))
            self.assertEqual(len(records), 1)
            report = json.loads(records[0].read_text())
            self.assertEqual(report['status'], 'interrupted')
            self.assertNotIn('model_draft', report)
            with (runs / '.AMB-003-r0.lock').open('a') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
