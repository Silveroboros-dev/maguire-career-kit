#!/usr/bin/env python3
"""Separate code/data freezes, offline v1/v2 comparison and regression measurement."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from legacy import V1, audit, measurement

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
NEW = {'candidate-fit': ('CF2', 'candidate_fit', 5), 'preference-fit': ('PF2', 'preference_fit', 8)}
OLD = {'candidate-fit': ('CF', 'candidate_fit', 12), 'preference-fit': ('PF', 'preference_fit', 12)}
SEED = 'maguire-quality-v2-fixed-order'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def now():
    return datetime.now(timezone.utc).isoformat()


def record(path):
    if not path.is_file() or path.is_symlink():
        raise ValueError('not a regular file: ' + str(path))
    raw = path.read_bytes()
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def save(path, data):
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def tree(root):
    return {str(p.relative_to(root)): record(p) for p in sorted(root.rglob('*')) if p.is_file()}


def verify_predecessor():
    if tree(V1) != read(ROOT / 'PREDECESSOR.json')['files']:
        raise ValueError('v1 predecessor changed')


def code_files():
    fixed = ['legacy.py', 'pipeline.py', 'grade_packets.py', 'CONTRACT.md', 'PREDECESSOR.json']
    paths = [ROOT / name for name in fixed] + sorted((ROOT / 'graders').glob('*.py')) + sorted((ROOT / 'tests').glob('*.py'))
    if not (ROOT / 'graders/__init__.py').is_file():
        raise ValueError('runtime missing')
    return {str(p.relative_to(ROOT)): record(p) for p in paths}


def git_state():
    def run(args):
        return subprocess.run(['git', '-C', str(REPO)] + args, check=True, text=True, capture_output=True).stdout.strip()
    return {'head': run(['rev-parse', 'HEAD']), 'branch': run(['branch', '--show-current']),
            'tracked_diff': run(['diff', '--name-only']), 'staged_diff': run(['diff', '--cached', '--name-only'])}


def freeze_code():
    verify_predecessor()
    review = ROOT / 'review/prefreeze_code_review.json'
    save(ROOT / 'CODE_FREEZE.json', {
        'schema': 'maguire-grader-code-freeze-v2', 'created_at': now(), 'files': code_files(),
        'code_review': record(review), 'git': git_state(), 'python': sys.version,
        'external_seal': False, 'independent_holdout': False,
        'exposure': 'Known v1 cases/failures and declared defect families available during development. Runtime author and code reviewer excluded new answers before code freeze. Root will review new data only after this freeze.',
    })
    print(json.dumps({'code_frozen': True, 'binding': record(ROOT / 'CODE_FREEZE.json')}))


def check_code():
    verify_predecessor()
    freeze = read(ROOT / 'CODE_FREEZE.json')
    if code_files() != freeze['files'] or record(ROOT / 'review/prefreeze_code_review.json') != freeze['code_review']:
        raise ValueError('runtime, pipeline, tests or review changed after code freeze')
    return freeze


def case_paths(root, spec):
    for suite, (prefix, grader, count) in spec.items():
        expected = {f'{prefix}-{i:02d}' for i in range(1, count + 1)}
        if {p.name for p in (root / suite).iterdir()} != expected:
            raise ValueError('case membership mismatch: ' + suite)
        for case_id in sorted(expected):
            folder = root / suite / case_id
            if folder.is_symlink() or (root / suite).is_symlink():
                raise ValueError('symlinked corpus directory')
            if {p.name for p in folder.iterdir()} != set(audit.FILES):
                raise ValueError('case file membership mismatch')
            yield folder, case_id, grader


def metadata_signature(answer):
    return sorted((r['target_id'], r['label'], sorted((e['source_id'], e['quote']) for e in r['evidence'])) for r in answer['assessments'])


def audit_new(root):
    cases = []
    for folder, case_id, grader in case_paths(root, NEW):
        data = {name: read(folder / name) for name in audit.FILES}
        info = audit.audit_case(data, case_id, grader)
        gold = data['gold.json']
        units = {u['target_id']: u for u in gold['units']}
        answers = data['answers.json']['answers']
        base = next(a for a in answers if a['answer_id'] == 'answer_01')
        for answer in answers:
            if {r['target_id'] for r in answer['assessments']} != set(units):
                raise ValueError(case_id + ': prose challenge changed coverage')
            if answer['conclusion']['action'] not in gold['acceptable_actions']:
                raise ValueError(case_id + ': prose challenge uses disallowed action')
            for row in answer['assessments']:
                u = units[row['target_id']]
                if row['label'] not in u['allowed_labels']:
                    raise ValueError(case_id + ': prose challenge uses disallowed label')
                cited = {c['source_id'] for c in row['evidence']}
                if not any(set(s) <= cited for s in u['acceptable_evidence_sets']):
                    raise ValueError(case_id + ': prose challenge lacks sufficient sources')
            if grader == 'preference_fit' and (metadata_signature(answer) != metadata_signature(base)
                    or answer['conclusion']['action'] != base['conclusion']['action']):
                raise ValueError(case_id + ': preference labels/citations/action differ from base')
        if info['intentional_citation_failures']:
            raise ValueError(case_id + ': prose challenge has invalid citations')
        cases.append(info)
    return {'schema': 'maguire-prose-challenge-structural-audit-v2', 'cases': cases,
            'case_count': len(cases), 'answers': sum(c['positive_answers'] + c['negative_answers'] for c in cases),
            'valid': True, 'semantic_quality_proven': False,
            'all_labels_citations_coverage_actions_valid': True,
            'preference_structural_signatures_identical_within_case': True}


def freeze_data():
    check_code()
    review = ROOT / 'review/dataset_review.json'
    reviewed = read(review)
    files = tree(ROOT / 'cases')
    if reviewed.get('status') != 'ready' or reviewed.get('blocking_findings') != [] or reviewed.get('case_files') != files:
        raise ValueError('dataset review missing, unresolved, or bound to different files')
    report = audit_new(ROOT / 'cases')
    save(ROOT / 'STRUCTURAL_AUDIT.json', report)
    save(ROOT / 'MANIFEST.json', {'schema': 'maguire-prose-challenge-inventory-v2',
                                'created_at': now(), 'files': files,
                                'cases': 13, 'answers': 52, 'human_approved': False, 'external_seal': False})
    save(ROOT / 'DATA_FREEZE.json', {'schema': 'maguire-prose-challenge-freeze-v2', 'created_at': now(),
                                   'code_freeze': record(ROOT / 'CODE_FREEZE.json'),
                                   'manifest': record(ROOT / 'MANIFEST.json'),
                                   'audit': record(ROOT / 'STRUCTURAL_AUDIT.json'),
                                   'review': record(review), 'external_seal': False})
    print(json.dumps({'data_frozen': True, 'cases': 13, 'answers': 52}))


def check_data():
    check_code()
    freeze = read(ROOT / 'DATA_FREEZE.json')
    for key, path in [('code_freeze', 'CODE_FREEZE.json'), ('manifest', 'MANIFEST.json'),
                      ('audit', 'STRUCTURAL_AUDIT.json'), ('review', 'review/dataset_review.json')]:
        if record(ROOT / path) != freeze[key]:
            raise ValueError('data-freeze binding changed: ' + path)
    if tree(ROOT / 'cases') != read(ROOT / 'MANIFEST.json')['files']:
        raise ValueError('frozen challenge data changed')


def project(inp, gold, answer):
    if inp['case_id'] != gold['case_id']:
        raise ValueError('cross-case gold')
    if set(answer) != {'answer_id', 'assessments', 'conclusion', 'limitations'}:
        raise ValueError('answer metadata leakage')
    return copy.deepcopy({'grader': inp['grader'],
                          'input': {k: inp[k] for k in ('decision_at', 'task', 'jd', 'candidate')},
                          'gold': {k: gold[k] for k in ('units', 'forbidden_assessment_targets', 'acceptable_actions')},
                          'answer': {k: answer[k] for k in ('assessments', 'conclusion', 'limitations')}})


def prepare(root, spec):
    packets, mapping, seen = [], [], set()
    for folder, case_id, grader in case_paths(root, spec):
        inp, gold, doc = (read(folder / name) for name in ('input.json', 'gold.json', 'answers.json'))
        if any(d['case_id'] != case_id for d in (inp, gold, doc)) or inp['grader'] != grader:
            raise ValueError('cross-case source binding')
        if len(doc['answers']) != 4 or len({a['answer_id'] for a in doc['answers']}) != 4:
            raise ValueError('four unique answers required')
        for answer in doc['answers']:
            packet = project(inp, gold, answer)
            digest = hashlib.sha256(measurement.canonical(packet)).hexdigest()
            if digest in seen:
                raise ValueError('duplicate projected packet')
            seen.add(digest)
            packets.append({'packet_sha256': digest, 'packet': packet})
            mapping.append({'packet_sha256': digest, 'case_path': str(folder.relative_to(root)),
                            'case_id': case_id, 'grader': grader, 'answer_id': answer['answer_id'],
                            'answer_sha256': hashlib.sha256(measurement.canonical(answer)).hexdigest()})
    packets.sort(key=lambda p: hashlib.sha256((SEED + p['packet_sha256']).encode()).hexdigest())
    mapping.sort(key=lambda p: (p['case_id'], p['answer_id']))
    return packets, mapping


def render(report, dataset, output):
    text = measurement.markdown(report)
    all_ = report['groups']['all']
    text = text.replace('Все 96 ответов', f"Все {all_['answers']} ответов")
    text = text.replace('Нет на этих 48 допустимых ответах.', f"Нет на этих {all_['expected_correct']} допустимых ответах.")
    for suite in ('candidate-fit', 'preference-fit'):
        rel = Path(os.path.relpath(dataset / suite, output)).as_posix()
        text = text.replace('../../' + suite + '/', rel + '/')
    return text


def run(suite, engine, output):
    check_data()
    state = git_state()
    if output.exists() or output.is_symlink() or output.parent.is_symlink():
        raise ValueError('use a new run directory')
    dataset, spec = (ROOT / 'cases', NEW) if suite == 'new' else (V1, OLD)
    runtime = ROOT if engine == 'v2' else V1
    packets, mapping = prepare(dataset, spec)
    output.mkdir(parents=True)
    save(output / 'freeze.json', {'schema': 'maguire-comparison-run-v2', 'created_at': now(),
                                 'suite': suite, 'engine': engine, 'git': state,
                                 'code_freeze': record(ROOT / 'CODE_FREEZE.json'),
                                 'data_freeze': record(ROOT / 'DATA_FREEZE.json'),
                                 'predecessor': record(ROOT / 'PREDECESSOR.json'), 'seed': SEED})
    with (output / 'packets.jsonl').open('x', encoding='utf-8') as stream:
        for packet in packets:
            stream.write(json.dumps(packet, sort_keys=True, ensure_ascii=False) + '\n')
    save(output / 'mapping.json', mapping)
    command = [sys.executable, '-I', '-B', str(runtime / 'grade_packets.py'),
               '--packets', str(output / 'packets.jsonl'), '--predictions', str(output / 'predictions.jsonl')]
    started = now()
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    save(output / 'execution.json', {'started_at': started, 'finished_at': now(), 'command': command,
                                     'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
    if result.returncode:
        raise ValueError('grader process failed; execution preserved')
    before_measurement = record(output / 'predictions.jsonl')
    check_data()
    measured_at = now()
    report = measurement.measure(dataset, mapping, rows(output / 'predictions.jsonl'))
    save(output / 'measurement.json', report)
    with (output / 'RESULTS.md').open('x', encoding='utf-8') as stream:
        stream.write(render(report, dataset, output))
    check_data()
    if git_state() != state:
        raise ValueError('Git state changed during run')
    names = ['freeze.json', 'packets.jsonl', 'mapping.json', 'execution.json', 'predictions.jsonl', 'measurement.json', 'RESULTS.md']
    save(output / 'receipt.json', {'schema': 'maguire-comparison-receipt-v2', 'completed_at': now(),
                                  'suite': suite, 'engine': engine, 'answers': len(packets),
                                  'files': {n: record(output / n) for n in names},
                                  'ordered_packet_sha256': [p['packet_sha256'] for p in packets],
                                  'predictions_before_measurement': before_measurement, 'measured_at': measured_at,
                                  'groups': report['groups'], 'external_seal': False, 'human_approved_gold': False})
    print(json.dumps({'suite': suite, 'engine': engine, 'groups': report['groups']}, indent=2))


def verify(output):
    check_data()
    receipt, freeze = read(output / 'receipt.json'), read(output / 'freeze.json')
    expected = {'freeze.json', 'packets.jsonl', 'mapping.json', 'execution.json', 'predictions.jsonl', 'measurement.json', 'RESULTS.md'}
    if set(receipt['files']) != expected:
        raise ValueError('receipt membership changed')
    for name, binding in receipt['files'].items():
        if record(output / name) != binding:
            raise ValueError('artifact changed: ' + name)
    if (freeze['suite'], freeze['engine']) != (receipt['suite'], receipt['engine']):
        raise ValueError('cross-run binding')
    for key, file in [('code_freeze', 'CODE_FREEZE.json'), ('data_freeze', 'DATA_FREEZE.json'), ('predecessor', 'PREDECESSOR.json')]:
        if freeze[key] != record(ROOT / file):
            raise ValueError('run freeze predecessor changed')
    dataset, spec = (ROOT / 'cases', NEW) if freeze['suite'] == 'new' else (V1, OLD)
    packets, mapping = prepare(dataset, spec)
    if packets != rows(output / 'packets.jsonl') or mapping != read(output / 'mapping.json'):
        raise ValueError('projection drift')
    predictions = rows(output / 'predictions.jsonl')
    if [p['packet_sha256'] for p in predictions] != receipt['ordered_packet_sha256']:
        raise ValueError('prediction identity/order drift')
    if [p['packet_sha256'] for p in packets] != receipt['ordered_packet_sha256'] or receipt['answers'] != len(packets):
        raise ValueError('receipt cohort drift')
    report = measurement.measure(dataset, mapping, predictions)
    if report != read(output / 'measurement.json') or report['groups'] != receipt['groups']:
        raise ValueError('measurement drift')
    if render(report, dataset, output) != (output / 'RESULTS.md').read_text(encoding='utf-8'):
        raise ValueError('render drift')
    if receipt['predictions_before_measurement'] != record(output / 'predictions.jsonl'):
        raise ValueError('prediction predecessor drift')
    if read(output / 'execution.json')['exit_code'] != 0:
        raise ValueError('execution incomplete')
    print(json.dumps({'verified': True, 'suite': receipt['suite'], 'engine': receipt['engine'], 'answers': len(packets)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['freeze-code', 'audit-data', 'freeze-data', 'run', 'verify'])
    parser.add_argument('--suite', choices=['new', 'regression'], default='new')
    parser.add_argument('--engine', choices=['v1', 'v2'], default='v2')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        if args.action == 'freeze-code': freeze_code()
        elif args.action == 'audit-data':
            check_code()
            print(json.dumps(audit_new(ROOT / 'cases'), indent=2))
        elif args.action == 'freeze-data': freeze_data()
        elif args.output is None: raise ValueError('--output required')
        elif args.action == 'run': run(args.suite, args.engine, args.output.absolute())
        else: verify(args.output.absolute())
    except (ValueError, KeyError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
