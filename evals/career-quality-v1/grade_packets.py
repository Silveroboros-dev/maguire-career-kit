#!/usr/bin/env python3
"""Grade projected packets only. No corpus, annotations or mapping are loaded."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from graders import grade


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def grade_rows(rows):
    """Forbid I/O during pure grading, including socket and subprocess creation."""
    active = [False]

    def guard(event, args):
        if active[0] and (event == 'open' or event.startswith(('socket.', 'subprocess.', 'os.'))):
            raise PermissionError('offline pure-grader boundary: ' + event)

    sys.addaudithook(guard)
    output, seen = [], set()
    for row in rows:
        digest = hashlib.sha256(canonical(row['packet'])).hexdigest()
        if set(row) != {'packet_sha256', 'packet'} or row['packet_sha256'] != digest or digest in seen:
            raise ValueError('invalid or duplicate packet identity')
        seen.add(digest)
        error = None
        try:
            active[0] = True
            result = grade(row['packet'])
        except Exception as exc:
            error = type(exc).__name__ + ': ' + str(exc)
            result = {'verdict': 'invalid', 'findings': [], 'assurance': 'rule_checks_only'}
        finally:
            active[0] = False
        if hashlib.sha256(canonical(row['packet'])).hexdigest() != digest:
            raise ValueError('grader mutated packet')
        if not isinstance(result, dict) or result.get('verdict') not in {'pass', 'fail', 'invalid'}:
            raise ValueError('invalid grader result envelope')
        if result.get('assurance') != 'rule_checks_only' or not isinstance(result.get('findings'), list):
            raise ValueError('missing findings/assurance')
        if result['verdict'] == 'fail' and not result['findings']:
            raise ValueError('failure without evidence')
        output.append({'packet_sha256': digest, 'result': result, 'execution_error': error})
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packets', type=Path, required=True)
    parser.add_argument('--predictions', type=Path, required=True)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.packets.read_text(encoding='utf-8').splitlines()]
    output = grade_rows(rows)
    with args.predictions.open('x', encoding='utf-8') as stream:
        for row in output:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')
        stream.flush()
        import os
        os.fsync(stream.fileno())
    print(json.dumps({'predictions': len(output),
                      'execution_errors': sum(x['execution_error'] is not None for x in output)}))


if __name__ == '__main__':
    main()
