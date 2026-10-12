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

    def test_predecessor_core_and_raw_gold_drift_block_preflight(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            baseline = repo / 'evals' / 'old'
            current = repo / 'evals' / 'new'
            baseline.mkdir(parents=True)
            current.mkdir()
            (baseline / 'checker.py').write_text('old checker')
            (current / 'v3_core.py').write_text('immutable core')
            for folder in ('raw', 'gold'):
                (baseline / folder).mkdir()
                (current / folder).mkdir()
                for family in pipeline.FAMILIES:
                    (baseline / folder / (family + '.json')).write_text('{}')
                    (current / folder / (family + '.json')).write_text('{}')
            manifest = dict(files={'evals/old/checker.py': pipeline.bound(baseline / 'checker.py')},
                            base_core=pipeline.bound(current / 'v3_core.py'))
            (current / 'PREDECESSOR.json').write_text(json.dumps(manifest))
            with patch.object(pipeline, 'ROOT', current), patch.object(pipeline, 'BASELINE', baseline), \
                    patch.object(pipeline, 'REPO', repo), patch.object(pipeline, 'BASE_SHA', pipeline.sha(current / 'v3_core.py')):
                self.assertEqual(pipeline.verify_predecessors(), 1)
                target = current / 'raw/candidate-fit.json'
                target.write_text('changed source')
                with self.assertRaisesRegex(ValueError, 'frozen raw/gold changed'):
                    pipeline.verify_predecessors()
                target.write_text('{}')
                (baseline / 'checker.py').write_text('changed historical runtime')
                with self.assertRaisesRegex(ValueError, 'predecessor changed'):
                    pipeline.verify_predecessors()

    def test_comparison_joins_by_content_not_presentation_id(self):
        _, mapping = projection()
        before_mapping = copy.deepcopy(mapping)
        before_mapping[0]['case_id'] = 'old-label'
        def measured(cid, outcome):
            return dict(overall={}, rows=[dict(case_id=cid, family='candidate-fit', expected='pass',
                         actual=outcome, intended_error_claim_ids=[], localized_error_claim_ids=[])])
        after = measured(mapping[0]['case_id'], 'pass')
        before = measured('old-label', 'needs_review')
        result = pipeline.compare_measurements(mapping, after, before_mapping, before)
        self.assertEqual((result['rows'][0]['v5'], result['rows'][0]['v6']), ('needs_review', 'pass'))
        before['rows'][0]['expected'] = 'fail'
        with self.assertRaisesRegex(ValueError, 'paired gold mismatch'):
            pipeline.compare_measurements(mapping, after, before_mapping, before)
        before['rows'][0]['expected'] = 'pass'
        before_mapping[0]['case_content_sha256'] = 'foreign'
        with self.assertRaisesRegex(ValueError, 'comparison content mismatch'):
            pipeline.compare_measurements(mapping, after, before_mapping, before)

    def test_frozen_v6_runtime_change_rejected_before_projection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checker = root / 'checker.py'
            checker.write_text('frozen v6 fixture')
            (root / 'FREEZE.json').write_text(json.dumps({'files': {'checker.py': pipeline.bound(checker)}}))
            checker.write_text('edited after freeze')
            with patch.object(pipeline, 'ROOT', root), \
                    patch.object(pipeline, 'verify_predecessors', return_value=454), \
                    patch.object(pipeline, 'load_projection') as project:
                with self.assertRaisesRegex(ValueError, 'frozen file changed'):
                    pipeline.verify_freeze()
                project.assert_not_called()

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
