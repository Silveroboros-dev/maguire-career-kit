"""Harness integrity tests use invented fixtures, never run new cases through checker."""
import copy
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'pipeline.py'
spec = importlib.util.spec_from_file_location('challenge_pipeline', MODULE)
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)


def fixture():
    fact = dict(subject='person', predicate='console_use', object='console', polarity='positive',
                modality='self_report', epistemic_scope='world', scope={}, time={}, measure=None)
    raw = dict(family='candidate-fit', human_approved=False,
               rows=[dict(case_id='presentation-1', title='metadata title', decision_at='2026-10-12T12:00:00Z',
                          sources=[dict(id='s1', kind='candidate_fact', status='active',
                                        observed_at='2026-10-11T12:00:00Z', text='I used a console.')],
                          answer={'text': 'I used a console.'})])
    normal = dict(family='candidate-fit', human_approved=False,
                  rows=[dict(case_id='presentation-1', sources=[dict(id='s1', facts=[fact])],
                             claims=[dict(id='c1', quote='I used a console.', stance='asserted', readings=[fact], check=None)])])
    reviewed = {'presentation-1': dict(source_inventory_complete=True, fragment_complete=True, claim_ids=['c1'])}
    return raw, normal, reviewed


def projection(raw=None, normal=None, reviewed=None):
    r, n, v = fixture()
    return pipeline.project_family(raw or r, normal or n, 'a' * 64, reviewed or v)


def fake_outcome(packet, verdict, failed=()):
    claims = []
    for c in packet['packet']['claims'] if verdict != 'invalid' else []:
        status = 'fail' if c['id'] in failed else ('needs_review' if verdict == 'needs_review' else 'pass')
        claims.append(dict(id=c['id'], anchor=c['anchor'], verdict=status, parse_status='valid',
                           reasoning_status='unresolved' if status == 'needs_review' else 'resolved',
                           evidence_relation='not_established' if status == 'fail' else None,
                           rule='synthetic_fixture', explanation='Synthetic harness fixture.',
                           support_evidence_ids=[], counter_evidence_ids=[], limited_evidence_ids=[],
                           evidence_ids=[], inspected_source_ids=[], axes=[]))
    keys = ('anchor', 'evidence_relation', 'rule', 'explanation', 'axes', 'evidence_ids')
    findings = [dict(claim_id=c['id'], **{k: c[k] for k in keys}) for c in claims if c['verdict'] == 'fail']
    return dict(packet_sha256=packet['packet_sha256'], execution_error=None,
                result=dict(schema='maguire-claim-packet-v6', scope='fragment',
                            assurance='manual_normalization_agent_reviewed', whole_answer_verdict=None,
                            verdict=verdict, claims=claims, findings=findings,
                            review_reasons=['fixture technical failure'] if verdict == 'invalid' else []))


