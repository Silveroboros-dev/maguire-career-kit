"""Post-prediction measurement against proposed annotations; never imported by graders."""
import hashlib
import json
from collections import Counter
from pathlib import Path


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def keyed(rows, key):
    result = {}
    for row in rows:
        value = row[key]
        if value in result:
            raise ValueError('duplicate identity: ' + value)
        result[value] = row
    return result


def value_at(answer, pointer):
    value = answer
    for token in pointer.split('/')[1:]:
        token = token.replace('~1', '/').replace('~0', '~')
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def measure(root, mapping, predictions):
    """Exact content join, no position-based join; invalids remain in denominators."""
    expected = keyed(mapping, 'packet_sha256')
    observed = keyed(predictions, 'packet_sha256')
    if expected.keys() != observed.keys():
        raise ValueError('missing or extra predictions')
    rows = []
    for digest, binding in expected.items():
        folder = root / binding['case_path']
        if folder.resolve().parent not in {(root / s).resolve() for s in ('candidate-fit', 'preference-fit')}:
            raise ValueError('case path outside corpus')
        answers = json.loads((folder / 'answers.json').read_text(encoding='utf-8'))
        annotations = json.loads((folder / 'annotations.json').read_text(encoding='utf-8'))
        if answers['case_id'] != binding['case_id'] or annotations['case_id'] != binding['case_id']:
            raise ValueError('cross-case annotation binding')
        answer = keyed(answers['answers'], 'answer_id')[binding['answer_id']]
        if hashlib.sha256(canonical(answer)).hexdigest() != binding['answer_sha256']:
            raise ValueError('answer bytes changed after projection')
        annotation = keyed(annotations['answers'], 'answer_id')[binding['answer_id']]
        result = observed[digest]['result']
        wanted, actual = annotation['expected_verdict'], result['verdict']
        if wanted not in {'pass', 'fail'} or actual not in {'pass', 'fail', 'invalid'}:
            raise ValueError('unknown verdict')
        outcome = ('invalid' if actual == 'invalid' else
                   'false_acceptance' if wanted == 'fail' and actual == 'pass' else
                   'false_rejection' if wanted == 'pass' and actual == 'fail' else
                   'caught_error' if wanted == 'fail' else 'accepted_correct')
        found = {(f['criterion_id'], f['target_id']) for f in result['findings']} if actual == 'fail' else set()
        intended = [{**f, 'exact_criterion_target_match': (f['criterion_id'], f['target_id']) in found}
                    for f in annotation['expected_findings']]
        mutation = annotation['mutation']
        excerpts = [{'path': p, 'value': value_at(answer, p)} for p in mutation['changed_paths']] if mutation else []
        rows.append({**binding, 'expected_verdict': wanted, 'actual_verdict': actual,
                     'outcome': outcome, 'annotation_reason': annotation['reason'],
                     'mutation_category': mutation['category'] if mutation else None,
                     'mutation_description': mutation['description'] if mutation else None,
                     'mutated_answer_fragments': excerpts, 'findings': result['findings'],
                     'intended_findings': intended,
                     'execution_error': observed[digest]['execution_error']})
    groups = {}
    for family in ('candidate_fit', 'preference_fit', 'all'):
        selected = [r for r in rows if family == 'all' or r['grader'] == family]
        count = Counter(r['outcome'] for r in selected)
        good = sum(r['expected_verdict'] == 'pass' for r in selected)
        bad = len(selected) - good
        invalid_good = sum(r['outcome'] == 'invalid' and r['expected_verdict'] == 'pass' for r in selected)
        invalid_bad = sum(r['outcome'] == 'invalid' and r['expected_verdict'] == 'fail' for r in selected)
        evaluated_good, evaluated_bad = good - invalid_good, bad - invalid_bad
        groups[family] = {
            'answers': len(selected), 'expected_correct': good, 'expected_incorrect': bad,
            **{k: count[k] for k in ('accepted_correct', 'caught_error', 'false_acceptance', 'false_rejection', 'invalid')},
            'invalid_correct': invalid_good, 'invalid_incorrect': invalid_bad,
            'evaluated_correct': evaluated_good, 'evaluated_incorrect': evaluated_bad,
            'execution_errors': sum(r['execution_error'] is not None for r in selected),
            'false_acceptance_rate_evaluated': count['false_acceptance'] / evaluated_bad if evaluated_bad else None,
            'false_rejection_rate_evaluated': count['false_rejection'] / evaluated_good if evaluated_good else None,
            'false_acceptance_rate_attempted': count['false_acceptance'] / bad if bad else None,
            'false_rejection_rate_attempted': count['false_rejection'] / good if good else None,
            'intended_findings': sum(len(r['intended_findings']) for r in selected),
            'exact_criterion_target_matches': sum(f['exact_criterion_target_match'] for r in selected for f in r['intended_findings']),
        }
    by_criterion = {}
    for r in rows:
        for f in r['intended_findings']:
            c = by_criterion.setdefault(f['criterion_id'], {'intended': 0, 'exact_matches': 0,
                                                          'answers_accepted': 0, 'answers_rejected': 0, 'invalid': 0})
            c['intended'] += 1
            c['exact_matches'] += int(f['exact_criterion_target_match'])
            c['answers_accepted'] += int(r['actual_verdict'] == 'pass')
            c['answers_rejected'] += int(r['actual_verdict'] == 'fail')
            c['invalid'] += int(r['actual_verdict'] == 'invalid')
    return {'schema': 'maguire-offline-grader-measurement-v1', 'groups': groups,
            'by_criterion': by_criterion, 'rows': rows,
            'human_approved_gold': False, 'independent_holdout': False,
            'assurance': 'Bounded deterministic checks against proposed development labels, not general semantic accuracy.',
            'localization_caveat': 'Exact criterion+target equality is a mechanical localization proxy, not independent confirmation of explanation correctness.'}


