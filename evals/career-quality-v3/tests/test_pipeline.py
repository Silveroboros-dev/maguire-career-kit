"""Projection, identity, localization and pure execution boundary checks."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pipeline
from test_checker import packet


def authored():
    return {'rows': [{'example_id': 'display-1', 'case_id': 'case-1', 'answer_id': 'answer-1',
                      'packet': packet()}]}


def measurement_fixture(actual='fail', expected='fail'):
    p = packet()
    identity = pipeline.digest(p)
    a = p['claims'][0]['anchor']
    relation = {'fail': 'not_established', 'pass': 'supported', 'needs_review': None}[actual]
    c = dict(id='c1', anchor=a, evidence_relation=relation, verdict=actual)
    finding = dict(claim_id='c1', anchor=a, evidence_relation=relation,
                   rule='synthetic', explanation='synthetic', axes=[], evidence_ids=[])
    predictions = [dict(packet_sha256=identity, execution_error=None,
                        result=dict(verdict=actual, claims=[c], findings=[finding] if actual == 'fail' else [],
                                    review_reasons=['unresolved'] if actual == 'needs_review' else []))]
    mapping = [dict(example_id='row-1', case_id='case-1', answer_id='answer-1', packet_sha256=identity)]
    wanted = {'fail': 'not_established', 'pass': 'supported', 'needs_review': None}[expected]
    truth = {'rows': [dict(example_id='row-1', verdict=expected,
                           claims=[dict(claim_id='c1', verdict=expected, evidence_relation=wanted, anchor=a)])]}
    return predictions, mapping, truth


class PipelineTests(unittest.TestCase):
    def test_projection_removes_catalog_metadata_and_does_not_mutate(self):
        data = authored()
        before = copy.deepcopy(data)
        packets, mapping = pipeline.project(data)
        self.assertEqual(data, before)
        self.assertEqual(set(packets[0]), {'packet_sha256', 'packet'})
        self.assertEqual(set(packets[0]['packet']),
                         {'schema', 'grader', 'decision_at', 'sources', 'claims', 'coverage'})
        self.assertNotIn('display-1', json.dumps(packets))
        data['rows'][0]['example_id'] = 'renumbered'
        self.assertEqual(pipeline.project(data)[0], packets)
        self.assertNotEqual(pipeline.project(data)[1], mapping)

    def test_duplicate_packet_identity_rejected(self):
        data = authored()
        data['rows'].append(copy.deepcopy(data['rows'][0]))
        with self.assertRaises(ValueError): pipeline.project(data)

    def test_measurement_separates_misses_false_rejects_and_abstentions(self):
        self.assertEqual(pipeline.measure(*measurement_fixture('pass', 'fail'))['false_acceptances'], ['row-1'])
        self.assertEqual(pipeline.measure(*measurement_fixture('fail', 'pass'))['false_rejections'], ['row-1'])
        review = pipeline.measure(*measurement_fixture('needs_review', 'fail'))
        self.assertEqual(review['needs_review'], ['row-1'])
        self.assertEqual(review['false_acceptances'], [])
        self.assertEqual(review['error_atoms_matched_relation_and_span'], 0)
        forced = pipeline.measure(*measurement_fixture('pass', 'needs_review'))
        self.assertEqual(forced['forced_decisions_on_ambiguity'], ['row-1'])

    def test_cross_case_missing_and_wrong_span_fail_closed(self):
        p, m, t = measurement_fixture()
        p[0]['packet_sha256'] = 'wrong'
        with self.assertRaises(ValueError): pipeline.measure(p, m, t)
        p, m, t = measurement_fixture()
        with self.assertRaises(ValueError): pipeline.measure([], m, t)
        p[0]['result']['findings'][0]['anchor'] = dict(p[0]['result']['findings'][0]['anchor'], start=9)
        with self.assertRaises(ValueError): pipeline.measure(p, m, t)

    def test_wrong_relation_is_not_credited_as_expected_atom(self):
        p, m, t = measurement_fixture()
        p[0]['result']['claims'][0]['evidence_relation'] = 'contradicted'
        p[0]['result']['findings'][0]['evidence_relation'] = 'contradicted'
        result = pipeline.measure(p, m, t)
        self.assertEqual(result['error_atoms_matched_relation_and_span'], 0)
        self.assertEqual(len(result['relation_mismatches']), 1)

    def test_guard_blocks_file_and_network_during_pure_grade(self):
        import grade_packets
        value = packet()
        rows = [dict(packet_sha256=pipeline.digest(value), packet=value)]
        def tries_file(_):
            with open(__file__) as stream: return stream.read()
        with patch.object(grade_packets, 'grade_fragment', tries_file):
            result = grade_packets.execute(rows)[0]
        self.assertEqual(result['result']['verdict'], 'invalid')
        self.assertIn('PermissionError', result['execution_error'])
        def tries_socket(_):
            import socket
            return socket.socket()
        with patch.object(grade_packets, 'grade_fragment', tries_socket):
            result = grade_packets.execute(rows)[0]
        self.assertEqual(result['result']['verdict'], 'invalid')
        self.assertIn('PermissionError', result['execution_error'])


if __name__ == '__main__':
    unittest.main()
