"""V6 accounting preserves v5 metric definitions; only schema identifiers change."""
import hashlib
import json
FAMILIES = ("candidate-fit", "preference-fit")
VERDICTS = ("pass", "fail", "needs_review", "invalid")

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')

def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def require(ok, message):
    if not ok:
        raise ValueError(message)

def unique(rows, field, label):
    result = {r[field]: r for r in rows}
    require(len(result) == len(rows), 'duplicate ' + label)
    return result

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

def validate_result(result, packet):
    require(set(result) == {'schema', 'scope', 'assurance', 'verdict', 'claims', 'findings',
                            'review_reasons', 'whole_answer_verdict'}, 'invalid result fields')
    require(result['schema'] == 'maguire-claim-packet-v6' and result['scope'] == 'fragment' and
            result['assurance'] == 'manual_normalization_agent_reviewed' and
            result['whole_answer_verdict'] is None, 'invalid result scope')
    require(isinstance(result['review_reasons'], list) and
            all(isinstance(x, str) and x for x in result['review_reasons']), 'invalid review reasons')
    if result['verdict'] == 'invalid':
        require(result['claims'] == [] and result['findings'] == [] and result['review_reasons'],
                'invalid result must preserve technical failure without partial verdicts')
        return
    require([c['id'] for c in result['claims']] == [c['id'] for c in packet['claims']], 'claim order differs')
    fields = {'id', 'anchor', 'parse_status', 'reasoning_status', 'evidence_relation', 'verdict',
              'rule', 'explanation', 'support_evidence_ids', 'counter_evidence_ids', 'limited_evidence_ids',
              'evidence_ids', 'inspected_source_ids', 'axes'}
    source_ids = {s['id'] for s in packet['sources']}
    for c in result['claims']:
        require(fields <= set(c), 'missing claim explanation envelope')
        require(c['verdict'] in VERDICTS[:3] and c['parse_status'] in ('valid', 'ambiguous') and
                c['reasoning_status'] == ('unresolved' if c['verdict'] == 'needs_review' else 'resolved'),
                'claim status inconsistent')
        require(c['evidence_relation'] in (None, 'supported', 'contradicted', 'not_established', 'conflicting'),
                'invalid evidence relation')
        require(all(isinstance(c[k], str) and c[k] for k in ('rule', 'explanation')), 'empty claim explanation')
        require(isinstance(c['axes'], list) and all(isinstance(x, str) for x in c['axes']), 'invalid axes')
        for k in ('support_evidence_ids', 'counter_evidence_ids', 'limited_evidence_ids', 'evidence_ids', 'inspected_source_ids'):
            require(isinstance(c[k], list) and len(c[k]) == len(set(c[k])) and set(c[k]) <= source_ids,
                    'foreign/duplicate evidence ' + k)
    failed = [c for c in result['claims'] if c['verdict'] == 'fail']
    finding_keys = ('anchor', 'evidence_relation', 'rule', 'explanation', 'axes', 'evidence_ids')
    expected_findings = [dict(claim_id=c['id'], **{k: c[k] for k in finding_keys}) for c in failed]
    require(result['findings'] == expected_findings, 'finding/claim mismatch')
    coverage = packet['coverage']
    deferred = (any(c['verdict'] == 'needs_review' for c in result['claims']) or result['review_reasons'] or
                coverage['status'] != 'agent_reviewed' or not coverage['source_inventory_complete'] or
                not coverage['fragment_complete'])
    expected = 'fail' if failed else 'needs_review' if deferred else 'pass'
    require(result['verdict'] == expected, 'fragment verdict inconsistent with claims/coverage')


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
        validate_result(result, p['packet'])
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
    return dict(schema='maguire-v6-regression-measurement', human_approved=False,
                scope='manually normalized fragments; no extractor or complete-advice assessment',
                overall=metric_group(rows), by_family={f: metric_group([r for r in rows if r['family'] == f]) for f in FAMILIES},
                rows=rows)