class ProjectionTests(unittest.TestCase):
    def test_presentation_ids_and_gold_metadata_do_not_reach_runtime(self):
        raw, normal, reviewed = fixture()
        before, _ = projection(raw, normal, reviewed)
        raw['rows'][0].update(case_id='other-label', title='fail: tempting tag', expected='fail')
        normal['rows'][0].update(case_id='other-label', expected='pass')
        reviewed['other-label'] = reviewed.pop('presentation-1')
        after, mapping = projection(raw, normal, reviewed)
        # Fixed byte hash here isolates projection; real raw edits change the anchor hash.
        self.assertEqual(before, after)
        self.assertEqual(mapping[0]['case_id'], 'other-label')
        self.assertEqual(set(after[0]), {'packet_sha256', 'packet'})
        self.assertEqual(set(after[0]['packet']), {'schema', 'grader', 'decision_at', 'sources', 'claims', 'coverage'})

    def test_duplicate_missing_and_foreign_rows_rejected(self):
        for kind in ('duplicate', 'missing', 'foreign'):
            raw, normal, reviewed = fixture()
            if kind == 'duplicate':
                normal['rows'].append(copy.deepcopy(normal['rows'][0]))
            elif kind == 'missing':
                normal['rows'] = []
            else:
                normal['rows'][0]['case_id'] = 'different-case'
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                projection(raw, normal, reviewed)

    def test_missing_or_cross_case_source_rejected(self):
        for source_id in (None, 'other-case-source'):
            raw, normal, reviewed = fixture()
            if source_id:
                normal['rows'][0]['sources'][0]['id'] = source_id
            else:
                normal['rows'][0]['sources'] = []
            with self.subTest(source_id=source_id), self.assertRaises(ValueError):
                projection(raw, normal, reviewed)

    def test_claim_quote_must_belong_to_own_raw_answer(self):
        raw, normal, reviewed = fixture()
        normal['rows'][0]['claims'][0]['quote'] = 'Unrelated source.'
        with self.assertRaises(ValueError):
            projection(raw, normal, reviewed)
        normal['rows'][0]['claims'][0]['quote'] = 'I used a console.'
        raw['rows'][0]['answer']['text'] *= 2
        with self.assertRaises(ValueError):
            projection(raw, normal, reviewed)

    def test_incomplete_review_is_not_silently_complete(self):
        for field in ('fragment_complete', 'source_inventory_complete', 'claim_ids'):
            raw, normal, reviewed = fixture()
            reviewed['presentation-1'][field] = [] if field == 'claim_ids' else False
            with self.subTest(field=field), self.assertRaises(ValueError):
                projection(raw, normal, reviewed)

    def test_raw_hash_is_part_of_content_identity(self):
        raw, normal, reviewed = fixture()
        original, _ = pipeline.project_family(raw, normal, 'a' * 64, reviewed)
        drifted, _ = pipeline.project_family(raw, normal, 'b' * 64, reviewed)
        self.assertNotEqual(original[0]['packet_sha256'], drifted[0]['packet_sha256'])
        self.assertNotEqual(original[0]['packet']['coverage']['source_sha256'],
                            drifted[0]['packet']['coverage']['source_sha256'])

    def test_semantic_values_not_changed_by_projection(self):
        raw, normal, reviewed = fixture()
        before = copy.deepcopy(normal)
        packets, _ = projection(raw, normal, reviewed)
        self.assertEqual(before, normal)
        self.assertEqual(packets[0]['packet']['sources'][0]['facts'], normal['rows'][0]['sources'][0]['facts'])
        self.assertEqual(packets[0]['packet']['claims'][0]['readings'], normal['rows'][0]['claims'][0]['readings'])


