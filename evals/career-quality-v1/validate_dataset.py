#!/usr/bin/env python3
"""Offline structural audit of authored examples; never a semantic quality grader."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
FILES = ('input.json', 'gold.json', 'answers.json', 'annotations.json')
SUITES = {'candidate-fit': ('CF', 'candidate_fit'),
          'preference-fit': ('PF', 'preference_fit')}
CRITERIA = {
    'candidate_fit': {'CF-COVERAGE', 'CF-EVIDENCE', 'CF-LABEL', 'CF-SCOPE',
                      'CF-UNCERTAINTY', 'CF-ACTION'},
    'preference_fit': {'PF-COVERAGE', 'PF-INTERPRETATION', 'PF-EVIDENCE',
                       'PF-UNKNOWN', 'PF-PRIORITY', 'PF-ACTION'},
}
LABELS = {'candidate_fit': {'supported', 'partial', 'unknown', 'contradicted'},
          'preference_fit': {'aligned', 'conflict', 'unknown'}}
ACTIONS = {'pursue', 'clarify', 'pass', 'show_existing_evidence', 'verify_skill'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def strings(values, name, nonempty=False):
    require(isinstance(values, list), name + ': expected list')
    require(not nonempty or bool(values), name + ': empty list')
    require(all(isinstance(v, str) and v.strip() for v in values), name + ': empty/non-string item')
    require(len(values) == len(set(values)), name + ': duplicate item')


def prose(value, name):
    require(isinstance(value, str) and bool(value.strip()), name + ': missing prose')


def fields(value, expected, name):
    require(isinstance(value, dict) and set(value) == set(expected.split()),
            name + ': unexpected or missing fields')


def timestamp(value):
    prose(value, 'timestamp')
    result = datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(result.utcoffset() == datetime.timedelta(0), 'timestamps must be UTC')
    return result


def index(items, key, name):
    require(isinstance(items, list), name + ': expected list')
    require(all(isinstance(x, dict) and isinstance(x.get(key), str) and x[key]
                for x in items), name + ': missing identity')
    result = {x[key]: x for x in items}
    require(len(result) == len(items), name + ': duplicate identity')
    return result


def pointer(key):
    return str(key).replace('~', '~0').replace('/', '~1')


def diff_paths(a, b, path=''):
    """Minimal recursive paths; changed-length arrays count as one edit."""
    if type(a) is not type(b):
        return [path]
    if isinstance(a, dict):
        found = []
        for key in sorted(set(a) | set(b)):
            if not path and key == 'answer_id':
                continue
            child = path + '/' + pointer(key)
            if key not in a or key not in b:
                found.append(child)
            else:
                found.extend(diff_paths(a[key], b[key], child))
        return found
    if isinstance(a, list):
        if len(a) != len(b):
            return [path]
        return [p for i, (x, y) in enumerate(zip(a, b))
                for p in diff_paths(x, y, path + '/' + str(i))]
    return [] if a == b else [path]


def audit_case(data, expected_case, grader):
    input_, gold, answers_doc, annotations_doc = [data[n] for n in FILES]
    for obj, schema in zip((input_, gold, answers_doc, annotations_doc),
                           ('input', 'gold', 'answers', 'annotations')):
        require(isinstance(obj, dict), schema + ': expected object')
        require(obj.get('schema') == 'maguire-quality-' + schema + '-v1', 'wrong schema: ' + schema)
        require(obj.get('case_id') == expected_case, 'cross-case binding: ' + schema)
    require(input_.get('grader') == grader, 'wrong grader')
    require(input_.get('data_class') == 'synthetic', 'only synthetic data allowed')
    fields(input_, 'schema case_id grader data_class decision_at task jd candidate', 'input')
    fields(input_['jd'], 'title sources', 'JD')
    fields(input_['candidate'], 'facts preferences', 'candidate')
    decision_at = timestamp(input_['decision_at'])
    prose(input_.get('task'), 'task')
    prose(input_['jd'].get('title'), 'JD title')
    jd = index(input_['jd']['sources'], 'id', 'JD sources')
    facts = index(input_['candidate']['facts'], 'id', 'facts')
    preferences = index(input_['candidate']['preferences'], 'id', 'preferences')
    sources = {**jd, **facts, **preferences}
    require(bool(jd), 'no JD sources')
    require(len(sources) == len(jd) + len(facts) + len(preferences), 'source identity collision')
    for identity, source in sources.items():
        prose(source.get('text'), 'source text: ' + identity)
    for identity, source in jd.items():
        fields(source, 'id text observed_at authority supersedes', 'JD source')
        require(identity.startswith('jd_'), 'JD source prefix')
        require(source.get('authority') in {'job_description', 'employer_update'}, 'source authority')
        require(timestamp(source['observed_at']) <= decision_at, 'future source in decision-time input')
        strings(source.get('supersedes'), 'JD supersedes')
        require(set(source['supersedes']) <= set(jd) - {identity}, 'unknown/self superseded JD source')
    for identity, fact in facts.items():
        fields(fact, 'id text evidence_type observed_at status supersedes', 'fact')
        require(identity.startswith('fact_'), 'fact prefix')
        require(fact.get('evidence_type') in {'self_report', 'supplied_artifact_excerpt'}, 'evidence type')
        require(fact.get('status') in {'active', 'withdrawn'}, 'fact status')
        require(timestamp(fact['observed_at']) <= decision_at, 'future fact in decision-time input')
        strings(fact.get('supersedes'), 'fact supersedes')
        require(set(fact['supersedes']) <= set(facts) - {identity}, 'unknown/self superseded fact')
    for identity, preference in preferences.items():
        fields(preference, 'id text priority allowed_exceptions confirmed_at', 'preference')
        require(identity.startswith('pref_'), 'preference prefix')
        require(preference.get('priority') in {'must_have', 'nice_to_have'}, 'preference priority')
        strings(preference.get('allowed_exceptions'), 'allowed exceptions')
        require(timestamp(preference['confirmed_at']) <= decision_at, 'future preference in decision-time input')

    fields(gold, 'schema case_id family title review_status human_approved units forbidden_assessment_targets acceptable_actions critical_errors notes', 'gold')
    require(gold.get('review_status') == 'proposed_agent_authored' and
            gold.get('human_approved') is False, 'incorrect gold approval claim')
    prose(gold.get('family'), 'case family')
    prose(gold.get('title'), 'case title')
    strings(gold.get('notes'), 'gold notes', nonempty=True)
    units = index(gold['units'], 'target_id', 'gold units')
    require(bool(units), 'no gold units')
    targets = jd if grader == 'candidate_fit' else preferences
    require(set(units) <= set(targets), 'gold target outside evaluated dimension')
    if grader == 'preference_fit':
        require(set(units) == set(preferences), 'gold omits a preference')
    for unit in units.values():
        fields(unit, 'target_id kind allowed_labels acceptable_evidence_sets rationale required_points forbidden_inferences', 'gold unit')
        prose(unit.get('kind'), 'unit kind')
        strings(unit.get('allowed_labels'), 'allowed labels', nonempty=True)
        require(set(unit['allowed_labels']) <= LABELS[grader], 'unknown label in gold')
        prose(unit.get('rationale'), 'gold rationale')
        strings(unit.get('required_points'), 'required points', nonempty=True)
        strings(unit.get('forbidden_inferences'), 'forbidden inferences', nonempty=True)
        sets = unit.get('acceptable_evidence_sets')
        require(isinstance(sets, list) and bool(sets), 'no acceptable evidence sets')
        for evidence in sets:
            strings(evidence, 'evidence set', nonempty=True)
            require(set(evidence) <= set(sources), 'gold references unknown source')
    strings(gold.get('forbidden_assessment_targets'), 'forbidden targets')
    require(set(gold['forbidden_assessment_targets']) <= set(sources), 'unknown forbidden target')
    require(not set(gold['forbidden_assessment_targets']) & set(units), 'required target is forbidden')
    strings(gold.get('acceptable_actions'), 'acceptable actions', nonempty=True)
    require(set(gold['acceptable_actions']) <= ACTIONS, 'unknown action in gold')
    critical = index(gold['critical_errors'], 'id', 'critical errors')
    for error in critical.values():
        fields(error, 'id description target_ids', 'critical error')
        prose(error.get('description'), 'critical error description')
        strings(error.get('target_ids'), 'critical targets', nonempty=True)
        require(set(error['target_ids']) <= set(sources), 'unknown critical-error target')

    fields(answers_doc, 'schema case_id answers', 'answers document')
    fields(annotations_doc, 'schema case_id answers', 'annotations document')
    answers = index(answers_doc['answers'], 'answer_id', 'answers')
    annotations = index(annotations_doc['answers'], 'answer_id', 'annotations')
    require(set(answers) == {'answer_01', 'answer_02', 'answer_03', 'answer_04'}, 'expected four neutral answer IDs')
    require(set(annotations) == set(answers), 'answer/annotation identity mismatch')
    positives = negatives = quote_failures = 0
    negative_categories = []
    for answer_id, answer in answers.items():
        fields(answer, 'answer_id assessments conclusion limitations', 'answer')
        annotation = annotations[answer_id]
        fields(annotation, 'answer_id expected_verdict citation_integrity reason mutation expected_findings', 'annotation')
        verdict = annotation.get('expected_verdict')
        require(verdict in {'pass', 'fail'}, 'unknown expected verdict')
        prose(annotation.get('reason'), 'annotation reason')
        assessments = index(answer['assessments'], 'target_id', answer_id + ' assessments')
        bad_citations = []
        for target, assessment in assessments.items():
            fields(assessment, 'target_id label evidence rationale', 'assessment')
            require(target in sources, 'assessment target not in input')
            require(assessment.get('label') in LABELS[grader], 'unknown response label')
            prose(assessment.get('rationale'), 'assessment rationale')
            refs = index(assessment['evidence'], 'source_id', 'answer evidence')
            for source_id, citation in refs.items():
                fields(citation, 'source_id quote', 'citation')
                prose(citation.get('quote'), 'citation quote')
                if source_id not in sources or citation['quote'] not in sources[source_id]['text']:
                    bad_citations.append(source_id)
        observed_integrity = 'fail' if bad_citations else 'pass'
        require(annotation.get('citation_integrity') == observed_integrity,
                answer_id + ': citation expectation mismatch: ' + repr(bad_citations))
        quote_failures += bool(bad_citations)
        conclusion = answer['conclusion']
        fields(conclusion, 'action text next_step', 'conclusion')
        require(conclusion.get('action') in ACTIONS, 'unknown response action')
        prose(conclusion.get('text'), 'conclusion text')
        prose(conclusion.get('next_step'), 'next step')
        strings(answer.get('limitations'), 'limitations', nonempty=True)
        if verdict == 'pass':
            positives += 1
            require(not bad_citations, 'positive has a fabricated citation')
            require(annotation.get('mutation') is None and annotation.get('expected_findings') == [],
                    'positive has mutation/findings')
            require(set(assessments) == set(units), 'positive omits/adds gold target')
            require(conclusion['action'] in gold['acceptable_actions'], 'positive action outside gold')
            for target, assessment in assessments.items():
                unit = units[target]
                require(assessment['label'] in unit['allowed_labels'], 'positive label outside gold')
                evidence = {r['source_id'] for r in assessment['evidence']}
                require(any(set(allowed) <= evidence for allowed in unit['acceptable_evidence_sets']),
                        'positive lacks a complete allowed evidence set: ' + target)
        else:
            negatives += 1
            mutation = annotation['mutation']
            fields(mutation, 'base_answer_id category description changed_paths', 'mutation')
            require(isinstance(mutation, dict) and mutation.get('base_answer_id') == 'answer_01',
                    'negative mutation base must be answer_01')
            prose(mutation.get('category'), 'mutation category')
            prose(mutation.get('description'), 'mutation description')
            negative_categories.append(mutation['category'])
            paths = diff_paths(answers['answer_01'], answer)
            strings(mutation['changed_paths'], 'changed paths', nonempty=True)
            require(paths and sorted(mutation['changed_paths']) == paths,
                    answer_id + ': mutation path mismatch; actual=' + repr(paths))
            findings = annotation.get('expected_findings')
            require(isinstance(findings, list) and bool(findings), 'negative has no expected finding')
            for finding in findings:
                fields(finding, 'criterion_id severity target_id explanation', 'finding')
                require(finding.get('criterion_id') in CRITERIA[grader], 'unknown finding criterion')
                require(finding.get('severity') in {'major', 'critical'}, 'unknown severity')
                require(finding.get('target_id') in sources, 'finding target not in input')
                prose(finding.get('explanation'), 'finding explanation')
    require(positives == negatives == 2, 'need two positive and two negative answers')
    require(annotations['answer_01']['expected_verdict'] == 'pass' and
            annotations['answer_02']['expected_verdict'] == 'pass', 'wrong positive bases')
    require(len(set(negative_categories)) == 2, 'duplicate defect category in case')
    require(diff_paths(answers['answer_01'], answers['answer_02']), 'identical positives')
    a, b = answers['answer_01'], answers['answer_02']
    def signature(answer):
        return (answer['conclusion']['action'], sorted((x['target_id'], x['label'],
                tuple(sorted(c['source_id'] for c in x['evidence']))) for x in answer['assessments']))
    return {'case_id': expected_case, 'family': gold['family'], 'title': gold['title'],
            'units': len(units), 'positive_answers': positives, 'negative_answers': negatives,
            'intentional_citation_failures': quote_failures,
            'substantive_positive_variant': signature(a) != signature(b)}


def record(path):
    raw = path.read_bytes()
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def audit(root, manifest=None):
    results, errors, files = [], [], {}
    for suite, (prefix, grader) in SUITES.items():
        expected = {prefix + '-' + str(i).zfill(2) for i in range(1, 13)}
        directory = root / suite
        actual = {p.name for p in directory.iterdir()} if directory.is_dir() else set()
        if actual != expected:
            errors.append(suite + ': expected exactly 12 case directories; got ' + repr(sorted(actual)))
        for case_id in sorted(expected):
            folder = directory / case_id
            try:
                require(not folder.is_symlink(), 'symlinked case directory')
                require({p.name for p in folder.iterdir()} == set(FILES), 'case must contain exactly four files')
                data = {}
                for name in FILES:
                    path = folder / name
                    require(path.is_file() and not path.is_symlink(), 'not a regular case file')
                    data[name] = json.loads(path.read_text(encoding='utf-8'))
                    files[str(path.relative_to(root))] = record(path)
                results.append(audit_case(data, case_id, grader))
            except (ValueError, KeyError, TypeError, OSError) as error:
                errors.append(case_id + ': ' + str(error))
        selected = [r for r in results if r['case_id'].startswith(prefix)]
        if len({r['family'] for r in selected}) != len(selected):
            errors.append(suite + ': duplicate family labels (labels alone do not prove diversity)')
        if len(selected) == 12 and sum(r['substantive_positive_variant'] for r in selected) < 4:
            errors.append(suite + ': fewer than four substantive positive variants')
    if manifest is not None:
        try:
            saved = json.loads(manifest.read_text(encoding='utf-8'))
            require(isinstance(saved, dict), 'inventory must be an object')
            require(saved.get('schema') == 'maguire-quality-case-inventory-v1', 'wrong inventory schema')
            require(saved.get('files') == files, 'case inventory hashes or membership changed')
        except (ValueError, OSError) as error:
            errors.append('manifest: ' + str(error))
    return {'schema': 'maguire-quality-structural-audit-v1', 'valid': not errors,
            'scope': 'Structure, joins, gold/positive label consistency, literal citations, mutation paths, counts and optional inventory. Not semantic grading.',
            'semantic_quality_proven': False, 'human_approved_gold': False,
            'case_count': len(results), 'positive_answers': sum(r['positive_answers'] for r in results),
            'negative_answers': sum(r['negative_answers'] for r in results),
            'cases': results, 'errors': errors, 'files': files}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    report = audit(args.root.resolve(), args.manifest)
    if args.report:
        with args.report.open('x', encoding='utf-8') as stream:
            json.dump(report, stream, indent=2, ensure_ascii=False)
            stream.write('\n')
    print(json.dumps({k: report[k] for k in ('valid', 'case_count', 'positive_answers',
                     'negative_answers', 'semantic_quality_proven', 'errors')}, ensure_ascii=False, indent=2))
    return 0 if report['valid'] else 1


if __name__ == '__main__':
    sys.exit(main())
