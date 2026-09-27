import json
import tempfile
import unittest
from argparse import Namespace
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch
import ambient
import managed_tick as managed


class ManagedTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.original = ambient.DB
        ambient.DB = self.root / 'queue.sqlite'
        self.args = Namespace(profile='test', runtime=Path('/runtime'), model=Path('/model'), queue_module=None)

    def tearDown(self):
        ambient.DB = self.original
        self.temp.cleanup()

    def test_pending_item_excludes_saved_drafts_and_caps_attempts(self):
        now = datetime(2026,9,26,9,tzinfo=managed.TZ)
        with patch.object(managed, 'RUNS', self.root):
            self.assertEqual(managed.pending_item(now)['id'], 'AMB-001')
            packet=ambient.prepare_packet('AMB-001',0,'2026-09-26')
            ambient.save_draft(packet['packet_id'],0,'Counsel should confirm the workshop owner and review the facilitation plan before delivery.')
            self.assertEqual(managed.pending_item(now)['id'],'AMB-002')
            for n in range(3):(self.root/f'AMB-002-r0-{n}.json').write_text('{}')
            self.assertEqual(managed.pending_item(now)['id'],'AMB-003')

    def test_draft_word_limit_preserves_unsaved_packet(self):
        packet=ambient.prepare_packet('AMB-001',0,'2026-09-26')
        with self.assertRaisesRegex(ValueError,'180 words'):
            ambient.save_draft(packet['packet_id'],0,'word '*181)
        self.assertIsNone(ambient.list_packets()['packets'][0]['model_draft'])

    def test_existing_proxy_is_not_killed_or_replaced(self):
        with patch.object(managed,'RUNS',self.root), patch.object(managed,'port_open',return_value=True), patch.object(managed.subprocess,'Popen') as start:
            self.assertEqual(managed.run(self.args)['status'],'waiting_for_existing_service')
            start.assert_not_called()

    def test_worker_failure_cleans_owned_processes(self):
        processes=[Mock(),Mock()]
        for process in processes:process.poll.return_value=None
        with patch.object(managed,'RUNS',self.root), patch.object(managed,'port_open',return_value=False), patch.object(managed,'model_ready',return_value=True), patch.object(managed.subprocess,'Popen',side_effect=processes), patch.object(managed,'run_review',side_effect=ValueError('failure')):
            with self.assertRaisesRegex(ValueError,'failure'):managed.run(self.args)
            for process in processes:process.terminate.assert_called_once()
