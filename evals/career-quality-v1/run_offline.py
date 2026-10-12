#!/usr/bin/env python3
"""Freeze code, project/shuffle 96 answers, grade offline, then measure labels."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

from measure import canonical, measure, markdown

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
SEED = 'maguire-rule-baseline-2026-10-12-v1'
SUITES = {'candidate-fit': ('CF', 'candidate_fit'), 'preference-fit': ('PF', 'preference_fit')}


def now():
    return datetime.now(timezone.utc).isoformat()


def record(path):
    if not path.is_file() or path.is_symlink():
        raise ValueError('not a regular file: ' + str(path))
    raw = path.read_bytes()
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def jsonlines(path, values):
    with path.open('x', encoding='utf-8') as stream:
        for value in values:
            stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + '\n')


def lines(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def verify_inventory(root):
    """Byte validation only; does not deserialize answer annotations."""
    manifest = read(root / 'MANIFEST.json')
    expected = {f'{suite}/{prefix}-{i:02d}/{name}' for suite, (prefix, _) in SUITES.items()
                for i in range(1, 13) for name in ('input.json', 'gold.json', 'answers.json', 'annotations.json')}
    if set(manifest['files']) != expected:
        raise ValueError('unexpected corpus membership')
    for rel in sorted(expected):
        path = root / rel
        if path.parent.is_symlink() or path.parent.parent.is_symlink():
            raise ValueError('symlinked corpus folder')
        if record(path) != manifest['files'][rel]:
            raise ValueError('frozen dataset drift: ' + rel)
    return manifest


def project(input_data, gold, answer):
    """Allowlist projection. The function has no expected-answer-label argument."""
    if input_data['case_id'] != gold['case_id']:
        raise ValueError('input/gold cross-case binding')
    if set(answer) != {'answer_id', 'assessments', 'conclusion', 'limitations'}:
        raise ValueError('answer metadata leakage or missing fields')
    return copy.deepcopy({
        'grader': input_data['grader'],
        'input': {key: input_data[key] for key in ('decision_at', 'task', 'jd', 'candidate')},
        'gold': {key: gold[key] for key in ('units', 'forbidden_assessment_targets', 'acceptable_actions')},
        'answer': {key: answer[key] for key in ('assessments', 'conclusion', 'limitations')},
    })


def prepare(root):
    packets, mapping, seen = [], [], set()
    for suite, (prefix, grader) in SUITES.items():
        for i in range(1, 13):
            case_id = f'{prefix}-{i:02d}'
            rel = suite + '/' + case_id
            folder = root / rel
            input_data, gold, answers = (read(folder / name) for name in ('input.json', 'gold.json', 'answers.json'))
            if any(data['case_id'] != case_id for data in (input_data, gold, answers)) or input_data['grader'] != grader:
                raise ValueError('cross-case corpus binding')
            if len(answers['answers']) != 4 or len({a['answer_id'] for a in answers['answers']}) != 4:
                raise ValueError('need four unique answers per case')
            for answer in answers['answers']:
                packet = project(input_data, gold, answer)
                digest = hashlib.sha256(canonical(packet)).hexdigest()
                if digest in seen:
                    raise ValueError('duplicate projected content')
                seen.add(digest)
                packets.append({'packet_sha256': digest, 'packet': packet})
                mapping.append({'packet_sha256': digest, 'case_path': rel, 'case_id': case_id,
                                'grader': grader, 'answer_id': answer['answer_id'],
                                'answer_sha256': hashlib.sha256(canonical(answer)).hexdigest()})
    packets.sort(key=lambda r: hashlib.sha256((SEED + r['packet_sha256']).encode()).hexdigest())
    mapping.sort(key=lambda r: (r['case_id'], r['answer_id']))
    return packets, mapping


def code_files(root):
    fixed = ['run_offline.py', 'grade_packets.py', 'measure.py', 'RUBRIC.md', 'FORMAT.md',
             'IMPLEMENTATION_CONTRACT.md', 'MANIFEST.json', 'validate_dataset.py',
             'review/grader_code_review_v1.json']
    paths = [root / p for p in fixed] + sorted((root / 'graders').glob('*.py')) + sorted((root / 'tests').glob('*.py'))
    if not (root / 'graders/__init__.py').is_file():
        raise ValueError('grader implementation missing')
    return {str(p.relative_to(root)): record(p) for p in paths}


def check_frozen(root, freeze):
    if code_files(root) != freeze['files']:
        raise ValueError('code/contract/manifest drift since freeze')
    verify_inventory(root)


def git_snapshot():
    def run(args):
        return subprocess.run(['git', '-C', str(REPO)] + args, check=True, capture_output=True, text=True).stdout.strip()
    return {'head': run(['rev-parse', 'HEAD']), 'branch': run(['branch', '--show-current']),
            'tracked_diff_names': run(['diff', '--name-only']),
            'staged_diff_names': run(['diff', '--cached', '--name-only'])}


def run(run_dir):
    if run_dir.parent.is_symlink() or run_dir.is_symlink() or run_dir.exists():
        raise ValueError('run directory must be new and not symlinked')
    verify_inventory(ROOT)
    original_git = git_snapshot()
    frozen_files = code_files(ROOT)
    run_dir.mkdir(parents=True)
    freeze = {'schema': 'maguire-grader-code-freeze-v1', 'created_at': now(), 'files': frozen_files,
              'git': original_git, 'shuffle_seed': SEED, 'python': sys.version, 'platform': platform.platform(),
              'authority': 'Offline local grading only. No API calls, installs, commits, pushes or case edits.',
              'exposure': 'Development data previously seen by root/authors. Runtime author did not open corpus answers/annotations; reviewer did not inspect their contents, but combined structural-test execution deserialized them. No blind-holdout claim.',
              'external_seal': False, 'assurance': 'rule_checks_only'}
    save(run_dir / 'freeze.json', freeze)
    packets, mapping = prepare(ROOT)
    jsonlines(run_dir / 'packets.jsonl', packets)
    save(run_dir / 'mapping.json', mapping)
    check_frozen(ROOT, freeze)
    started = now()
    command = [sys.executable, '-I', '-B', str(ROOT / 'grade_packets.py'), '--packets',
               str(run_dir / 'packets.jsonl'), '--predictions', str(run_dir / 'predictions.jsonl')]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    finished = now()
    save(run_dir / 'execution.json', {'command': command, 'started_at': started,
                                    'finished_at': finished, 'returncode': result.returncode,
                                    'stdout': result.stdout, 'stderr': result.stderr})
    if result.returncode:
        raise ValueError('grading process failed; execution.json preserved')
    predictions_binding = record(run_dir / 'predictions.jsonl')
    check_frozen(ROOT, freeze)
    # First annotation deserialization in this execution occurs inside measure,
    # after the grader process has exited and predictions have been fsynced.
    measurement_started = now()
    report = measure(ROOT, mapping, lines(run_dir / 'predictions.jsonl'))
    save(run_dir / 'measurement.json', report)
    with (run_dir / 'RESULTS.md').open('x', encoding='utf-8') as stream:
        stream.write(markdown(report))
    check_frozen(ROOT, freeze)
    if git_snapshot() != original_git:
        raise ValueError('Git snapshot changed during execution')
    names = ['freeze.json', 'packets.jsonl', 'mapping.json', 'predictions.jsonl',
             'execution.json', 'measurement.json', 'RESULTS.md']
    save(run_dir / 'receipt.json', {
        'schema': 'maguire-grader-run-receipt-v1', 'completed_at': now(),
        'prediction_saved_before_measurement_at': measurement_started,
        'prediction_binding_before_measurement': predictions_binding,
        'files': {name: record(run_dir / name) for name in names},
        'ordered_packet_sha256': [p['packet_sha256'] for p in packets],
        'case_manifest': record(ROOT / 'MANIFEST.json'), 'answers': len(packets),
        'groups': report['groups'], 'git_before_and_after': original_git,
        'external_seal': False, 'human_approved_gold': False,
        'runtime_boundary': 'Separate process receives projected packets only; pure grade calls deny Python audit events for file/network/process I/O. This is not an adversarial OS sandbox.',
    })
    print(json.dumps(report['groups'], indent=2))


def verify_run(run_dir):
    receipt, freeze = read(run_dir / 'receipt.json'), read(run_dir / 'freeze.json')
    expected_files = {'freeze.json', 'packets.jsonl', 'mapping.json', 'predictions.jsonl',
                      'execution.json', 'measurement.json', 'RESULTS.md'}
    if set(receipt['files']) != expected_files:
        raise ValueError('run file membership changed')
    for name, binding in receipt['files'].items():
        if record(run_dir / name) != binding:
            raise ValueError('run artifact drift: ' + name)
    check_frozen(ROOT, freeze)
    packets, mapping = prepare(ROOT)
    if packets != lines(run_dir / 'packets.jsonl') or mapping != read(run_dir / 'mapping.json'):
        raise ValueError('projection changed')
    predictions = lines(run_dir / 'predictions.jsonl')
    if [p['packet_sha256'] for p in predictions] != receipt['ordered_packet_sha256']:
        raise ValueError('prediction order/binding changed')
    report = measure(ROOT, mapping, predictions)
    if report != read(run_dir / 'measurement.json') or report['groups'] != receipt['groups']:
        raise ValueError('measurement changed')
    if markdown(report) != (run_dir / 'RESULTS.md').read_text(encoding='utf-8'):
        raise ValueError('rendered report changed')
    if receipt['case_manifest'] != record(ROOT / 'MANIFEST.json') or receipt['answers'] != len(packets):
        raise ValueError('receipt corpus binding changed')
    if receipt['prediction_binding_before_measurement'] != record(run_dir / 'predictions.jsonl'):
        raise ValueError('prediction predecessor binding changed')
    if read(run_dir / 'execution.json')['returncode'] != 0:
        raise ValueError('execution did not complete')
    print(json.dumps({'verified': True, 'answers': len(packets), 'external_seal': False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True, help='new folder, convention: runs/baseline-v1')
    parser.add_argument('--verify', action='store_true', help='verify existing result without rerunning grader')
    args = parser.parse_args()
    try:
        if args.verify:
            verify_run(args.run_dir.absolute())
        else:
            run(args.run_dir.absolute())
    except (ValueError, KeyError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
