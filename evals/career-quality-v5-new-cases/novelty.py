"""Outcome-blind text-overlap screen; similarity is not semantic clearance."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parent
EVALS = ROOT.parent


def read(path):
    return json.loads(path.read_text())


def bound(path):
    b = path.read_bytes()
    return {'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}


def text_fields(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in ('text', 'rationale', 'next_step') and isinstance(item, str):
                yield item
            elif isinstance(item, (dict, list)):
                yield from text_fields(item)
    elif isinstance(value, list):
        for item in value:
            yield from text_fields(item)


def canon(s):
    return ' '.join(s.casefold().split())


def tokens(s):
    return set(re.findall(r'[a-z]+', s.casefold()))


def main():
    if (ROOT / 'FREEZE.json').exists() or (ROOT / 'START.json').exists():
        raise RuntimeError('frozen cohort: no screening rewrite')
    corpus, bindings = [], {}
    def bind(p):
        bindings[str(p.relative_to(EVALS))] = bound(p)
    for version in ('career-quality-v1', 'career-quality-v2'):
        for p in sorted((EVALS / version).rglob('input.json')):
            answers = p.with_name('answers.json')
            if not answers.exists():
                continue
            bind(p); bind(answers)
            sources = list(text_fields(read(p)))
            for a in read(answers)['answers']:
                answer = '\n'.join(text_fields(a))
                corpus.append({'ref': str(answers.relative_to(EVALS)) + '#' + a['answer_id'],
                               'sources': sources, 'answer': answer})
    p = EVALS / 'career-quality-v3/data/normalizations.json'
    bind(p)
    for row in read(p)['rows']:
        corpus.append({'ref': str(p.relative_to(EVALS)) + '#' + row['example_id'],
                       'sources': [s['anchor']['quote'] for s in row['packet']['sources']],
                       'answer': row['selected_fragment']['quote']})
    for version in ('career-quality-v3-new-cases', 'career-quality-v4', 'career-quality-v5'):
        for p in sorted((EVALS / version / 'raw').glob('*.json')):
            bind(p)
            for row in read(p)['rows']:
                corpus.append({'ref': str(p.relative_to(EVALS)) + '#' + row['case_id'],
                               'sources': [s['text'] for s in row['sources']], 'answer': row['answer']['text']})
    unique = {}
    for c in corpus:
        text = '\n'.join(c['sources'] + [c['answer']])
        c['text'] = text
        c['tokens'] = tokens(text)
        unique.setdefault(canon(text), c)
    rows = []
    raw_bindings = {}
    for p in sorted((ROOT / 'raw').glob('*.json')):
        raw_bindings[str(p.relative_to(ROOT))] = bound(p)
        for row in read(p)['rows']:
            text = '\n'.join([s['text'] for s in row['sources']] + [row['answer']['text']])
            t = tokens(text)
            scores = sorted(((len(t & c['tokens']) / len(t | c['tokens']), c)
                             for c in unique.values()), key=lambda pair: pair[0], reverse=True)[:3]
            rows.append({'case_id': row['case_id'], 'text_sha256': hashlib.sha256(text.encode()).hexdigest(),
                         'exact_source_answer_overlap': canon(text) in unique,
                         'exact_answer_overlap': any(canon(row['answer']['text']) == canon(c['answer']) for c in corpus),
                         'nearest': [{'ref': c['ref'], 'word_jaccard': round(score, 5),
                                      'sources': c['sources'], 'answer': c['answer']} for score, c in scores]})
    result = {'schema': 'maguire-v5-new-cases-overlap-screen-v1', 'human_approved': False,
              'comparison_files': bindings, 'new_raw_files': raw_bindings,
              'prior_records': len(corpus), 'unique_prior_source_answer_texts': len(unique),
              'rows': rows, 'limits': 'No labels or outcomes read. Exact/word overlap only; shared reasoning families and semantic overlap require review. New text does not prove statistical independence.'}
    output = ROOT / 'NOVELTY_SCREEN.json'
    version = 2
    while output.exists():
        output = ROOT / ('NOVELTY_SCREEN_v%d.json' % version)
        version += 1
    with output.open('x') as f:
        json.dump(result, f, ensure_ascii=False, indent=2); f.write('\n')
    print(json.dumps({'output': output.name, 'new_rows': len(rows), 'prior_records': len(corpus), 'unique_prior_texts': len(unique),
                      'exact_overlaps': [r['case_id'] for r in rows if r['exact_source_answer_overlap'] or r['exact_answer_overlap']]}))


if __name__ == '__main__':
    main()
