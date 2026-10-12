#!/usr/bin/env python3
"""Freeze, execute and verify the local, known 16-fragment v3 regression."""
import argparse
import copy
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
DESIGN = ROOT.parent / 'career-quality-v3-design' / 'CLAIM_TRACES.json'


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bound(path):
    return dict(sha256=sha(path), bytes=path.stat().st_size)


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    with path.open('x') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def pointer(value, path):
    for key in path.lstrip('/').split('/'):
        key = key.replace('~1', '/').replace('~0', '~')
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def verify_predecessor():
    previous = read(ROOT / 'PREDECESSOR.json')
    repo = ROOT.parent.parent
    for path, expected in previous['files'].items():
        if sha(repo / path) != expected:
            raise ValueError('predecessor changed: ' + path)
    return len(previous['files'])


def validate_data(review_path):
    """Read authored data and review, not outcome expectations."""
    normal = read(ROOT / 'data/normalizations.json')
    lineage = read(ROOT / 'data/source_files.json')['files_by_sha256']
    design = read(DESIGN)
    if normal['design_sha256'] != sha(DESIGN) or normal['human_approved'] is not False:
        raise ValueError('invalid design/review lineage')
    review = read(review_path)
    if review['status'] != 'ready' or review['human_approved'] is not False:
        raise ValueError('normalization review is not ready')
    if (review['schema'] != 'maguire-v3-normalization-review-v2' or
            review['reviewer']['identity'] != 'agent:/root/v3_slice_review' or
            review['reviewer']['role'] != 'agent_semantic_reviewer'):
        raise ValueError('unrecognized review record (local identity, not authenticated signature)')
    if review['predecessor_review_sha256'] != sha(ROOT / 'review/normalization_review_v1.json'):
        raise ValueError('review predecessor changed')
    for name in ('normalizations.json', 'expectations.json', 'source_files.json'):
        rel = 'data/' + name
        if review['bindings'][rel] != sha(ROOT / rel):
            raise ValueError('stale normalization review: ' + rel)
    ids = [r['example_id'] for r in normal['rows']]
    if len(ids) != len(set(ids)) or len(ids) != 16:
        raise ValueError('missing/duplicate development examples')
    if set(ids) != set(review['reviewed_example_ids']) or len(review['reviewed_example_ids']) != 16:
        raise ValueError('review coverage does not match examples')
    design_by_id = {x['example_id']: x for x in design['examples']}
    if set(ids) != set(design_by_id):
        raise ValueError('design cohort differs')
    reviewed = {r['example_id']: r for r in review['per_example']}
    if len(reviewed) != len(review['per_example']) or set(reviewed) != set(ids):
        raise ValueError('review has missing/duplicate dispositions')
    if (review['checks']['reviewed_fragment_count'] != len(ids) or
            review['checks']['reviewed_claim_atom_count'] != sum(len(r['packet']['claims']) for r in normal['rows'])):
        raise ValueError('review counts do not match bound normalization')
    allowed_paths = {(DESIGN.parent / a['file']).resolve()
                     for e in design['examples']
                     for a in [e['answer_anchor']] + [s['anchor'] for s in e['sources']]}
    originals = {}
    for h, rel in lineage.items():
        path = ROOT.parent / rel
        if path.resolve() not in allowed_paths:
            raise ValueError('lineage includes an unrelated original')
        if sha(path) != h:
            raise ValueError('original source drift: ' + rel)
        originals[h] = read(path)
    anchor_count = 0
    for row in normal['rows']:
        e = design_by_id[row['example_id']]
        if row['case_id'] != e['case_id'] or row['answer_id'] != e['answer_id']:
            raise ValueError('cross-case binding')
        if row['selected_fragment'] != e['answer_anchor']:
            raise ValueError('selected fragment drift')
        packet = row['packet']
        disposition = reviewed[row['example_id']]
        if (disposition['disposition'] != 'ready_with_stated_limits' or
                disposition['case_id'] != row['case_id'] or disposition['answer_id'] != row['answer_id'] or
                disposition['claim_atom_count'] != len(packet['claims'])):
            raise ValueError('review disposition or atom count differs')
        original_sources = {s['source_id']: s for s in e['sources']}
        if len(packet['sources']) != len(original_sources) or {s['id'] for s in packet['sources']} != set(original_sources):
            raise ValueError('source inventory incomplete or cross-case')
        for source in packet['sources']:
            a = original_sources[source['id']]['anchor']
            wanted = dict(sha256=a['sha256'], pointer=a['json_pointer'],
                          start=a['span']['start'], end=a['span']['end'], quote=a['quote'])
            if source['anchor'] != wanted:
                raise ValueError('source assigned to wrong case or ID')
        if set(packet) != {'schema', 'grader', 'decision_at', 'sources', 'claims', 'coverage'}:
            raise ValueError('unapproved packet fields')
        for group in ('sources', 'claims'):
            if packet['coverage'][{'sources':'source_sha256', 'claims':'claims_sha256'}[group]] != digest(packet[group]):
                raise ValueError('coverage hash mismatch')
            for item in packet[group]:
                a = item['anchor']
                raw = pointer(originals[a['sha256']], a['pointer'])
                if raw[a['start']:a['end']] != a['quote']:
                    raise ValueError('anchor mismatch')
                anchor_count += 1
                if group == 'claims':
                    f = e['answer_anchor']
                    if (a['sha256'] != f['sha256'] or a['pointer'] != f['json_pointer'] or
                            a['start'] < f['span']['start'] or a['end'] > f['span']['end']):
                        raise ValueError('claim outside selected fragment')
    return normal, anchor_count


