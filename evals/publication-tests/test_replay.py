import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('published_replay', ROOT / 'replay.py')
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)


class PublicationTests(unittest.TestCase):
    def test_manifest_detects_byte_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = root / 'data.json'
            p.write_text('{"truth":1}')
            (root / 'PUBLICATION.json').write_text(json.dumps({'files': {'data.json': replay.bound(p)}}))
            replay.verify_manifest(root)
            p.write_text('{"truth":2}')
            with self.assertRaisesRegex(ValueError, 'published file drift'):
                replay.verify_manifest(root)

    def test_manifest_rejects_reference_outside_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            root = parent / 'evals'
            root.mkdir()
            p = parent / 'outside.json'
            p.write_text('{}')
            (root / 'PUBLICATION.json').write_text(json.dumps({'files': {'../outside.json': replay.bound(p)}}))
            with self.assertRaisesRegex(ValueError, 'publication inventory'):
                replay.verify_manifest(root)

    def test_manifest_rejects_unlisted_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = root / 'data.json'
            p.write_text('{}')
            (root / 'PUBLICATION.json').write_text(json.dumps({'files': {'data.json': replay.bound(p)}}))
            (root / 'unlisted.py').write_text('unbound executable')
            with self.assertRaisesRegex(ValueError, 'publication inventory'):
                replay.verify_manifest(root)

    def test_manifest_rejects_empty_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'PUBLICATION.json').write_text(json.dumps({'files': {}}))
            with self.assertRaisesRegex(ValueError, 'empty'):
                replay.verify_manifest(root)

    def test_original_frozen_dependencies_must_be_published(self):
        newer = ('pipeline.py', 'checker.py', 'v3_core.py', 'grade_packets.py',
                 'measurement.py', 'FREEZE.json')
        older = ('checker.py', 'v3_core.py', 'grade_packets.py', 'measurement.py', 'FREEZE.json')
        entries = {'career-quality-v6-new-cases/' + name: {} for name in newer}
        entries.update({'career-quality-v6/' + name: {} for name in older})
        replay.require_dependencies({'files': entries})
        for name in older:
            missing = dict(entries)
            del missing['career-quality-v6/' + name]
            with self.assertRaisesRegex(ValueError, 'critical runtime or freeze missing'):
                replay.require_dependencies({'files': missing})


if __name__ == '__main__':
    unittest.main()
