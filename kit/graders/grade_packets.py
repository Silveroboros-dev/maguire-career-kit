#!/usr/bin/env python3
"""Isolated execution of v8 packets without labels; never loads expectation data."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ACTIVE = [False]


def offline_guard(event, args):
    if event.startswith(('socket.', 'subprocess.', 'os.system', 'os.exec', 'os.spawn')):
        raise PermissionError('offline worker: ' + event)
    if ACTIVE[0] and (event == 'open' or event.startswith('os.')):
        raise PermissionError('pure checker: ' + event)


sys.addaudithook(offline_guard)
from checker import grade_fragment  # noqa: E402


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def execute(rows):
    seen, predictions = set(), []
    for row in rows:
        if set(row) != {'packet_sha256', 'packet'}:
            raise ValueError('unexpected worker input fields')
        identity = hashlib.sha256(canonical(row['packet'])).hexdigest()
        if identity != row['packet_sha256'] or identity in seen:
            raise ValueError('packet identity invalid or duplicate')
        seen.add(identity)
        error = None
        try:
            ACTIVE[0] = True
            result = grade_fragment(row['packet'])
        except Exception as exc:
            error = type(exc).__name__ + ': ' + str(exc)
            result = dict(schema='maguire-claim-packet-v8', scope='fragment',
                          assurance='manual_normalization_agent_reviewed', verdict='invalid',
                          claims=[], findings=[], review_reasons=['execution_error'],
                          whole_answer_verdict=None)
        finally:
            ACTIVE[0] = False
        if hashlib.sha256(canonical(row['packet'])).hexdigest() != identity:
            raise ValueError('checker mutated packet')
        if result.get('verdict') not in {'pass', 'fail', 'needs_review', 'invalid'}:
            raise ValueError('invalid result envelope')
        predictions.append(dict(packet_sha256=identity, result=result, execution_error=error))
    return predictions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packets', type=Path, required=True)
    parser.add_argument('--predictions', type=Path, required=True)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.packets.read_text().splitlines()]
    results = execute(rows)
    with args.predictions.open('x') as stream:
        for result in results:
            stream.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + '\n')
    print(json.dumps({'records': len(results),
                      'execution_errors': sum(r['execution_error'] is not None for r in results)}))


if __name__ == '__main__':
    main()
