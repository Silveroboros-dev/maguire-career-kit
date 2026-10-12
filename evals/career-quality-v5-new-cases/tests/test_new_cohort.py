"""New-cohort harness controls; never execute the challenge packets."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_pipeline import pipeline, fixture, projection


class NewCohortTests(unittest.TestCase):
    def test_content_identity_survives_serialized_presentation_renaming(self):
        raw, normal, reviewed = fixture()
        identity = pipeline.case_identity(raw['rows'][0])
        renamed = json.loads(json.dumps(raw))
        renamed['rows'][0]['case_id'] = 'unrelated-label'
        renamed['rows'][0]['title'] = 'a different title'
        renamed['rows'][0]['sources'][0]['id'] = 'new-source-label'
        self.assertEqual(identity, pipeline.case_identity(renamed['rows'][0]))
        for field in ('answer', 'date', 'status'):
            changed = copy.deepcopy(renamed['rows'][0])
            if field == 'answer':
                changed['answer']['text'] = 'A materially different answer.'
            elif field == 'date':
                changed['decision_at'] = '2026-10-01T12:00:00Z'
            else:
                changed['sources'][0]['status'] = 'withdrawn'
            self.assertNotEqual(identity, pipeline.case_identity(changed))

    def test_projection_binds_canonical_content_and_contains_no_label(self):
        raw, normal, reviewed = fixture()
        packets, mapping = projection(raw, normal, reviewed)
        self.assertEqual(mapping[0]['case_content_sha256'], pipeline.case_identity(raw['rows'][0]))
        self.assertNotIn('case_content_sha256', packets[0]['packet'])
        self.assertNotIn('expected', json.dumps(packets))

    def test_frozen_runtime_drift_blocks_execution_preflight(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            frozen = repo / 'evals' / 'frozen'
            current = repo / 'evals' / 'new'
            frozen.mkdir(parents=True)
            current.mkdir()
            names = ('checker.py', 'v3_core.py', 'grade_packets.py', 'measurement.py')
            for name in names:
                (frozen / name).write_text('fixture ' + name)
                (current / name).write_bytes((frozen / name).read_bytes())
            (frozen / 'SCHEMA.md').write_text('public schema')
            (current / 'FROZEN_SCHEMA.md').write_text('public schema')
            runtime = {name: pipeline.bound(frozen / name) for name in names}
            (frozen / 'FREEZE.json').write_text(json.dumps({'files': runtime}))
            (current / 'PREDECESSOR.json').write_text(json.dumps({'files': {}, 'frozen_runtime': runtime}))
            with patch.object(pipeline, 'ROOT', current), patch.object(pipeline, 'FROZEN', frozen), \
                    patch.object(pipeline, 'REPO', repo), patch.object(pipeline, 'BASE_SHA', pipeline.sha(current / 'v3_core.py')):
                self.assertEqual(pipeline.verify_predecessors(), 0)
                (current / 'checker.py').write_text('changed runtime')
                with self.assertRaisesRegex(ValueError, 'frozen v5 runtime drift'):
                    pipeline.verify_predecessors()

    def test_second_start_cannot_execute_worker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'FREEZE.json').write_text('{}')
            (root / 'START.json').write_text('{"original":true}')
            packets, mapping = projection()
            with patch.object(pipeline, 'ROOT', root), \
                    patch.object(pipeline, 'verify_freeze', return_value=(packets, mapping, [], 0)), \
                    patch.object(pipeline.subprocess, 'run') as worker:
                with self.assertRaises(FileExistsError):
                    pipeline.run(root / 'runs' / 'second')
                worker.assert_not_called()
            self.assertEqual((root / 'START.json').read_text(), '{"original":true}')


if __name__ == '__main__':
    unittest.main()