def markdown(report):
    lines = ['# Результаты offline-грейдеров', '',
             'Все 96 ответов проверены по заранее зафиксированному коду. `pass` означает отсутствие',
             'ошибок, обнаруженных реализованными правилами; смысловая корректность целиком не доказана.',
             'Разметка предложена агентами и не утверждена человеком. Это development, не holdout.', '',
             '| Грейдер | Ответов | Ошибки найдены | Ошибки пропущены | Корректные приняты | Ложные отказы | Invalid |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for key, name in [('candidate_fit', 'Candidate → JD'), ('preference_fit', 'Role → preferences'), ('all', 'Всего')]:
        c = report['groups'][key]
        lines.append(f"| {name} | {c['answers']} | {c['caught_error']}/{c['expected_incorrect']} | {c['false_acceptance']}/{c['expected_incorrect']} | {c['accepted_correct']}/{c['expected_correct']} | {c['false_rejection']}/{c['expected_correct']} | {c['invalid']} |")
    lines += ['', '## Пропущенные ошибки — ошибочный ответ получил pass', '']
    missed = [r for r in report['rows'] if r['outcome'] == 'false_acceptance']
    if not missed:
        lines.append('Нет на этом наборе. Это не доказывает полноту правил вне набора.')
    for r in missed:
        lines += detail(r, show_excerpt=True)
    lines += ['', '## Ложные отказы — допустимый ответ получил fail', '']
    rejected = [r for r in report['rows'] if r['outcome'] == 'false_rejection']
    if not rejected:
        lines.append('Нет на этих 48 допустимых ответах.')
    for r in rejected:
        lines += detail(r, show_excerpt=False)
    lines += ['', '## Найден ли именно задуманный дефект', '',
              'Здесь более строгий, но всё ещё механический показатель: совпадение `criterion_id`',
              'и `target_id` с авторской аннотацией. Иное название критерия может описывать ту же',
              'ошибку; совпадение названий само по себе тоже не доказывает качество объяснения.', '',
              '| Критерий | Дефектов | Точное совпадение | Ответ отклонён | Ответ пропущен | Invalid |',
              '| --- | ---: | ---: | ---: | ---: | ---: |']
    for key, c in sorted(report['by_criterion'].items()):
        lines.append(f"| {key} | {c['intended']} | {c['exact_matches']} | {c['answers_rejected']} | {c['answers_accepted']} | {c['invalid']} |")
    unmatched = [r for r in report['rows'] if r['outcome'] == 'caught_error' and
                 not all(f['exact_criterion_target_match'] for f in r['intended_findings'])]
    lines += ['', 'Отклонённые ответы без полного совпадения ожидаемого критерия и цели:', '']
    if not unmatched:
        lines.append('Нет.')
    for r in unmatched:
        actual = ', '.join(sorted({str(f['criterion_id']) + '@' + str(f['target_id']) for f in r['findings']}))
        expected = ', '.join(f['criterion_id'] + '@' + str(f['target_id']) for f in r['intended_findings'])
        lines.append(f"- {r['case_id']}/{r['answer_id']}: ожидалось {expected}; найдено {actual}.")
    invalid = [r for r in report['rows'] if r['outcome'] == 'invalid']
    lines += ['', '## Невалидные оценки', '']
    lines += [f"- {r['case_id']}/{r['answer_id']}: {r['execution_error'] or r['findings']}" for r in invalid] or ['Нет.']
    lines += ['', '## Границы результата', '',
              '- Нет live API-вызовов, модельного judge или новых ответов Maguire. Проверены готовые фикстуры.',
              '- Идентификаторы и авторские вердикты исключены из runtime-пакета. Код и данные зафиксированы до прогона; авторы проекта ранее видели development-набор.',
              '- Gold содержит допустимые метки и основания. Это проверка качества ответа относительно подготовленного эталона, а не самостоятельная оценка новой вакансии.',
              '- Сравнение идёт с предложенной разметкой, а не с независимо подтверждённой истиной. Нет оценки вероятности интервью или порога выпуска продукта.',
              '- Смысловая полнота цитаты, тонкие преувеличения и полезность каждого next_step требуют последующей проверки человеком или отдельно валидированным semantic judge.',
              '- Набор не менялся для улучшения результата. Хеши локальные и не являются внешней подписью.', '',
              'Полная детализация: [measurement.json](measurement.json); ответы грейдера: [predictions.jsonl](predictions.jsonl);',
              'фиксация кода: [freeze.json](freeze.json); итоговая связность: [receipt.json](receipt.json).', '']
    return '\n'.join(lines)


def detail(row, show_excerpt):
    link = '../../' + row['case_path']
    lines = [f"### {row['case_id']}/{row['answer_id']}", '',
             f"[Ответ]({link}/answers.json) · [Разметка]({link}/annotations.json)", '', row['annotation_reason'], '']
    for f in row['findings']:
        lines.append(f"- `{f['criterion_id']}` / `{f['code']}` / `{f['target_id']}`: {f['explanation']}")
    if show_excerpt:
        for frag in row['mutated_answer_fragments']:
            text = json.dumps(frag['value'], ensure_ascii=False) if not isinstance(frag['value'], str) else frag['value']
            lines += [f"Изменённое поле `{frag['path']}`:", '', '> ' + text.replace('\n', '\n> '), '']
    return lines