def project(normal):
    packets, mapping = [], []
    for row in normal['rows']:
        packet = copy.deepcopy(row['packet'])
        packet['coverage']['status'] = 'agent_reviewed'
        h = digest(packet)
        packets.append(dict(packet_sha256=h, packet=packet))
        mapping.append(dict(example_id=row['example_id'], case_id=row['case_id'],
                            answer_id=row['answer_id'], packet_sha256=h))
    if len({p['packet_sha256'] for p in packets}) != len(packets):
        raise ValueError('identity collapse')
    return packets, mapping


def freeze(review_path):
    prior_count = verify_predecessor()
    normal, anchors = validate_data(review_path)
    fixed = ['checker.py', 'grade_packets.py', 'pipeline.py', 'prepare_data.py',
             'CONTRACT.md', 'NORMALIZATION.md', 'PREDECESSOR.json']
    paths = [ROOT / f for f in fixed]
    paths += sorted((ROOT / 'tests').glob('*.py'))
    paths += sorted((ROOT / 'data').glob('*.json'))
    paths += sorted((ROOT / 'review').glob('*review_v*.json'))
    paths += sorted((ROOT / 'review/prior-normalization-v1').glob('*.json'))
    if review_path not in paths:
        paths.append(review_path)
    value = dict(schema='maguire-v3-local-freeze', created_at=datetime.now(timezone.utc).isoformat(),
                 scope='fragment', independent_holdout=False, human_approved=False,
                 normalization_review=str(review_path.relative_to(ROOT)),
                 normalization_review_sha256=sha(review_path),
                 predecessor_files=prior_count, fragments=len(normal['rows']),
                 claims=sum(len(r['packet']['claims']) for r in normal['rows']),
                 verified_anchors=anchors,
                 files={str(p.relative_to(ROOT)): bound(p) for p in paths})
    write(ROOT / 'FREEZE.json', value)
    return value


def verify_freeze():
    freeze = read(ROOT / 'FREEZE.json')
    for rel, expected in freeze['files'].items():
        if bound(ROOT / rel) != expected:
            raise ValueError('frozen artifact drift: ' + rel)
    verify_predecessor()
    return freeze


