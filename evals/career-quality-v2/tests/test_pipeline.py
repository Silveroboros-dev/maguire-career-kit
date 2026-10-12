"""Projection/corpus-boundary tests using only v1 development inputs."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pipeline


class PipelineTests(unittest.TestCase):
    def setUp(self):
        # Known v1 material only. New v2 answer corpus is excluded before freeze.
        folder = pipeline.V1 / 'preference-fit/PF-01'
        self.data = {n: json.loads((folder / n).read_text()) for n in pipeline.audit.FILES}

    def test_projection_is_independent_of_presentation_ids(self):
        inp, gold = self.data['input.json'], self.data['gold.json']
        answer = self.data['answers.json']['answers'][0]
        a = pipeline.project(inp, gold, answer)
        inp['case_id'] = gold['case_id'] = 'arbitrary'
        answer['answer_id'] = 'not-a-label'
        self.assertEqual(a, pipeline.project(inp, gold, answer))
        self.assertEqual({'units', 'forbidden_assessment_targets', 'acceptable_actions'}, set(a['gold']))
        self.assertNotIn('answer_id', a['answer'])

    def test_cross_case_and_label_metadata_rejected(self):
        inp, gold = self.data['input.json'], self.data['gold.json']
        answer = self.data['answers.json']['answers'][0]
        gold['case_id'] = 'wrong'
        with self.assertRaisesRegex(ValueError, 'cross-case'):
            pipeline.project(inp, gold, answer)
        gold['case_id'] = inp['case_id']
        answer['expected_verdict'] = 'pass'
        with self.assertRaisesRegex(ValueError, 'leakage'):
            pipeline.project(inp, gold, answer)

    def test_signature_ignores_prose_but_not_labels_or_quote_content(self):
        answer = self.data['answers.json']['answers'][0]
        changed = copy.deepcopy(answer)
        changed['assessments'][0]['rationale'] = 'An incorrect interpretation with the same evidence.'
        self.assertEqual(pipeline.metadata_signature(answer), pipeline.metadata_signature(changed))
        changed['assessments'][0]['evidence'][0]['quote'] += ' invented'
        self.assertNotEqual(pipeline.metadata_signature(answer), pipeline.metadata_signature(changed))

    def challenge(self):
        data = copy.deepcopy(self.data)
        base = data['answers.json']['answers'][0]
        annotations = data['annotations.json']['answers']
        variants = []
        for i in range(4):
            answer = copy.deepcopy(base)
            answer['answer_id'] = f'answer_{i+1:02d}'
            if i:
                answer['conclusion']['text'] += f' Invented test-only prose variant {i}.'
            if i >= 2:
                annotations[i]['mutation']['changed_paths'] = pipeline.audit.diff_paths(base, answer)
            variants.append(answer)
        data['answers.json']['answers'] = variants
        return data

    def audit_one(self, data):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / 'preference-fit/PF-01'
            folder.mkdir(parents=True)
            for name, doc in data.items():
                (folder / name).write_text(json.dumps(doc))
            with patch.object(pipeline, 'NEW', {'preference-fit': ('PF', 'preference_fit', 1)}):
                return pipeline.audit_new(root)

    def test_structural_challenge_audit_never_claims_semantic_truth(self):
        report = self.audit_one(self.challenge())
        self.assertTrue(report['valid'])
        self.assertFalse(report['semantic_quality_proven'])
        self.assertEqual(4, report['answers'])

    def test_negative_must_keep_correct_label(self):
        data = self.challenge()
        data['answers.json']['answers'][2]['assessments'][0]['label'] = 'aligned'
        data['annotations.json']['answers'][2]['mutation']['changed_paths'] = pipeline.audit.diff_paths(
            data['answers.json']['answers'][0], data['answers.json']['answers'][2])
        with self.assertRaisesRegex(ValueError, 'disallowed label'):
            self.audit_one(data)

    def test_even_allowed_action_variation_is_forbidden_in_preference_challenge(self):
        data = self.challenge()
        base_action = data['answers.json']['answers'][0]['conclusion']['action']
        data['answers.json']['answers'][2]['conclusion']['action'] = next(
            a for a in data['gold.json']['acceptable_actions'] if a != base_action)
        data['annotations.json']['answers'][2]['mutation']['changed_paths'] = pipeline.audit.diff_paths(
            data['answers.json']['answers'][0], data['answers.json']['answers'][2])
        with self.assertRaisesRegex(ValueError, 'differ from base'):
            self.audit_one(data)

    def test_original_v1_tree_unchanged(self):
        pipeline.verify_predecessor()


if __name__ == '__main__':
    unittest.main()
