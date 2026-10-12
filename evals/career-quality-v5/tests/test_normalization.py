"""Audit authoring boundaries without grading the 40-case corpus."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('v5_migration', ROOT / 'migrate_annotations.py')
migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration)


def read(path):
    return json.loads(path.read_text())


class NormalizationTests(unittest.TestCase):
    def test_serialized_annotations_match_authoring_and_exact_allowed_delta(self):
        changed = []
        for family in migration.FAMILIES:
            old = read(ROOT.parent / 'career-quality-v4' / 'normalized' / (family + '.json'))
            new = read(ROOT / 'normalized' / (family + '.json'))
            self.assertEqual(new, migration.build(family))
            self.assertFalse(new['human_approved'])
            # The allowed semantic delta is narrow. All other bytes-as-values,
            # including claim identities, readings, source roles and refs survive.
            expected = copy.deepcopy(old['rows'])
            for row in expected:
                for prop in migration.propositions(row):
                    if prop['measure'] and prop['measure']['unit'] == 'days':
                        prop['measure']['unit'] = 'day'
                        changed.append((row['case_id'], 'unit'))
                if row['case_id'] == 'PF3N-09':
                    source = next(s for s in row['sources'] if s['id'] == 'J09')
                    source['facts'][0]['scope'] = {'status': 'available_now'}
                    changed.append((row['case_id'], 'current_status'))
            self.assertEqual(new['rows'], expected)
        self.assertEqual(changed.count(('CF3N-08', 'unit')), 4)
        self.assertEqual(changed.count(('PF3N-06', 'unit')), 2)
        self.assertEqual(changed.count(('PF3N-09', 'current_status')), 1)
        self.assertEqual(len(changed), 7)

    def test_current_unavailability_does_not_deny_pending_or_promise_availability(self):
        doc = read(ROOT / 'normalized/preference-fit.json')
        row = next(r for r in doc['rows'] if r['case_id'] == 'PF3N-09')
        source = next(s for s in row['sources'] if s['id'] == 'J09')
        current, future = source['facts']
        self.assertEqual((current['polarity'], current['modality'], current['scope']),
                         ('negative', 'observation', {'status': 'available_now'}))
        self.assertEqual((future['polarity'], future['modality'], future['scope']),
                         ('positive', 'observation', {'status': 'pending', 'reason': 'procurement'}))
        self.assertEqual(row['claims'][1]['stance'], 'advice')
        self.assertEqual(row['claims'][1]['check']['offer']['fact_index'], 1)

    def test_day_alias_keeps_count_frequency_period_and_historical_time(self):
        cf = read(ROOT / 'normalized/candidate-fit.json')
        pf = read(ROOT / 'normalized/preference-fit.json')
        historical = next(r for r in cf['rows'] if r['case_id'] == 'CF3N-08')
        onboarding = next(r for r in pf['rows'] if r['case_id'] == 'PF3N-06')
        for prop in migration.propositions(historical):
            if prop['measure'] and prop['measure']['unit'] == 'day':
                self.assertEqual((prop['measure']['kind'], prop['measure']['per']), ('frequency', 'week'))
        for source in onboarding['sources']:
            for prop in source['facts']:
                if prop['measure']:
                    self.assertEqual((prop['measure']['kind'], prop['measure']['unit'], prop['measure']['per']),
                                     ('count', 'day', None))
                    self.assertEqual(prop['time'], {'phase': 'onboarding'})
        old = read(ROOT.parent / 'career-quality-v4/normalized/candidate-fit.json')
        before = next(r for r in old['rows'] if r['case_id'] == 'CF3N-08')
        self.assertEqual([p['time'] for p in migration.propositions(historical)],
                         [p['time'] for p in migration.propositions(before)])

    def test_raw_and_gold_unchanged_and_no_frozen_annotation_overwrite(self):
        for folder in ('raw', 'gold'):
            for family in migration.FAMILIES:
                rel = Path(folder) / (family + '.json')
                self.assertEqual((ROOT / rel).read_bytes(), (ROOT.parent / 'career-quality-v4' / rel).read_bytes())
        for marker in ('FREEZE.json', 'START.json'):
            with tempfile.TemporaryDirectory() as tmp:
                local = Path(tmp)
                (local / marker).write_text('{}')
                with patch.object(migration, 'HERE', local), patch.object(migration, 'build') as build:
                    with self.assertRaises(RuntimeError):
                        migration.main()
                    build.assert_not_called()
                self.assertFalse((local / 'normalized').exists())


if __name__ == '__main__':
    unittest.main()
