#!/usr/bin/env python3
"""Audit, freeze and run one offline v4 regression without changing v3."""
import argparse
import copy
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from measurement import FAMILIES, VERDICTS, canonical, digest, require, unique, measure, metric_group

REPO = ROOT.parent.parent
BASELINE = ROOT.parent / 'career-quality-v3-new-cases'
INPUTS = tuple(folder + '/' + family + '.json'
               for folder in ('raw', 'normalized', 'gold') for family in FAMILIES)
BASE_SHA = 'e4b2699f543e4260128ebfabd61547c92b5c1dba3497acd07ca2f7007f225e33'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bound(path):
    return dict(sha256=sha(path), bytes=path.stat().st_size)


def write(path, obj):
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def read_lines(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def write_lines(path, rows):
    with path.open('x', encoding='utf-8') as stream:
        for row in rows:
            stream.write(canonical(row).decode('utf-8') + '\n')


def verify_predecessors():
    previous = read(ROOT / 'PREDECESSOR.json')
    for rel, expected in previous['files'].items():
        require(bound(REPO / rel) == expected, 'predecessor changed: ' + rel)
    require(sha(ROOT / 'v3_core.py') == BASE_SHA, 'copied v3 core changed')
    for folder in ('raw', 'gold'):
        for family in FAMILIES:
            rel = folder + '/' + family + '.json'
            require(bound(ROOT / rel) == bound(BASELINE / rel), 'original text/gold changed: ' + rel)
    return len(previous['files'])


def load_checker():
    spec = importlib.util.spec_from_file_location('v4_checker_shape_only', ROOT / 'checker.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def anchor(file_sha, pointer, full, quote):
    require(isinstance(quote, str) and quote and full.count(quote) == 1, 'quote must have one exact location')
    start = full.index(quote)
    return dict(sha256=file_sha, pointer=pointer, start=start, end=start + len(quote), quote=quote)


def project_family(raw, normal, raw_sha, reviewed):
    require(raw['family'] == normal['family'], 'family mismatch')
    require(raw['human_approved'] is False and normal['human_approved'] is False, 'unsupported human approval')
    rr = unique(raw['rows'], 'case_id', 'raw case')
    nn = unique(normal['rows'], 'case_id', 'normalized case')
    require(set(rr) == set(nn), 'missing/foreign normalized case')
    packets, mapping = [], []
    for i, r in enumerate(raw['rows']):
        cid = r['case_id']
        n = nn[cid]
        require(cid in reviewed, 'missing semantic review ' + cid)
        v = reviewed[cid]
        require(v['fragment_complete'] is True and v['source_inventory_complete'] is True,
                'incomplete semantic coverage ' + cid)
        ns = unique(n['sources'], 'id', 'normalized source')
        rs = unique(r['sources'], 'id', 'raw source')
        nc = unique(n['claims'], 'id', 'claim')
        require(set(rs) == set(ns), 'missing/foreign source')
        require(nc and set(v['claim_ids']) == set(nc) and len(v['claim_ids']) == len(nc), 'claim review mismatch')
        require(not set(rs) & set(nc), 'source/claim ID collision')
        sources = [dict(id=s['id'], kind=s['kind'], status=s['status'], observed_at=s['observed_at'],
                        anchor=anchor(raw_sha, '/rows/%d/sources/%d/text' % (i, j), s['text'], s['text']),
                        facts=copy.deepcopy(ns[s['id']]['facts'])) for j, s in enumerate(r['sources'])]
        claims = [dict(id=c['id'], stance=c['stance'], readings=copy.deepcopy(c['readings']),
                       check=copy.deepcopy(c['check']),
                       anchor=anchor(raw_sha, '/rows/%d/answer/text' % i, r['answer']['text'], c['quote']))
                  for c in n['claims']]
        packet = dict(schema='maguire-claim-packet-v4', grader=raw['family'].replace('-', '_'),
                      decision_at=r['decision_at'], sources=sources, claims=claims,
                      coverage=dict(scope='fragment', source_sha256=digest(sources), claims_sha256=digest(claims),
                                    status='agent_reviewed', source_inventory_complete=True, fragment_complete=True))
        h = digest(packet)
        packets.append(dict(packet_sha256=h, packet=packet))
        mapping.append(dict(case_id=cid, family=raw['family'], packet_sha256=h))
    return packets, mapping


def load_projection(review_rel):
    review = read(ROOT / review_rel)
    require(review['status'] == 'ready' and review['human_approved'] is False, 'semantic review not ready')
    require(set(INPUTS) <= set(review['files']), 'review does not bind six data files')
    for rel, expected in review['files'].items():
        require(bound(ROOT / rel) == expected, 'stale review: ' + rel)
    reviewed = unique(review['cases'], 'case_id', 'review case')
    checker = load_checker()
    packets, mapping, gold = [], [], []
    for family in FAMILIES:
        raw = read(ROOT / ('raw/' + family + '.json'))
        norm = read(ROOT / ('normalized/' + family + '.json'))
        old_norm = read(BASELINE / ('normalized/' + family + '.json'))
        old = unique(old_norm['rows'], 'case_id', 'old case')
        new = unique(norm['rows'], 'case_id', 'new case')
        require(set(new) == set(old) and len(new) == 20, 'cohort changed')
        for cid, row in new.items():
            require({c['id'] for c in row['claims']} == {c['id'] for c in old[cid]['claims']} and
                    len(row['claims']) == len(old[cid]['claims']), 'claim identities changed: ' + cid)
        p, m = project_family(raw, norm, sha(ROOT / ('raw/' + family + '.json')), reviewed)
        for item in p:
            checker.validate_packet(item['packet'])  # shape only, no prediction
        packets.extend(p)
        mapping.extend(m)
        g = read(ROOT / ('gold/' + family + '.json'))
        require(g['human_approved'] is False and g['family'] == family, 'gold provenance mismatch')
        gg = unique(g['rows'], 'case_id', 'gold case')
        require(set(gg) == set(new), 'gold cohort mismatch')
        for cid, row in gg.items():
            require(row['verdict'] in VERDICTS[:3] and bool(row['error_claim_ids']) == (row['verdict'] == 'fail'),
                    'invalid gold annotation')
            require(set(row['error_claim_ids']) <= {c['id'] for c in new[cid]['claims']}, 'foreign gold claim')
        gold.extend(g['rows'])
    require(set(reviewed) == {m['case_id'] for m in mapping}, 'extra review cases')
    require(len({p['packet_sha256'] for p in packets}) == len(packets), 'packet identity collapse')
    return packets, mapping, gold


def compare_baseline(measured):
    baseline = read(BASELINE / 'runs/new-cases-v3/measurement.json')
    old = unique(baseline['rows'], 'case_id', 'v3 result')
    require(set(old) == {r['case_id'] for r in measured['rows']}, 'v3 comparison cohort mismatch')
    changes = []
    for r in measured['rows']:
        b = old[r['case_id']]
        require(r['expected'] == b['expected'], 'gold verdict differs from v3')
        changes.append(dict(case_id=r['case_id'], family=r['family'], expected=r['expected'],
                            v3=b['actual'], v4=r['actual'],
                            v3_failed_claims=b['failed_claim_ids'], v4_failed_claims=r['failed_claim_ids']))
    return dict(schema='maguire-v3-v4-known-regression-comparison',
                baseline=bound(BASELINE / 'runs/new-cases-v3/measurement.json'),
                v3=baseline['overall'], v4=measured['overall'], rows=changes)


def report(m, comparison):
    lines = ['# v4 known-case regression', '',
             'Unchanged raw fragments and gold; revised manual normalization and checker. Not an independent holdout.', '',
             '| Family | Good: pass / fail / review / invalid | Bad: pass / fail / review / invalid | Ambiguous: pass / fail / review / invalid |',
             '|---|---|---|---|']
    for name, g in list(m['by_family'].items()) + [('all', m['overall'])]:
        cells = [' / '.join(str(g['confusion'][label][v]) for v in VERDICTS) for label in VERDICTS[:3]]
        lines.append('| ' + name + ' | ' + ' | '.join(cells) + ' |')
    o = m['overall']
    for label, key in [('Missed accepted errors', 'missed_errors'), ('False rejections', 'false_rejections'),
                       ('Ambiguous forced decisions', 'ambiguous_forced_decisions'), ('Invalid', 'invalid'),
                       ('Execution errors', 'execution_errors')]:
        lines.extend(['', label + ': ' + (', '.join(o[key]) or 'none') + '.'])
    lines.extend(['', 'Needs review by gold class:'])
    for g, ids in o['needs_review'].items():
        lines.append('- ' + g + ': ' + (', '.join(ids) or 'none'))
    lines.extend(['', 'Intended faulty claims flagged: %d / %d.' % (o['intended_errors_flagged'], o['intended_errors_total']),
                  'Bad fragments rejected only for other claims: ' + (', '.join(o['bad_fragments_rejected_only_on_other_claims']) or 'none') + '.',
                  'Additional failed claims in bad fragments: ' + (json.dumps(o['extra_failures_in_bad_fragments']) if o['extra_failures_in_bad_fragments'] else 'none') + '.',
                  '', '| Case | Gold | v3 | v4 | Failed claims v4 |', '|---|---|---|---|---|'])
    for r in comparison['rows']:
        lines.append('| ' + ' | '.join([r['case_id'], r['expected'], r['v3'], r['v4'], ', '.join(r['v4_failed_claims']) or '—']) + ' |')
    lines.extend(['', 'All denominators retained. Review is neither acceptance nor detection. Localization does not prove causal explanation.',
                  'Agent manual normalization/review only; human_approved=false. Old v3 was not rerun or changed.', ''])
    return '\n'.join(lines)


def freeze(review_rel, challenge_rel):
    previous = verify_predecessors()
    packets, mapping, _ = load_projection(review_rel)
    challenge = read(ROOT / challenge_rel)
    require(challenge['status'] == 'ready' and challenge['human_approved'] is False, 'challenge not ready')
    require({'checker.py', 'v3_core.py', 'grade_packets.py', 'pipeline.py', 'measurement.py', 'SCHEMA.md',
             'CONTRACT.md', review_rel, 'tests/test_checker.py', 'tests/test_pipeline.py'} <= set(challenge['files']),
            'challenge coverage incomplete')
    for rel, expected in challenge['files'].items():
        require(bound(ROOT / rel) == expected, 'stale challenge: ' + rel)
    files = {str(p.relative_to(ROOT)): bound(p) for p in sorted(ROOT.rglob('*')) if p.is_file()
             and '__pycache__' not in p.parts and 'runs' not in p.relative_to(ROOT).parts and p.name != 'FREEZE.json'}
    write(ROOT / 'FREEZE.json', dict(schema='maguire-v4-freeze', created_at=datetime.now(timezone.utc).isoformat(),
                                   human_approved=False, evaluation='known_case_regression', files=files,
                                   review=review_rel, challenge=challenge_rel, predecessor_files=previous,
                                   mapping=mapping, packet_sha256s=[p['packet_sha256'] for p in packets]))
    return dict(frozen=len(packets), claims=sum(len(p['packet']['claims']) for p in packets), predecessor_files=previous)


def verify_freeze():
    count = verify_predecessors()
    f = read(ROOT / 'FREEZE.json')
    for rel, expected in f['files'].items():
        require(bound(ROOT / rel) == expected, 'frozen file changed: ' + rel)
    packets, mapping, gold = load_projection(f['review'])
    require(mapping == f['mapping'] and [p['packet_sha256'] for p in packets] == f['packet_sha256s'], 'projection changed')
    return packets, mapping, gold, count


def run(output):
    packets, mapping, _, count = verify_freeze()
    output.mkdir(parents=True, exist_ok=False)
    write_lines(output / 'packets.jsonl', packets)
    write(output / 'mapping.json', mapping)
    command = [sys.executable, '-B', str(ROOT / 'grade_packets.py'), '--packets', str(output / 'packets.jsonl'),
               '--predictions', str(output / 'predictions.jsonl')]
    start = dict(command=command, started_at=datetime.now(timezone.utc).isoformat(), freeze=bound(ROOT / 'FREEZE.json'),
                 output=str(output.relative_to(ROOT)), packet_sha256s=[p['packet_sha256'] for p in packets])
    write(ROOT / 'START.json', start)
    try:
        proc = subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True, timeout=60,
                              env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
        execution = dict(command=command, returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)
    except subprocess.TimeoutExpired as exc:
        write(output / 'execution.json', dict(command=command, timeout=True, stdout=str(exc.stdout), stderr=str(exc.stderr)))
        raise
    write(output / 'execution.json', execution)
    require(proc.returncode == 0, 'worker failed; outputs preserved, no retry in place')
    predictions = read_lines(output / 'predictions.jsonl')
    # Worker has completed and prediction bytes exist before the measurement opens gold.
    gold = [r for family in FAMILIES for r in read(ROOT / ('gold/' + family + '.json'))['rows']]
    measurement = measure(mapping, packets, predictions, gold)
    comparison = compare_baseline(measurement)
    write(output / 'measurement.json', measurement)
    write(output / 'comparison.json', comparison)
    with (output / 'REPORT.md').open('x', encoding='utf-8') as stream:
        stream.write(report(measurement, comparison))
    verify_freeze()
    write(output / 'RECEIPT.json', dict(schema='maguire-v4-run-receipt', completed_at=datetime.now(timezone.utc).isoformat(),
                                      freeze=bound(ROOT / 'FREEZE.json'), start=bound(ROOT / 'START.json'),
                                      predecessor_files=count,
                                      artifacts={p.name: bound(p) for p in sorted(output.iterdir()) if p.is_file()}))
    return measurement['overall']


def verify(output):
    packets, mapping, gold, count = verify_freeze()
    receipt = read(output / 'RECEIPT.json')
    require(receipt['freeze'] == bound(ROOT / 'FREEZE.json') and receipt['start'] == bound(ROOT / 'START.json'), 'run context drift')
    start = read(ROOT / 'START.json')
    require(start['freeze'] == receipt['freeze'] and start['output'] == str(output.relative_to(ROOT)) and
            start['packet_sha256s'] == [p['packet_sha256'] for p in packets], 'start binding mismatch')
    require(set(receipt['artifacts']) == {'packets.jsonl', 'mapping.json', 'execution.json', 'predictions.jsonl',
                                        'measurement.json', 'comparison.json', 'REPORT.md'}, 'run artifact inventory differs')
    for rel, expected in receipt['artifacts'].items():
        require(bound(output / rel) == expected, 'run artifact drift: ' + rel)
    require(read_lines(output / 'packets.jsonl') == packets and read(output / 'mapping.json') == mapping, 'saved projection drift')
    m = measure(mapping, packets, read_lines(output / 'predictions.jsonl'), gold)
    c = compare_baseline(m)
    require(read(output / 'measurement.json') == m and read(output / 'comparison.json') == c, 'accounting drift')
    require((output / 'REPORT.md').read_text(encoding='utf-8') == report(m, c), 'report drift')
    return dict(verified=len(packets), predecessor_files=count, reran_checker=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('audit', 'freeze', 'run', 'verify'))
    parser.add_argument('--review', default='review/annotation_review_v1.json')
    parser.add_argument('--challenge', default='review/challenge_packet_v1.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'runs/v4-regression')
    args = parser.parse_args()
    if args.action == 'audit':
        count = verify_predecessors()
        packets, _, _ = load_projection(args.review)
        value = dict(packets=len(packets), claims=sum(len(p['packet']['claims']) for p in packets),
                     predecessor_files=count, predictions_executed=False)
    elif args.action == 'freeze':
        value = freeze(args.review, args.challenge)
    else:
        output = args.output.resolve()
        require(ROOT / 'runs' in output.parents, 'output outside this experiment runs/')
        value = run(output) if args.action == 'run' else verify(output)
    print(json.dumps(value, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