def measure(predictions, mapping, expected):
    """Outcome data enters only here, after predictions have been saved."""
    truth = {r['example_id']: r for r in expected['rows']}
    if len(truth) != len(expected['rows']) or set(truth) != {r['example_id'] for r in mapping}:
        raise ValueError('measurement cohort mismatch')
    if len(predictions) != len(mapping):
        raise ValueError('prediction count mismatch')
    groups, rows = {}, []
    misses, false_rejections, reviews, invalids, forced_ambiguity = [], [], [], [], []
    intended, found, spurious, relation_mismatches = 0, 0, [], []
    claim_reviews, atom_counts = [], Counter()
    for pred, identity in zip(predictions, mapping):
        if pred['packet_sha256'] != identity['packet_sha256']:
            raise ValueError('prediction identity/order mismatch')
        e = truth[identity['example_id']]
        result = pred['result']
        actual = result['verdict']
        if actual not in {'pass', 'fail', 'needs_review', 'invalid'}:
            raise ValueError('unknown verdict')
        group = groups.setdefault(e['verdict'], dict(total=0, pass_=0, fail=0, needs_review=0, invalid=0))
        group['total'] += 1
        group['pass_' if actual == 'pass' else actual] += 1
        key = identity['example_id']
        if e['verdict'] == 'fail' and actual == 'pass': misses.append(key)
        if e['verdict'] == 'pass' and actual == 'fail': false_rejections.append(key)
        if actual == 'needs_review': reviews.append(key)
        if actual == 'invalid' or pred['execution_error'] is not None: invalids.append(key)
        if e['verdict'] == 'needs_review' and actual in {'pass', 'fail'}: forced_ambiguity.append(key)
        claims = {c['id']: c for c in result['claims']}
        if len(claims) != len(result['claims']):
            raise ValueError('duplicate returned claim')
        expected_claims = {c['claim_id']: c for c in e['claims']}
        if len(expected_claims) != len(e['claims']):
            raise ValueError('duplicate expected claim')
        if actual != 'invalid' and set(claims) != set(expected_claims):
            raise ValueError('missing/extra returned claims')
        matched_errors = []
        for cid, wanted in expected_claims.items():
            c = claims.get(cid)
            if wanted['verdict'] == 'fail': intended += 1
            if c is None: continue
            atom_counts[c['verdict']] += 1
            if c['anchor'] != wanted['anchor']:
                raise ValueError('finding/claim anchor drift')
            if c['verdict'] == 'needs_review': claim_reviews.append(key + '/' + cid)
            if c['verdict'] == 'fail' and wanted['verdict'] != 'fail': spurious.append(key + '/' + cid)
            if c['evidence_relation'] != wanted['evidence_relation']:
                relation_mismatches.append(dict(example_id=key, claim_id=cid,
                    expected=wanted['evidence_relation'], actual=c['evidence_relation']))
            if (wanted['verdict'] == 'fail' and c['verdict'] == 'fail' and
                    wanted['evidence_relation'] == c['evidence_relation']):
                found += 1
                matched_errors.append(cid)
        fail_ids = {c['id'] for c in result['claims'] if c['verdict'] == 'fail'}
        if fail_ids != {f['claim_id'] for f in result['findings']} or len(fail_ids) != len(result['findings']):
            raise ValueError('finding/claim mismatch')
        for f in result['findings']:
            if f['anchor'] != claims[f['claim_id']]['anchor']:
                raise ValueError('finding localized to wrong span')
        rows.append(dict(**identity, expected=e['verdict'], actual=actual,
                         intended_error_atoms_matched=matched_errors,
                         review_reasons=result['review_reasons'], findings=result['findings'],
                         execution_error=pred['execution_error']))
    return dict(schema='maguire-v3-measurement', scope='selected_fragments',
        human_approved_gold=False, independent_holdout=False, total=len(rows), groups=groups,
        false_acceptances=misses, false_rejections=false_rejections,
        needs_review=reviews, invalid_or_error=invalids, forced_decisions_on_ambiguity=forced_ambiguity,
        intended_error_atoms=intended, error_atoms_matched_relation_and_span=found,
        spurious_claim_failures=spurious, relation_mismatches=relation_mismatches,
        atom_verdicts=dict(atom_counts), claim_needs_review=claim_reviews,
        caveat='Relation/span match is mechanical; substantive reasoning requires separate post-run review.',
        rows=rows)


def render(m):
    lines = ['# V3: проверка ручного разбора 16 фрагментов', '',
             'Известные примеры разработки. Gold и нормализация проверены агентами; '
             'человек их не утверждал. Автоматического извлечения и оценки целых ответов нет.', '',
             '| Ожидаемая категория | Всего | pass | fail | needs_review | invalid |',
             '| --- | ---: | ---: | ---: | ---: | ---: |']
    for label, g in m['groups'].items():
        lines.append(f"| {label} | {g['total']} | {g['pass_']} | {g['fail']} | {g['needs_review']} | {g['invalid']} |")
    lines += ['', f"Пропущенные ошибки (ошибочный фрагмент получил pass): {m['false_acceptances'] or 'нет'}.",
              f"Ложные отказы (допустимый фрагмент получил fail): {m['false_rejections'] or 'нет'}.",
              f"На review: {m['needs_review'] or 'нет'}.",
              f"Принудительные решения на неоднозначности: {m['forced_decisions_on_ambiguity'] or 'нет'}.",
              f"Invalid/execution errors: {m['invalid_or_error'] or 'нет'}.", '',
              f"Ожидаемые ошибочные атомы с совпавшими relation и span: "
              f"{m['error_atoms_matched_relation_and_span']}/{m['intended_error_atoms']}.",
              f"Ложные замечания к отдельным атомам: {m['spurious_claim_failures'] or 'нет'}.",
              f"Расхождения отношений: {m['relation_mismatches'] or 'нет'}.",
              f"Отдельные атомы на review: {m['claim_needs_review'] or 'нет'}.", '',
              'Совпадение отношения и места не заменяет содержательной проверки причины.', '',
              '| Пример | Исходный ответ | Ожидалось | Получено | Замечания: claim / rule |',
              '| --- | --- | --- | --- | --- |']
    for r in m['rows']:
        findings = '; '.join(f"{x['claim_id']} / {x['rule']}" for x in r['findings']) or '—'
        lines.append(f"| {r['example_id']} | {r['case_id']}/{r['answer_id']} | {r['expected']} | {r['actual']} | {findings} |")
    lines += ['', 'D10/D11 повторяют одну формулировку в двух ответах. '
              'Количество записей не равно количеству независимых смысловых проверок.',
              'Fail может сосуществовать с неоднозначностью другого атома: '
              'уже установленный дефект не отменяется. Needs_review не считается обнаруженной ошибкой.',
              'Сохранённые пакеты не содержат example/case/answer IDs или ожидаемых решений. '
              'Хеши подтверждают локальную неизменность, не внешнюю подпись.', '']
    return '\n'.join(lines)


