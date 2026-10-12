#!/usr/bin/env python3
"""One offline challenge run against unchanged v3; no text extraction or tuning."""
import argparse
import copy
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
RUNTIME = ROOT.parent / 'career-quality-v3'
FAMILIES = ('candidate-fit', 'preference-fit')
INPUTS = tuple(folder + '/' + family + '.json'
               for folder in ('raw', 'normalized', 'gold') for family in FAMILIES)
CHECKER_SHA = 'e4b2699f543e4260128ebfabd61547c92b5c1dba3497acd07ca2f7007f225e33'
WORKER_SHA = 'ca85f0de76a431b6b2d18eb71a8a59dc1ff7c15c425a704f1079742aff4c1665'
VERDICTS = ('pass', 'fail', 'needs_review', 'invalid')


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def write_lines(path, rows):
    with path.open('x', encoding='utf-8') as stream:
        for row in rows:
            stream.write(canonical(row).decode('utf-8') + '\n')


def read_lines(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def unique(rows, field, label):
    result = {r[field]: r for r in rows}
    require(len(result) == len(rows), 'duplicate ' + label)
    return result


def verify_predecessors():
    predecessor = read(ROOT / 'PREDECESSOR.json')
    for rel, expected in predecessor['files'].items():
        path = REPO / rel
        require(sha(path) == expected['sha256'] and path.stat().st_size == expected['bytes'],
                'predecessor changed: ' + rel)
    require(sha(RUNTIME / 'checker.py') == CHECKER_SHA, 'checker drift')
    require(sha(RUNTIME / 'grade_packets.py') == WORKER_SHA, 'worker drift')
    return len(predecessor['files'])


def structural_checker():
    # Only private schema validators are called before freeze; never grade/check_claim.
    require(sha(RUNTIME / 'checker.py') == CHECKER_SHA, 'checker drift')
    spec = importlib.util.spec_from_file_location('frozen_v3_shape_only', RUNTIME / 'checker.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def anchor(file_sha, pointer, full_text, quote):
    require(isinstance(quote, str) and quote and full_text.count(quote) == 1,
            'quote must occur exactly once in its own raw string')
    start = full_text.index(quote)
    return dict(sha256=file_sha, pointer=pointer, start=start, end=start + len(quote), quote=quote)


def project_family(raw, normal, raw_sha, reviewed):
    """No gold argument. Raw and annotation rows are joined by identity, never position."""
    require(raw['family'] == normal['family'], 'family mismatch')
    require(raw['human_approved'] is False and normal['human_approved'] is False,
            'unsupported human approval claim')
    raw_by_id = unique(raw['rows'], 'case_id', 'raw case')
    norm_by_id = unique(normal['rows'], 'case_id', 'normalized case')
    require(set(raw_by_id) == set(norm_by_id), 'missing/foreign normalized case')
    packets, mapping = [], []
    for index, row in enumerate(raw['rows']):
        cid = row['case_id']
        norm = norm_by_id[cid]
        require(cid in reviewed, 'unreviewed case ' + cid)
        review = reviewed[cid]
        require(review['source_inventory_complete'] is True and review['fragment_complete'] is True,
                'incomplete semantic coverage ' + cid)
        rs = unique(row['sources'], 'id', 'source')
        ns = unique(norm['sources'], 'id', 'normalized source')
        require(set(rs) == set(ns), 'source inventory mismatch ' + cid)
        nc = unique(norm['claims'], 'id', 'claim')
        require(nc and set(review['claim_ids']) == set(nc) and
                len(review['claim_ids']) == len(nc), 'review claim coverage mismatch ' + cid)
        require(not set(rs).intersection(nc), 'source/claim ID collision')
        sources, claims = [], []
        for si, source in enumerate(row['sources']):
            sources.append(dict(id=source['id'], kind=source['kind'], status=source['status'],
                                observed_at=source['observed_at'], facts=copy.deepcopy(ns[source['id']]['facts']),
                                anchor=anchor(raw_sha, '/rows/%d/sources/%d/text' % (index, si),
                                              source['text'], source['text'])))
        for claim in norm['claims']:
            claims.append(dict(id=claim['id'], stance=claim['stance'],
                               readings=copy.deepcopy(claim['readings']),
                               anchor=anchor(raw_sha, '/rows/%d/answer/text' % index,
                                             row['answer']['text'], claim['quote'])))
        packet = dict(schema='maguire-claim-packet-v3', grader=raw['family'].replace('-', '_'),
                      decision_at=row['decision_at'], sources=sources, claims=claims,
                      coverage=dict(scope='fragment', source_sha256=digest(sources),
                                    claims_sha256=digest(claims), status='agent_reviewed',
                                    source_inventory_complete=True, fragment_complete=True))
        packet_sha = digest(packet)
        packets.append(dict(packet_sha256=packet_sha, packet=packet))
        mapping.append(dict(case_id=cid, family=raw['family'], packet_sha256=packet_sha))
    return packets, mapping


def load_projection(review_rel):
    review = read(ROOT / review_rel)
    require(review['status'] == 'ready' and review['human_approved'] is False,
            'annotation review not ready')
    require(set(review['files']) == set(INPUTS), 'review must bind exactly six inputs')
    for rel, h in review['files'].items():
        require(sha(ROOT / rel) == h, 'stale annotation review: ' + rel)
    raw_review_path = ROOT / 'review/raw_judgments_v1.json'
    require(review['raw_judgments_sha256'] == sha(raw_review_path), 'raw judgment receipt drift')
    raw_review = read(raw_review_path)
    require(raw_review['human_approved'] is False, 'unsupported human review')
    require(set(raw_review['raw_files']) == {'raw/' + f + '.json' for f in FAMILIES},
            'raw review input inventory mismatch')
    for rel, h in raw_review['raw_files'].items():
        require(sha(ROOT / rel) == h, 'raw text changed after independent judgment')
    raw_judgments = unique(raw_review['judgments'], 'case_id', 'raw review case')
    reviewed = unique(review['cases'], 'case_id', 'review case')
    checker = structural_checker()
    packets, mapping, gold_rows = [], [], []
    for family in FAMILIES:
        raw = read(ROOT / ('raw/' + family + '.json'))
        norm = read(ROOT / ('normalized/' + family + '.json'))
        gold = read(ROOT / ('gold/' + family + '.json'))
        prefix = 'CF3N' if family == 'candidate-fit' else 'PF3N'
        require({r['case_id'] for r in raw['rows']} == {prefix + '-%02d' % n for n in range(1, 21)}
                and len(raw['rows']) == 20, 'cohort changed: ' + family)
        require(gold['family'] == family and gold['human_approved'] is False, 'gold provenance invalid')
        g = unique(gold['rows'], 'case_id', 'gold case')
        n = unique(norm['rows'], 'case_id', 'normalized case')
        require(set(g) == set(n), 'gold cohort mismatch')
        for cid, row in g.items():
            require(row['verdict'] in VERDICTS[:3], 'invalid gold verdict')
            require(bool(row['error_claim_ids']) == (row['verdict'] == 'fail'), 'invalid error annotation')
            require(set(row['error_claim_ids']) <= {c['id'] for c in n[cid]['claims']},
                    'foreign error claim')
        p, m = project_family(raw, norm, sha(ROOT / ('raw/' + family + '.json')), reviewed)
        for item in p:
            packet = item['packet']
            checker._timestamp(packet['decision_at'], 'decision_at')
            checker._validate_sources_claims(packet['sources'], packet['claims'])
            checker._coverage(packet['coverage'])
        packets.extend(p)
        mapping.extend(m)
        gold_rows.extend(gold['rows'])
    require(set(reviewed) == {m['case_id'] for m in mapping}, 'extra review cases')
    require(set(raw_judgments) == set(reviewed), 'raw judgment coverage mismatch')
    require(len({p['packet_sha256'] for p in packets}) == len(packets), 'packet identity collapse')
    return packets, mapping, gold_rows


def all_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from all_strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from all_strings(nested)


def duplicate_audit():
    prior = {}
    for folder in ('career-quality-v1', 'career-quality-v2'):
        for path in (ROOT.parent / folder).rglob('answers.json'):
            for text in all_strings(read(path)):
                prior.setdefault(text, []).append(str(path.relative_to(REPO)))
    design = read(ROOT.parent / 'career-quality-v3-design/CLAIM_TRACES.json')
    for example in design['examples']:
        prior.setdefault(example['answer_anchor']['quote'], []).append('design:' + example['example_id'])
    seen, matches, within = {}, [], []
    for family in FAMILIES:
        for row in read(ROOT / ('raw/' + family + '.json'))['rows']:
            text, cid = row['answer']['text'], row['case_id']
            if text in prior:
                matches.append(dict(case_id=cid, prior=prior[text]))
            if text in seen:
                within.append([seen[text], cid])
            seen[text] = cid
    return dict(exact_prior_matches=matches, exact_within_matches=within,
                method='Whole new fragment equality against prior answer JSON strings and design selected spans; no semantic independence claim.')


def metric_group(rows):
    matrix = {g: {v: 0 for v in VERDICTS} for g in VERDICTS[:3]}
    for r in rows:
        matrix[r['expected']][r['actual']] += 1
    def ids(expected, actual):
        return [r['case_id'] for r in rows if r['expected'] == expected and r['actual'] == actual]
    return dict(total=len(rows), confusion=matrix,
                missed_errors=ids('fail', 'pass'), false_rejections=ids('pass', 'fail'),
                needs_review={g: ids(g, 'needs_review') for g in VERDICTS[:3]},
                ambiguous_forced_decisions=[r['case_id'] for r in rows if r['expected'] == 'needs_review' and r['actual'] in ('pass', 'fail')],
                invalid=[r['case_id'] for r in rows if r['actual'] == 'invalid'],
                execution_errors=[r['case_id'] for r in rows if r['execution_error']],
                automatic_decisions=sum(r['actual'] in ('pass', 'fail') for r in rows),
                intended_errors_total=sum(len(r['intended_error_claim_ids']) for r in rows),
                intended_errors_flagged=sum(len(r['localized_error_claim_ids']) for r in rows),
                bad_fragments_rejected_only_on_other_claims=[r['case_id'] for r in rows if r['expected'] == 'fail' and r['actual'] == 'fail' and not r['localized_error_claim_ids']],
                extra_failures_in_bad_fragments=[dict(case_id=r['case_id'], claim_ids=r['other_failed_claim_ids']) for r in rows if r['expected'] == 'fail' and r['other_failed_claim_ids']])


def measure(mapping, packets, predictions, gold_rows):
    wanted = [m['packet_sha256'] for m in mapping]
    require(len(set(wanted)) == len(wanted), 'duplicate mapping packet')
    require([p['packet_sha256'] for p in packets] == wanted, 'packet/mapping mismatch')
    require([p['packet_sha256'] for p in predictions] == wanted,
            'omitted/foreign/duplicate/reordered prediction')
    gold = unique(gold_rows, 'case_id', 'gold case')
    require(set(gold) == {m['case_id'] for m in mapping} and len(gold) == len(mapping), 'gold/mapping mismatch')
    rows = []
    for m, p, prediction in zip(mapping, packets, predictions):
        require(digest(p['packet']) == p['packet_sha256'], 'packet hash mismatch')
        result = prediction['result']
        require(result['verdict'] in VERDICTS, 'unrecognized runtime verdict')
        require(prediction['execution_error'] is None or
                (isinstance(prediction['execution_error'], str) and prediction['execution_error'] and
                 result['verdict'] == 'invalid'), 'execution error must be a nonempty message and invalid verdict')
        returned = unique(result['claims'], 'id', 'returned claim')
        wanted_claims = {c['id']: c for c in p['packet']['claims']}
        require(set(returned) <= set(wanted_claims), 'foreign runtime claim')
        if result['verdict'] != 'invalid':
            require(set(returned) == set(wanted_claims), 'runtime omitted claim')
        for cid, value in returned.items():
            require(value['anchor'] == wanted_claims[cid]['anchor'], 'runtime anchor drift')
            require(value['verdict'] in VERDICTS, 'unrecognized claim verdict')
        g = gold[m['case_id']]
        intended = set(g['error_claim_ids'])
        failed = {c['id'] for c in result['claims'] if c['verdict'] == 'fail'}
        rows.append(dict(case_id=m['case_id'], family=m['family'], packet_sha256=m['packet_sha256'],
                         expected=g['verdict'], actual=result['verdict'], reference_reason=g['reason'],
                         intended_error_claim_ids=sorted(intended), failed_claim_ids=sorted(failed),
                         localized_error_claim_ids=sorted(intended & failed),
                         other_failed_claim_ids=sorted(failed - intended),
                         review_claim_ids=[c['id'] for c in result['claims'] if c['verdict'] == 'needs_review'],
                         execution_error=prediction['execution_error'], claims=result['claims'],
                         review_reasons=result['review_reasons']))
    return dict(schema='maguire-frozen-v3-new-cases-measurement', human_approved=False,
                scope='manually normalized fragments; no extractor or complete-advice assessment',
                overall=metric_group(rows), by_family={f: metric_group([r for r in rows if r['family'] == f]) for f in FAMILIES},
                rows=rows)


def report(measurement):
    lines = ['# Frozen v3: new challenge fragments', '',
             'Manual agent authoring and review; human_approved=false. Gold was frozen before predictions.', '',
             '| Family | Good → pass / fail / review / invalid | Bad → pass / fail / review / invalid | Ambiguous → pass / fail / review / invalid |',
             '|---|---|---|---|']
    for family, group in list(measurement['by_family'].items()) + [('overall', measurement['overall'])]:
        cells = [' / '.join(str(group['confusion'][g][v]) for v in VERDICTS) for g in VERDICTS[:3]]
        lines.append('| ' + family + ' | ' + ' | '.join(cells) + ' |')
    for label, key in [('Missed accepted errors', 'missed_errors'), ('False rejections', 'false_rejections'),
                       ('Ambiguous forced decisions', 'ambiguous_forced_decisions'), ('Invalid', 'invalid'),
                       ('Execution errors', 'execution_errors')]:
        lines.extend(['', label + ': ' + (', '.join(measurement['overall'][key]) or 'none') + '.'])
    overall = measurement['overall']
    lines.extend(['', 'Intended faulty claims flagged: %d / %d.' %
                  (overall['intended_errors_flagged'], overall['intended_errors_total']),
                  'Bad fragments rejected only on other claims: ' +
                  (', '.join(overall['bad_fragments_rejected_only_on_other_claims']) or 'none') + '.',
                  'Additional failures on non-faulty claims inside bad fragments: ' +
                  ('; '.join(r['case_id'] + ': ' + ', '.join(r['claim_ids']) for r in overall['extra_failures_in_bad_fragments']) or 'none') + '.'])
    lines.extend(['', 'Needs review by gold class:'])
    for label, ids in measurement['overall']['needs_review'].items():
        lines.append('- ' + label + ': ' + (', '.join(ids) or 'none'))
    lines.extend(['', 'All individual decisions (full evidence traces in measurement.json):', '',
                  '| Case | Gold | Actual | Intended bad claims | Failed claims | Review claims |', '|---|---|---|---|---|---|'])
    for r in measurement['rows']:
        lines.append('| ' + ' | '.join([r['case_id'], r['expected'], r['actual'],
                     ', '.join(r['intended_error_claim_ids']) or '—', ', '.join(r['failed_claim_ids']) or '—',
                     ', '.join(r['review_claim_ids']) or '—']) + ' |')
    lines.extend(['', 'Abstention is not detection or acceptance. Claim localization is separate from the correctness of an explanation.',
                  'The authors did not inspect runtime; separation was procedural in a shared filesystem, not an externally independent holdout.', ''])
    return '\n'.join(lines)


def freeze(review_rel, challenge_rel):
    count = verify_predecessors()
    packets, mapping, gold = load_projection(review_rel)
    challenge = read(ROOT / challenge_rel)
    require(challenge['status'] == 'ready' and challenge['human_approved'] is False, 'preflight not ready')
    required = {'pipeline.py', 'tests/test_pipeline.py', 'CONTRACT.md', review_rel}
    require(required <= set(challenge['files']), 'preflight does not bind implementation and review')
    for rel, h in challenge['files'].items():
        require(sha(ROOT / rel) == h, 'stale preflight: ' + rel)
    files = {}
    for path in sorted(ROOT.rglob('*')):
        rel = str(path.relative_to(ROOT))
        if path.is_file() and not rel.startswith(('runs/', '__pycache__/', 'tests/__pycache__/')) and rel != 'FREEZE.json':
            files[rel] = sha(path)
    result = dict(schema='maguire-frozen-v3-new-cases-freeze', created_at=datetime.now(timezone.utc).isoformat(),
                  human_approved=False, review=review_rel, challenge=challenge_rel, files=files,
                  file_bytes={rel: (ROOT / rel).stat().st_size for rel in files},
                  predecessor_files=count, runtime={'checker.py': CHECKER_SHA, 'grade_packets.py': WORKER_SHA},
                  cohort=[dict(m, expected=g['verdict']) for m, g in zip(mapping, gold)],
                  packet_sha256s=[p['packet_sha256'] for p in packets], duplicate_audit=duplicate_audit())
    # Do not rely on gold row order, including in the human-facing manifest.
    gb = {g['case_id']: g for g in gold}
    result['cohort'] = [dict(m, expected=gb[m['case_id']]['verdict']) for m in mapping]
    write(ROOT / 'FREEZE.json', result)
    return dict(frozen=len(packets), claims=sum(len(p['packet']['claims']) for p in packets),
                predecessor_files=count, duplicate_audit=result['duplicate_audit'])


def verify_freeze():
    count = verify_predecessors()
    manifest = read(ROOT / 'FREEZE.json')
    for rel, h in manifest['files'].items():
        require(sha(ROOT / rel) == h and (ROOT / rel).stat().st_size == manifest['file_bytes'][rel],
                'frozen input changed: ' + rel)
    packets, mapping, gold = load_projection(manifest['review'])
    require([p['packet_sha256'] for p in packets] == manifest['packet_sha256s'], 'projection changed')
    return packets, mapping, gold, count


def run(output):
    packets, mapping, _, count = verify_freeze()
    output.mkdir(parents=True, exist_ok=False)
    write_lines(output / 'packets.jsonl', packets)
    write(output / 'mapping.json', mapping)
    command = [sys.executable, '-B', str(RUNTIME / 'grade_packets.py'), '--packets', str(output / 'packets.jsonl'),
               '--predictions', str(output / 'predictions.jsonl')]
    execution = dict(command=command, started_at=datetime.now(timezone.utc).isoformat(),
                     runtime_sha256=WORKER_SHA, checker_sha256=CHECKER_SHA)
    # Exclusive marker enforces the contract's one measured start, even under a different output path.
    write(ROOT / 'START.json', dict(execution, freeze_sha256=sha(ROOT / 'FREEZE.json'),
                                  freeze_bytes=(ROOT / 'FREEZE.json').stat().st_size,
                                  output=str(output.relative_to(ROOT)),
                                  packet_sha256s=[p['packet_sha256'] for p in packets]))
    try:
        proc = subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True, timeout=60,
                              env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
        execution.update(returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)
    except subprocess.TimeoutExpired as exc:
        execution.update(returncode=None, timeout=True, stdout=str(exc.stdout), stderr=str(exc.stderr))
        write(output / 'execution.json', execution)
        raise
    write(output / 'execution.json', execution)
    require(proc.returncode == 0, 'worker failed; preserved output, no retry in place')
    # Prediction bytes now exist. Only the measurement process opens authored gold.
    predictions = read_lines(output / 'predictions.jsonl')
    gold = [row for f in FAMILIES for row in read(ROOT / ('gold/' + f + '.json'))['rows']]
    measurement = measure(mapping, packets, predictions, gold)
    write(output / 'measurement.json', measurement)
    with (output / 'REPORT.md').open('x', encoding='utf-8') as stream:
        stream.write(report(measurement))
    verify_freeze()
    receipt = dict(schema='maguire-frozen-v3-new-cases-run', completed_at=datetime.now(timezone.utc).isoformat(),
                   freeze_sha256=sha(ROOT / 'FREEZE.json'), predecessor_files=count,
                   freeze_bytes=(ROOT / 'FREEZE.json').stat().st_size,
                   start_sha256=sha(ROOT / 'START.json'), start_bytes=(ROOT / 'START.json').stat().st_size,
                   artifacts={p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()},
                   artifact_bytes={p.name: p.stat().st_size for p in sorted(output.iterdir()) if p.is_file()})
    write(output / 'RECEIPT.json', receipt)
    return measurement['overall']


def verify(output):
    packets, mapping, gold, count = verify_freeze()
    receipt = read(output / 'RECEIPT.json')
    require(receipt['freeze_sha256'] == sha(ROOT / 'FREEZE.json') and
            receipt['freeze_bytes'] == (ROOT / 'FREEZE.json').stat().st_size, 'run freeze drift')
    require(receipt['start_sha256'] == sha(ROOT / 'START.json') and
            receipt['start_bytes'] == (ROOT / 'START.json').stat().st_size, 'start receipt drift')
    start = read(ROOT / 'START.json')
    require(start['freeze_sha256'] == receipt['freeze_sha256'] and start['output'] == str(output.relative_to(ROOT))
            and start['packet_sha256s'] == [p['packet_sha256'] for p in packets], 'start belongs to different run')
    require(set(receipt['artifacts']) == {'packets.jsonl', 'mapping.json', 'predictions.jsonl',
                                        'execution.json', 'measurement.json', 'REPORT.md'}, 'run artifact inventory differs')
    for rel, h in receipt['artifacts'].items():
        require(sha(output / rel) == h and (output / rel).stat().st_size == receipt['artifact_bytes'][rel],
                'run artifact changed: ' + rel)
    require(read_lines(output / 'packets.jsonl') == packets and read(output / 'mapping.json') == mapping,
            'saved projection differs')
    measurement = measure(mapping, packets, read_lines(output / 'predictions.jsonl'), gold)
    require(read(output / 'measurement.json') == measurement, 'measurement drift')
    require((output / 'REPORT.md').read_text(encoding='utf-8') == report(measurement), 'report drift')
    return dict(verified=len(packets), predecessor_files=count, reran_checker=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('audit', 'freeze', 'run', 'verify'))
    parser.add_argument('--review', default='review/annotation_review_v1.json')
    parser.add_argument('--challenge', default='review/challenge_packet_v1.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'runs/new-cases-v3')
    args = parser.parse_args()
    if args.action == 'audit':
        count = verify_predecessors()
        packets, _, gold = load_projection(args.review)
        result = dict(packets=len(packets), claims=sum(len(p['packet']['claims']) for p in packets),
                      gold_counts=dict(Counter(g['verdict'] for g in gold)), predecessor_files=count,
                      duplicate_audit=duplicate_audit(), predictions_executed=False)
    elif args.action == 'freeze':
        result = freeze(args.review, args.challenge)
    else:
        output = args.output.resolve()
        require(ROOT / 'runs' in output.parents, 'output must be inside this experiment runs/')
        result = run(output) if args.action == 'run' else verify(output)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
