"""Adversarial projection, process-boundary and measurement checks with new fixtures."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
import grade_packets
from measure import canonical, measure
from run_offline import project
from test_grader_boundaries import candidate_packet


def bind(packet):
    return {'packet_sha256': hashlib.sha256(canonical(packet)).hexdigest(), 'packet': packet}


class ProjectionBoundary(unittest.TestCase):
    def test_projection_ignores_display_identifiers_and_excludes_catalogs(self):
        packet = candidate_packet()
        inp = {**packet['input'], 'grader': packet['grader'], 'case_id': 'old', 'schema': 'input'}
        gold = {**packet['gold'], 'case_id': 'old', 'critical_errors': ['DO NOT LEAK'], 'title': 'marker'}
        answer = {**packet['answer'], 'answer_id': 'answer_01'}
        first = project(inp, gold, answer)
        inp['case_id'] = gold['case_id'] = 'renamed'
        answer['answer_id'] = 'the_wrong_answer'
        self.assertEqual(first, project(inp, gold, answer))
        self.assertEqual(set(first['gold']), {'units', 'forbidden_assessment_targets', 'acceptable_actions'})
        self.assertNotIn('DO NOT LEAK', canonical(first).decode())
        answer['expected_verdict'] = 'pass'
        with self.assertRaisesRegex(ValueError, 'leakage'):
            project(inp, gold, answer)

    def test_projection_rejects_cross_case_gold(self):
        packet = candidate_packet()
        with self.assertRaisesRegex(ValueError, 'cross-case'):
            project({**packet['input'], 'case_id': 'a'}, {**packet['gold'], 'case_id': 'b'}, {})

    def test_first_grade_call_is_pure_and_results_are_content_bound(self):
        row = bind(candidate_packet())
        original = copy.deepcopy(row)
        result = grade_packets.grade_rows([row])
        self.assertEqual('pass', result[0]['result']['verdict'], result)
        self.assertIsNone(result[0]['execution_error'])
        self.assertEqual(row, original)
        self.assertEqual(row['packet_sha256'], result[0]['packet_sha256'])

    def test_duplicate_or_stale_packet_is_rejected(self):
        row = bind(candidate_packet())
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            grade_packets.grade_rows([row, row])
        row['packet']['answer']['conclusion']['text'] = 'Changed after binding.'
        with self.assertRaisesRegex(ValueError, 'identity'):
            grade_packets.grade_rows([row])

    def test_file_and_network_attempts_become_technical_failures(self):
        def file_attempt(packet):
            return Path('/not-a-real-file').read_text()
        def socket_attempt(packet):
            import socket
            return socket.socket()
        # Import outside the audited region: a socket constructor itself is denied.
        import socket
        for function in (file_attempt, socket_attempt):
            with self.subTest(function=function.__name__), patch.object(grade_packets, 'grade', function):
                result = grade_packets.grade_rows([bind(candidate_packet())])[0]
                self.assertEqual('invalid', result['result']['verdict'])
                self.assertIn('offline pure-grader boundary', result['execution_error'])


class MeasurementBoundary(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        folder = self.root / 'candidate-fit' / 'CF-NEW'
        folder.mkdir(parents=True)
        answers = [{**candidate_packet()['answer'], 'answer_id': name} for name in ('good', 'bad', 'broken')]
        self.mapping = [{'packet_sha256': str(i), 'case_path': 'candidate-fit/CF-NEW',
                         'case_id': 'CF-NEW', 'grader': 'candidate_fit', 'answer_id': a['answer_id'],
                         'answer_sha256': hashlib.sha256(canonical(a)).hexdigest()} for i, a in enumerate(answers)]
        annotations = [{'answer_id': a['answer_id'], 'expected_verdict': 'pass' if i == 0 else 'fail',
                        'reason': 'Invented fixture.', 'mutation': None,
                        'expected_findings': [] if i == 0 else [{'criterion_id': 'CF-LABEL',
                                                               'target_id': 'jd_prototype', 'severity': 'major',
                                                               'explanation': 'Expected test defect.'}]} for i, a in enumerate(answers)]
        (folder / 'answers.json').write_text(json.dumps({'case_id': 'CF-NEW', 'answers': answers}))
        (folder / 'annotations.json').write_text(json.dumps({'case_id': 'CF-NEW', 'answers': annotations}))
        self.predictions = [{'packet_sha256': str(i), 'execution_error': None,
                             'result': {'verdict': verdict, 'findings': []}} for i, verdict in enumerate(('pass', 'pass', 'invalid'))]

    def tearDown(self):
        self.temp.cleanup()

    def test_invalids_remain_visible_and_rates_have_explicit_denominators(self):
        c = measure(self.root, self.mapping, self.predictions)['groups']['all']
        self.assertEqual((3, 1, 1, 1), (c['answers'], c['false_acceptance'], c['accepted_correct'], c['invalid']))
        self.assertEqual(1, c['evaluated_incorrect'])
        self.assertEqual(1, c['invalid_incorrect'])
        self.assertEqual(1.0, c['false_acceptance_rate_evaluated'])
        self.assertEqual(0.5, c['false_acceptance_rate_attempted'])

    def test_reordering_does_not_change_identity_join(self):
        self.assertEqual(measure(self.root, self.mapping, self.predictions),
                         measure(self.root, self.mapping, list(reversed(self.predictions))))

    def test_missing_extra_duplicate_predictions_fail_closed(self):
        for predictions in (self.predictions[:-1], self.predictions + [self.predictions[0]],
                            self.predictions + [{'packet_sha256': 'extra'}]):
            with self.subTest(predictions=predictions), self.assertRaises(ValueError):
                measure(self.root, self.mapping, predictions)

    def test_rejected_bad_answer_is_not_automatically_localized(self):
        self.predictions[1]['result'] = {'verdict': 'fail', 'findings': [
            {'criterion_id': 'CF-ACTION', 'target_id': None}]}
        result = measure(self.root, self.mapping, self.predictions)
        self.assertEqual(1, result['groups']['all']['caught_error'])
        self.assertEqual(0, result['groups']['all']['exact_criterion_target_matches'])
        self.predictions[1]['result']['findings'][0] = {'criterion_id': 'CF-LABEL', 'target_id': 'jd_prototype'}
        self.assertEqual(1, measure(self.root, self.mapping, self.predictions)['groups']['all']['exact_criterion_target_matches'])

    def test_answer_drift_fails_join(self):
        self.mapping[0]['answer_sha256'] = 'incorrect'
        with self.assertRaisesRegex(ValueError, 'changed'):
            measure(self.root, self.mapping, self.predictions)


if __name__ == '__main__':
    unittest.main()
