import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from export_proxy_usage import export


class ProxyUsageTests(unittest.TestCase):
    def test_truncation_is_counted_and_incomplete_sequences_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for index, finish in enumerate(['length', 'stop']):
                messages = [{'role': 'user', 'content': 'Review the commitment.'}]
                if index:
                    messages += [{'role': 'assistant', 'content': 'Partial'}, {'role': 'user', 'content': 'Continue'}]
                data = {'request': {'messages': messages}, 'response': {
                    'id': str(index), 'choices': [{'finish_reason': finish}],
                    'usage': {'prompt_tokens': 10 + index, 'completion_tokens': 5}},
                    'http_status': 200, 'seconds': 2}
                path = Path(directory) / f'{index}.json'
                path.write_text(json.dumps(data)); paths.append(path)
            result = export(paths, 2)
            self.assertEqual(result['total_input_tokens'], 21)
            self.assertEqual(result['total_output_tokens'], 10)
            self.assertEqual(result['calls'][0]['finish_reason'], 'length')
            for bad in [paths[:1], paths[::-1], [paths[0], paths[0]]]:
                with self.assertRaises(ValueError):
                    export(bad, 2)
            with self.assertRaisesRegex(ValueError, 'completed answer'):
                export(paths[:1], 1)
