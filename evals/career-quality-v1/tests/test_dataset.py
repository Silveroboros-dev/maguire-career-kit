"""Adversarial checks of dataset integrity checks, not tests of semantic grading."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('dataset_audit', ROOT / 'validate_dataset.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class DatasetBoundaries(unittest.TestCase):
    def setUp(self):
        folder = ROOT / 'candidate-fit/CF-01'
        self.data = {name: json.loads((folder / name).read_text()) for name in audit.FILES}

    def run_case(self, data=None):
        return audit.audit_case(data or self.data, 'CF-01', 'candidate_fit')

    def test_full_dataset_and_inventory(self):
        result = audit.audit(ROOT, ROOT / 'MANIFEST.json')
        self.assertTrue(result['valid'], result['errors'])
        self.assertEqual((result['case_count'], result['positive_answers'], result['negative_answers']),
                         (24, 48, 48))
        self.assertFalse(result['semantic_quality_proven'])

    def test_cross_case_answer_binding_rejected(self):
        self.data['answers.json']['case_id'] = 'CF-02'
        with self.assertRaisesRegex(ValueError, 'cross-case binding'):
            self.run_case()

    def test_labels_cannot_be_added_to_model_input(self):
        self.data['input.json']['expected_answer'] = 'supported'
        with self.assertRaisesRegex(ValueError, 'unexpected or missing fields'):
            self.run_case()

    def test_verdict_metadata_cannot_leak_into_answer(self):
        self.data['answers.json']['answers'][1]['expected_verdict'] = 'pass'
        with self.assertRaisesRegex(ValueError, 'answer: unexpected or missing fields'):
            self.run_case()

    def test_malformed_gold_is_an_invalid_dataset_not_a_crash(self):
        self.data['gold.json'] = []
        with self.assertRaisesRegex(ValueError, 'gold: expected object'):
            self.run_case()

    def test_malformed_conclusion_is_rejected(self):
        self.data['answers.json']['answers'][1]['conclusion'] = []
        with self.assertRaisesRegex(ValueError, 'conclusion: unexpected or missing fields'):
            self.run_case()

    def test_future_evidence_cannot_leak_into_decision_snapshot(self):
        self.data['input.json']['candidate']['facts'][0]['observed_at'] = '2027-01-01T00:00:00Z'
        with self.assertRaisesRegex(ValueError, 'future fact'):
            self.run_case()

    def test_missing_positive_unit_rejected(self):
        self.data['answers.json']['answers'][0]['assessments'].pop()
        with self.assertRaisesRegex(ValueError, 'positive omits/adds'):
            self.run_case()

    def test_real_quote_replaced_by_fabrication_rejected(self):
        self.data['answers.json']['answers'][0]['assessments'][0]['evidence'][0]['quote'] = 'FABRICATED QUOTE NOT IN THE SOURCE'
        with self.assertRaisesRegex(ValueError, 'citation expectation mismatch'):
            self.run_case()

    def test_declared_fabrication_negative_can_be_represented(self):
        base = self.data['answers.json']['answers'][0]
        bad = copy.deepcopy(base)
        bad['answer_id'] = 'answer_03'
        bad['assessments'][0]['evidence'][0]['quote'] = 'FABRICATED QUOTE NOT IN THE SOURCE'
        self.data['answers.json']['answers'][2] = bad
        annotation = self.data['annotations.json']['answers'][2]
        annotation['citation_integrity'] = 'fail'
        annotation['mutation']['changed_paths'] = audit.diff_paths(base, bad)
        # Structural acceptance of an expressly labelled bad example is not PASS
        # for that example's advice or annotation semantics.
        result = self.run_case()
        self.assertEqual(result['intentional_citation_failures'], 1)

    def test_undeclared_negative_mutation_rejected(self):
        self.data['answers.json']['answers'][2]['conclusion']['text'] += ' Unlisted extra change.'
        with self.assertRaisesRegex(ValueError, 'mutation path mismatch'):
            self.run_case()

    def test_unknown_source_and_false_approval_rejected(self):
        changed = copy.deepcopy(self.data)
        changed['gold.json']['units'][0]['acceptable_evidence_sets'] = [['fact_absent']]
        with self.assertRaisesRegex(ValueError, 'unknown source'):
            self.run_case(changed)
        self.data['gold.json']['human_approved'] = True
        with self.assertRaisesRegex(ValueError, 'approval claim'):
            self.run_case()

    def test_inventory_drift_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'manifest.json'
            original = json.loads((ROOT / 'MANIFEST.json').read_text())
            original['files'][next(iter(original['files']))]['sha256'] = '0' * 64
            path.write_text(json.dumps(original))
            result = audit.audit(ROOT, path)
            self.assertFalse(result['valid'])
            self.assertTrue(any('inventory hashes' in e for e in result['errors']))

    def test_json_pointer_paths_and_array_replacement(self):
        self.assertEqual(audit.diff_paths({'a/b': {'~c': 1}}, {'a/b': {'~c': 2}}), ['/a~1b/~0c'])
        self.assertEqual(audit.diff_paths({'x': [1]}, {'x': [1, 2]}), ['/x'])


if __name__ == '__main__':
    unittest.main()