def run(output):
    frozen = verify_freeze()
    normal, _ = validate_data(ROOT / frozen['normalization_review'])
    packets, mapping = project(normal)
    output.mkdir(parents=True, exist_ok=False)
    with (output / 'packets.jsonl').open('x') as stream:
        for row in packets:
            stream.write(canonical(row).decode() + '\n')
    write(output / 'mapping.json', mapping)
    command = [sys.executable, '-B', str(ROOT / 'grade_packets.py'),
               '--packets', str(output / 'packets.jsonl'), '--predictions', str(output / 'predictions.jsonl')]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                               env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}, timeout=60)
    write(output / 'execution.json', dict(command=command, returncode=completed.returncode,
                                         stdout=completed.stdout, stderr=completed.stderr,
                                         python=sys.version, offline_guard='worker audit hook'))
    if completed.returncode != 0:
        raise RuntimeError('worker failed; preserve incomplete run: ' + str(output))
    predictions = read_jsonl(output / 'predictions.jsonl')
    metrics = measure(predictions, mapping, read(ROOT / 'data/expectations.json'))
    write(output / 'measurement.json', metrics)
    with (output / 'RESULTS.md').open('x') as stream: stream.write(render(metrics))
    verify_freeze()
    receipt = dict(schema='maguire-v3-local-run-receipt', created_at=datetime.now(timezone.utc).isoformat(),
                   freeze=bound(ROOT / 'FREEZE.json'), scope='selected_fragments',
                   files={p.name: bound(p) for p in sorted(output.iterdir()) if p.is_file()},
                   fragments=len(packets), packet_sha256_order=[r['packet_sha256'] for r in packets],
                   authority='offline_only_no_external_calls_no_git_writes')
    write(output / 'receipt.json', receipt)
    return metrics


def verify(output):
    frozen = verify_freeze()
    receipt = read(output / 'receipt.json')
    if receipt['freeze'] != bound(ROOT / 'FREEZE.json'):
        raise ValueError('run bound to another freeze')
    for name, expected in receipt['files'].items():
        if bound(output / name) != expected: raise ValueError('run file drift: ' + name)
    normal, _ = validate_data(ROOT / frozen['normalization_review'])
    packets, mapping = project(normal)
    if packets != read_jsonl(output / 'packets.jsonl') or mapping != read(output / 'mapping.json'):
        raise ValueError('projection drift')
    if [p['packet_sha256'] for p in packets] != receipt['packet_sha256_order'] or len(packets) != receipt['fragments']:
        raise ValueError('receipt cohort drift')
    expected_metrics = measure(read_jsonl(output / 'predictions.jsonl'), mapping,
                               read(ROOT / 'data/expectations.json'))
    if expected_metrics != read(output / 'measurement.json'):
        raise ValueError('derived metrics drift')
    if render(expected_metrics) != (output / 'RESULTS.md').read_text():
        raise ValueError('derived report drift')
    if read(output / 'execution.json')['returncode'] != 0:
        raise ValueError('nonzero execution exit')
    return dict(status='verified', fragments=len(packets), predecessor_files=verify_predecessor())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    f = subs.add_parser('freeze'); f.add_argument('--review', type=Path, required=True)
    for cmd in ('run', 'verify'):
        p = subs.add_parser(cmd); p.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'freeze':
        value = freeze(args.review.resolve())
        print(json.dumps({k:value[k] for k in ('fragments', 'claims', 'verified_anchors', 'predecessor_files')}))
    elif args.command == 'run':
        value = run(args.output.resolve())
        print(json.dumps({k:value[k] for k in ('total', 'groups', 'false_acceptances', 'false_rejections', 'needs_review', 'invalid_or_error')}, ensure_ascii=False))
    else:
        print(json.dumps(verify(args.output.resolve())))


if __name__ == '__main__':
    main()
