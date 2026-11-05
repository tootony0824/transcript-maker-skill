import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('render', Path(__file__).resolve().parents[1] / 'transcript-maker/scripts/render_transcript.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class RenderTests(unittest.TestCase):
    def test_qwen_chunks_and_whisper_segments(self):
        for key in ('chunks', 'segments'):
            result = m.render({key: [{'start': 61, 'end': 62, 'text': '你好。'}]}, '标题', 120)
            self.assertIn('[00:01:01] 你好。', result)

    def test_rejects_truncated_and_invalid_timing(self):
        for data in ({'truncated': True, 'chunks': []}, {'chunks': [{'start': 8, 'end': 12, 'text': 'x'}]}, {'chunks': [{'start': 5, 'end': 6, 'text': 'x'}, {'start': 4, 'end': 5, 'text': 'y'}]}):
            with self.assertRaises(ValueError):
                m.render(data, '标题', 10)


if __name__ == '__main__':
    unittest.main()
