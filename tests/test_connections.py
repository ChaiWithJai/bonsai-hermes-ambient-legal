import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ambient


class ConnectionTests(unittest.TestCase):
    def test_success_closes_connection(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(ambient, 'DB', Path(directory) / 'queue.sqlite'):
            with ambient.connect() as conn:
                self.assertEqual(conn.execute('SELECT count(*) FROM items').fetchone()[0], 4)
            with self.assertRaises(sqlite3.ProgrammingError):
                conn.execute('SELECT 1')

    def test_exception_rolls_back_and_closes_connection(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(ambient, 'DB', Path(directory) / 'queue.sqlite'):
            with self.assertRaisesRegex(RuntimeError, 'interrupted'):
                with ambient.connect() as conn:
                    conn.execute('BEGIN IMMEDIATE')
                    conn.execute('DELETE FROM items')
                    raise RuntimeError('interrupted')
            with self.assertRaises(sqlite3.ProgrammingError):
                conn.execute('SELECT 1')
            with ambient.connect() as recovered:
                self.assertEqual(recovered.execute('SELECT count(*) FROM items').fetchone()[0], 4)
