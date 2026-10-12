#!/usr/bin/env python3
"""Verify published evidence; optionally replay v6 offline into a new directory."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
COHORT = ROOT / 'career-quality-v6-new-cases'


def bound(path):
    data = path.read_bytes()
    return {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def verify_manifest(root=ROOT):
    manifest = json.loads((root / 'PUBLICATION.json').read_text())
    files = manifest['files']
    omitted = set(manifest.get('omitted_local_files', {}))
    if not files or set(files) & omitted:
        raise ValueError('empty or overlapping publication inventory')
    actual = {str(path.relative_to(root)) for path in root.rglob('*')
              if path.is_file() and '__pycache__' not in path.parts
              and path.name != '.DS_Store' and path != root / 'PUBLICATION.json'}
    if actual - omitted != set(files):
        raise ValueError('publication inventory is incomplete or contains missing files')
    for rel, expected in files.items():
        path = (root / rel).resolve()
        if root.resolve() not in path.parents or bound(path) != expected:
            raise ValueError('published file drift: ' + rel)
    return manifest


def load_pipeline():
    sys.path.insert(0, str(COHORT))
    spec = importlib.util.spec_from_file_location('public_v6_evidence', COHORT / 'pipeline.py')
    pipeline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pipeline)
    return pipeline


def require_dependencies(manifest):
    critical = {str(Path('career-quality-v6-new-cases') / rel)
                for rel in ('pipeline.py', 'checker.py', 'v3_core.py', 'grade_packets.py',
                            'measurement.py', 'FREEZE.json')}
    critical |= {'career-quality-v6/' + rel for rel in
                 ('FREEZE.json', 'checker.py', 'v3_core.py', 'grade_packets.py', 'measurement.py')}
    if not critical <= set(manifest['files']):
        raise ValueError('critical runtime or freeze missing from publication inventory')


def verify_evidence():
    manifest = verify_manifest()
    require_dependencies(manifest)
    p = load_pipeline()
    frozen = p.read(COHORT / 'FREEZE.json')
    for name in ('checker.py', 'v3_core.py', 'grade_packets.py', 'measurement.py'):
        expected = p.read(COHORT.parent / 'career-quality-v6/FREEZE.json')['files'][name]
        if bound(COHORT / name) != expected or bound(COHORT.parent / 'career-quality-v6' / name) != expected:
            raise ValueError('original frozen v6 runtime drift: ' + name)
    packets, mapping, gold = p.load_projection(frozen['review'])
    if mapping != frozen['mapping'] or [v['packet_sha256'] for v in packets] != frozen['packet_sha256s']:
        raise ValueError('frozen projection drift')
    run = COHORT / 'runs/new-cases-v6'
    if packets != p.read_lines(run / 'packets.jsonl') or mapping != p.read(run / 'mapping.json'):
        raise ValueError('saved packet or mapping drift')
    measured = p.measure(mapping, packets, p.read_lines(run / 'predictions.jsonl'), gold)
    if measured != p.read(run / 'measurement.json') or p.report(measured) != (run / 'REPORT.md').read_text():
        raise ValueError('published result accounting drift')
    return p, packets, mapping, gold, measured, manifest


def replay(output):
    p, packets, mapping, gold, original, _ = verify_evidence()
    output = output.resolve()
    if output == ROOT or ROOT in output.parents:
        raise ValueError('replay output must be outside the published eval tree')
    output.mkdir(parents=True, exist_ok=False)
    p.write_lines(output / 'packets.jsonl', packets)
    command = [sys.executable, '-B', str(COHORT / 'grade_packets.py'), '--packets',
               str(output / 'packets.jsonl'), '--predictions', str(output / 'predictions.jsonl')]
    process = subprocess.run(command, capture_output=True, text=True, timeout=60)
    p.write(output / 'execution.json', {'returncode': process.returncode,
                                     'stdout': process.stdout, 'stderr': process.stderr})
    if process.returncode:
        raise RuntimeError('offline worker failed; output retained')
    measured = p.measure(mapping, packets, p.read_lines(output / 'predictions.jsonl'), gold)
    p.write(output / 'measurement.json', measured)
    (output / 'REPORT.md').write_text(p.report(measured))
    if measured != original:
        raise ValueError('replay differs from published result; outputs retained')
    return {'replayed': len(packets), 'matches_published_measurement': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('verify', 'run'))
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.action == 'verify':
        _, packets, _, _, _, manifest = verify_evidence()
        value = {'verified_packets': len(packets), 'published_files': len(manifest['files']),
                 'reran_checker': False, 'historical_private_receipts_verified': False}
    else:
        if args.output is None:
            parser.error('run requires --output naming a new directory outside evals/')
        value = replay(args.output)
    print(json.dumps(value, indent=2))


if __name__ == '__main__':
    main()
