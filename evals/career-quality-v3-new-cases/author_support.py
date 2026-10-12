"""Small authoring helpers. No checker import, predictions or network calls."""
from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def p(subject, predicate, obj, modality='observation', polarity='positive',
      epistemic_scope='world', scope=None, time=None, measure=None):
    return dict(subject=subject, predicate=predicate, object=obj, modality=modality,
                polarity=polarity, epistemic_scope=epistemic_scope,
                scope=scope or {}, time=time or {}, measure=measure)


def m(kind, unit, lower, upper, per=None):
    return dict(kind=kind, unit=unit, lower=lower, upper=upper, per=per)


def source(id, text, facts, kind='candidate_fact', status='active',
           observed_at='2026-09-14T10:00:00Z'):
    return dict(id=id, text=text, facts=facts, kind=kind, status=status, observed_at=observed_at)


def claim(id, quote, reading=None, stance='asserted', readings=None):
    return dict(id=id, quote=quote, stance=stance,
                readings=readings if readings is not None else [reading])


def case(id, title, sources, answer, claims, expected, reason,
         error_claim_ids=None, review_reason=None, tags=None,
         decision_at='2026-10-12T12:00:00Z'):
    return dict(id=id, title=title, sources=sources, answer=answer, claims=claims,
                expected=expected, reason=reason, error_claim_ids=error_claim_ids or [],
                review_reason=review_reason, tags=tags or [], decision_at=decision_at)


def save_family(family, cases, exposure):
    if family not in {'candidate-fit', 'preference-fit'}: raise ValueError(family)
    if len(cases) != 20 or len({c['id'] for c in cases}) != 20:
        raise ValueError('need 20 unique cases')
    counts = Counter(c['expected'] for c in cases)
    if counts != {'pass':12, 'fail':6, 'needs_review':2}: raise ValueError(counts)
    raw, normalized, gold = [], [], []
    for c in cases:
        if len({s['id'] for s in c['sources']}) != len(c['sources']): raise ValueError('duplicate source')
        if not c['claims'] or len({x['id'] for x in c['claims']}) != len(c['claims']): raise ValueError('claims')
        for x in c['claims']:
            if not x['quote'] or c['answer'].count(x['quote']) != 1: raise ValueError((c['id'],x['quote']))
        if not set(c['error_claim_ids']) <= {x['id'] for x in c['claims']}: raise ValueError('bad gold ID')
        if (c['expected']=='fail') != bool(c['error_claim_ids']): raise ValueError('gold target mismatch')
        raw.append(dict(case_id=c['id'], title=c['title'], decision_at=c['decision_at'],
                        sources=[{k:v for k,v in s.items() if k!='facts'} for s in c['sources']],
                        answer={'text':c['answer']}))
        normalized.append(dict(case_id=c['id'],
            sources=[dict(id=s['id'],facts=s['facts']) for s in c['sources']], claims=c['claims']))
        gold.append(dict(case_id=c['id'], verdict=c['expected'], reason=c['reason'],
                         error_claim_ids=c['error_claim_ids'], review_reason=c['review_reason'], tags=c['tags']))
    for folder, rows in [('raw',raw),('normalized',normalized),('gold',gold)]:
        path=ROOT/folder/(family+'.json')
        with path.open('x') as stream:
            json.dump(dict(schema='maguire-v3-new-'+folder, family=family,
                           human_approved=False, exposure=exposure, rows=rows), stream,
                      ensure_ascii=False,indent=2,allow_nan=False)
            stream.write('\n')
    print(json.dumps({'family':family,'cases':len(cases),'labels':dict(counts),
                      'claims':sum(len(c['claims']) for c in cases)}))