class MeasurementTests(unittest.TestCase):
    def test_review_is_neither_detected_error_nor_false_rejection(self):
        rows = []
        for i, (gold, actual) in enumerate([('fail', 'pass'), ('pass', 'fail'), ('pass', 'needs_review'),
                                           ('fail', 'needs_review'), ('needs_review', 'needs_review'),
                                           ('needs_review', 'fail'), ('pass', 'invalid')]):
            rows.append(dict(case_id=str(i), expected=gold, actual=actual, execution_error=None,
                             intended_error_claim_ids=['c1'] if gold == 'fail' else [],
                             localized_error_claim_ids=[], other_failed_claim_ids=[]))
        result = pipeline.metric_group(rows)
        self.assertEqual(result['total'], 7)
        self.assertEqual(result['missed_errors'], ['0'])
        self.assertEqual(result['false_rejections'], ['1'])
        self.assertEqual(result['needs_review'], {'pass': ['2'], 'fail': ['3'], 'needs_review': ['4']})
        self.assertEqual(result['ambiguous_forced_decisions'], ['5'])
        self.assertEqual(result['invalid'], ['6'])
        self.assertEqual(sum(sum(c.values()) for c in result['confusion'].values()), 7)

    def test_missing_duplicate_foreign_or_reordered_predictions_rejected(self):
        packets, mapping = projection()
        p2 = copy.deepcopy(packets[0])
        p2['packet']['decision_at'] = '2026-10-13T12:00:00Z'
        p2['packet_sha256'] = pipeline.digest(p2['packet'])
        packets.append(p2)
        mapping.append(dict(mapping[0], case_id='presentation-2', packet_sha256=p2['packet_sha256']))
        gold = [dict(case_id=m['case_id'], verdict='pass', reason='fixture', error_claim_ids=[]) for m in mapping]
        valid = [fake_outcome(p, 'pass') for p in packets]
        foreign = copy.deepcopy(valid)
        foreign[0]['packet_sha256'] = 'z' * 64
        for values in (valid[:1], valid + [valid[0]], list(reversed(valid)), foreign):
            with self.subTest(values=len(values)), self.assertRaises(ValueError):
                pipeline.measure(mapping, packets, values, gold)

    def test_rejection_of_correct_atom_is_not_credit_for_intended_error(self):
        raw, normal, reviewed = fixture()
        normal['rows'][0]['claims'].append(dict(normal['rows'][0]['claims'][0], id='c2'))
        reviewed['presentation-1']['claim_ids'].append('c2')
        packets, mapping = projection(raw, normal, reviewed)
        gold = [dict(case_id='presentation-1', verdict='fail', reason='c2 is wrong', error_claim_ids=['c2'])]
        result = pipeline.measure(mapping, packets, [fake_outcome(packets[0], 'fail', ['c1'])], gold)
        self.assertEqual(result['overall']['intended_errors_flagged'], 0)
        self.assertEqual(result['overall']['bad_fragments_rejected_only_on_other_claims'], ['presentation-1'])

    def test_prediction_cannot_change_anchor_or_drop_claim(self):
        packets, mapping = projection()
        gold = [dict(case_id='presentation-1', verdict='pass', reason='fixture', error_claim_ids=[])]
        for mutate in ('anchor', 'missing'):
            pred = fake_outcome(packets[0], 'pass')
            if mutate == 'anchor':
                pred['result']['claims'][0]['anchor'] = {'quote': 'fabricated'}
            else:
                pred['result']['claims'] = []
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                pipeline.measure(mapping, packets, [pred], gold)

    def test_malformed_claim_verdict_and_error_envelope_rejected(self):
        packets, mapping = projection()
        gold = [dict(case_id='presentation-1', verdict='pass', reason='fixture', error_claim_ids=[])]
        for mutate in ('claim_verdict', 'error_with_pass', 'empty_error'):
            pred = fake_outcome(packets[0], 'pass')
            if mutate == 'claim_verdict':
                pred['result']['claims'][0]['verdict'] = 'looks_good'
            else:
                pred['execution_error'] = 'worker crashed' if mutate == 'error_with_pass' else ''
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                pipeline.measure(mapping, packets, [pred], gold)

    def test_report_discloses_execution_errors_and_localization(self):
        packets, mapping = projection()
        gold = [dict(case_id='presentation-1', verdict='fail', reason='fixture', error_claim_ids=['c1'])]
        pred = fake_outcome(packets[0], 'invalid')
        pred['execution_error'] = 'fixture crash'
        measured = pipeline.measure(mapping, packets, [pred], gold)
        text = pipeline.report(measured, {"rows": []})
        self.assertIn('Execution errors: presentation-1.', text)
        self.assertIn('Intended faulty claims flagged: 0 / 1.', text)
        self.assertIn('Bad fragments rejected only for other claims: none.', text)

    def test_forged_fragment_pass_or_missing_explanation_is_rejected(self):
        packets, mapping = projection()
        gold = [dict(case_id='presentation-1', verdict='pass', reason='fixture', error_claim_ids=[])]
        for mutation in ('aggregate', 'explanation', 'finding', 'foreign_evidence'):
            pred = fake_outcome(packets[0], 'fail', ['c1'])
            if mutation == 'aggregate':
                pred['result']['verdict'] = 'pass'
            elif mutation == 'explanation':
                del pred['result']['claims'][0]['explanation']
            elif mutation == 'finding':
                pred['result']['findings'] = []
            else:
                pred['result']['claims'][0]['evidence_ids'] = ['foreign-source']
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                pipeline.measure(mapping, packets, [pred], gold)

    def test_returned_claim_order_is_bound(self):
        raw, normal, reviewed = fixture()
        normal['rows'][0]['claims'].append(dict(normal['rows'][0]['claims'][0], id='c2'))
        reviewed['presentation-1']['claim_ids'].append('c2')
        packets, mapping = projection(raw, normal, reviewed)
        pred = fake_outcome(packets[0], 'pass')
        pred['result']['claims'].reverse()
        gold = [dict(case_id='presentation-1', verdict='pass', reason='fixture', error_claim_ids=[])]
        with self.assertRaises(ValueError):
            pipeline.measure(mapping, packets, [pred], gold)


if __name__ == '__main__':
    unittest.main()
