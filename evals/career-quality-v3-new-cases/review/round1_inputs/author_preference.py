"""Manually authored fictional preference-fit challenge cases.

This is source-data authoring only. It does not import or call a grader.
"""
from author_support import case, claim, m, p, save_family, source


def j(n, text, *facts, kind='job_description', observed_at='2026-09-14T10:00:00Z'):
    return source(f'J{n:02}' if isinstance(n, int) else f'J{n}', text,
                  list(facts), kind=kind, observed_at=observed_at)


def pref(n, text, *facts):
    return source(f'P{n:02}', text, list(facts), kind='preference')


def c(n, title, sources, answer, claims, expected, reason, errors=None,
      review_reason=None, tags=None):
    return case(f'PF3N-{n:02}', title, sources, answer, claims, expected,
                reason, error_claim_ids=errors, review_reason=review_reason,
                tags=tags)


cases = [
    c(1, 'Published annual stipend clears a floor', [
        j(1, 'The employer publishes a personal equipment stipend of $600 per year.',
          p('employer', 'published_stipend', 'personal equipment', measure=m('amount', 'USD', 600, 600), scope={'annual': True})),
        pref(1, 'I need a personal equipment stipend of at least $500 per year.',
             p('candidate', 'personal_stipend', 'personal equipment', modality='preference_constraint',
               measure=m('amount', 'USD', 500, None), scope={'priority': 'must_have', 'annual': True})),
    ], 'The published $600 yearly equipment stipend clears your $500 minimum.', [
        claim('A', 'published $600 yearly equipment stipend',
              p('employer', 'published_stipend', 'personal equipment', measure=m('amount', 'USD', 600, 600), scope={'annual': True})),
        claim('B', 'clears your $500 minimum',
              p('employer stipend', 'compatible', 'candidate equipment minimum', modality='record_assessment',
                scope={'annual': True})),
    ], 'pass', 'The published annual amount exceeds the candidate-owned annual floor.', tags=['amount', 'bounded_inference']),

    c(2, 'Stated monthly range has a sufficient floor', [
        j(2, 'The role pays a personal workspace stipend between $450 and $650 each month.',
          p('role', 'published_stipend', 'personal workspace', measure=m('amount', 'USD', 450, 650, 'calendar_month'))),
        pref(2, 'I require at least $400 per month for a workspace stipend.',
             p('candidate', 'personal_stipend', 'personal workspace', modality='preference_constraint',
               measure=m('amount', 'USD', 400, None, 'calendar_month'), scope={'priority': 'must_have'})),
    ], 'Even the stated $450 monthly floor is above your $400 monthly requirement.', [
        claim('A', 'stated $450 monthly floor',
              p('role', 'published_stipend', 'personal workspace', measure=m('amount', 'USD', 450, 650, 'calendar_month'))),
        claim('B', 'above your $400 monthly requirement',
              p('role stipend', 'compatible', 'candidate workspace minimum', modality='record_assessment',
                scope={'basis': 'monthly_floor'})),
    ], 'pass', 'The lower bound of the stated monthly range is already above the preference floor.', tags=['range', 'bounded_inference']),

    c(3, 'Required attendance under a ceiling', [
        j(3, 'This archivist role requires one station day each week.',
          p('role', 'station_attendance', 'required', modality='requirement', measure=m('frequency', 'day', 1, 1, 'week'))),
        pref(3, 'I can attend the station at most two days per week.',
             p('candidate', 'station_attendance', 'maximum', modality='preference_constraint',
               measure=m('frequency', 'day', None, 2, 'week'), scope={'priority': 'must_have'})),
    ], 'Its one required station day per week is within your two-day ceiling.', [
        claim('A', 'one required station day per week',
              p('role', 'station_attendance', 'required', modality='requirement', measure=m('frequency', 'day', 1, 1, 'week'))),
        claim('B', 'within your two-day ceiling',
              p('role attendance', 'compatible', 'candidate station ceiling', modality='record_assessment')),
    ], 'pass', 'The required frequency is narrower than the candidate ceiling.', tags=['ceiling', 'attendance']),

    c(4, 'Narrow permitted on-call window', [
        j(4, 'The monitoring rota assigns one Saturday on-call shift each calendar month and no weekday shifts.',
          p('role', 'on_call', 'Saturday', modality='requirement', measure=m('frequency', 'shift', 1, 1, 'calendar_month'), scope={'weekday_shifts': False})),
        pref(4, 'I permit Saturday on-call once a month, but I cannot take weekday shifts.',
             p('candidate', 'on_call', 'Saturday', modality='preference_constraint',
               measure=m('frequency', 'shift', None, 1, 'calendar_month'), scope={'priority': 'must_have', 'weekday_shifts': False})),
    ], 'The Saturday-only monthly rota fits the on-call window you allow.', [
        claim('A', 'Saturday-only monthly rota',
              p('role', 'on_call', 'Saturday', modality='requirement', measure=m('frequency', 'shift', 1, 1, 'calendar_month'), scope={'weekday_shifts': False})),
        claim('B', 'fits the on-call window you allow',
              p('role rota', 'compatible', 'candidate on-call window', modality='record_assessment')),
    ], 'pass', 'The explicit Saturday-only schedule stays inside both the frequency and weekday limits.', tags=['permitted_scope', 'on_call']),

    c(5, 'Explicit revised attendance rule', [
        j(5, 'The original posting requires three station days a week.',
          p('role', 'station_attendance', 'required', modality='requirement', measure=m('frequency', 'day', 3, 3, 'week'))),
        j('05U', 'The employer update explicitly replaces the three-day rule: the role now requires one station day per week.',
          p('update J05U', 'supersedes', 'posting J05', modality='observation'),
          p('role', 'station_attendance', 'required', modality='requirement', measure=m('frequency', 'day', 1, 1, 'week')),
          kind='employer_update', observed_at='2026-09-20T10:00:00Z'),
        pref(5, 'I can attend the station no more than once per week.',
             p('candidate', 'station_attendance', 'maximum', modality='preference_constraint',
               measure=m('frequency', 'day', None, 1, 'week'), scope={'priority': 'must_have'})),
    ], 'The replacement rule requires one station day weekly, meeting your cap.', [
        claim('A', 'replacement rule requires one station day weekly',
              p('role', 'station_attendance', 'required', modality='requirement', measure=m('frequency', 'day', 1, 1, 'week'))),
        claim('B', 'meeting your cap', p('role attendance', 'compatible', 'candidate station ceiling', modality='record_assessment')),
    ], 'pass', 'The employer explicitly replaced the old three-day rule with a one-day rule.', tags=['rule_change', 'attendance']),

    c(6, 'Remote permission after finite onboarding', [
        j(6, 'The role is on site for its first 30 days; remote work is permitted afterward.',
          p('role', 'station_attendance', 'on site', modality='requirement', time={'first_days': 30}),
          p('role', 'remote_work', 'permitted', modality='permission', time={'after_day': 30})),
        pref(6, 'I can work on site for up to 30 onboarding days if remote work is permitted afterward.',
             p('candidate', 'remote_work', 'after onboarding', modality='preference_constraint',
               scope={'priority': 'must_have', 'condition': 'on_site_first_30_days'})),
    ], 'The stated 30-day on-site period matches your exception, with remote work permitted afterward.', [
        claim('A', '30-day on-site period matches your exception',
              p('role onboarding', 'compatible', 'candidate 30-day exception', modality='record_assessment', time={'first_days': 30})),
        claim('B', 'remote work permitted afterward',
              p('role', 'remote_work', 'permitted', modality='permission', time={'after_day': 30})),
    ], 'pass', 'The employer expressly allows remote work after an on-site period equal to the candidate exception.', tags=['condition', 'remote_work']),

    c(7, 'Unsettled allowance stays unresolved', [
        j(7, 'The employer says it plans a learning allowance but has not decided its amount.',
          p('employer', 'learning_allowance', 'amount undecided', modality='observation')),
        pref(7, 'I need a confirmed learning allowance of at least $1,000 a year.',
             p('candidate', 'learning_allowance', 'confirmed minimum', modality='preference_constraint',
               measure=m('amount', 'USD', 1000, None), scope={'priority': 'must_have', 'annual': True})),
    ], 'The employer has not decided the allowance amount, so your $1,000 requirement remains unresolved.', [
        claim('A', 'employer has not decided the allowance amount',
              p('employer', 'learning_allowance', 'amount undecided')),
        claim('B', 'your $1,000 requirement remains unresolved',
              p('role allowance', 'compatible', 'candidate allowance minimum', modality='record_assessment',
                scope={'status': 'unresolved'})),
    ], 'pass', 'An undecided amount cannot establish whether the stated minimum is met.', tags=['uncertainty', 'caution']),

    c(8, 'Conditional remote fit', [
        j(8, 'The exact remote schedule will be written into the offer; no weekly count is set in the posting.',
          p('role', 'written_offer', 'sets remote schedule', modality='commitment'),
          p('posting', 'remote_work', 'weekly count unset', modality='observation')),
        pref(8, 'I require at least three remote days per week.',
             p('candidate', 'remote_work', 'minimum', modality='preference_constraint',
               measure=m('frequency', 'day', 3, None, 'week'), scope={'priority': 'must_have'})),
    ], 'If the written offer confirms three remote days weekly, this preference is met.', [
        claim('A', 'written offer confirms three remote days weekly',
              p('role', 'written_offer', 'three remote days', modality='possibility',
                measure=m('frequency', 'day', 3, 3, 'week'), scope={'condition': 'if_offer_confirms'}), stance='conditional'),
        claim('B', 'this preference is met',
              p('role schedule', 'compatible', 'candidate remote minimum', modality='record_assessment',
                scope={'condition': 'if_offer_confirms_three_days'}), stance='conditional'),
    ], 'pass', 'The answer makes satisfaction conditional on a future written term and does not claim the term exists now.', tags=['conditional_advice', 'remote_work']),

    c(9, 'Caption provision pending', [
        j(9, 'The employer says live captions are pending procurement and are not yet available.',
          p('role', 'live_captions', 'available now', polarity='negative', modality='observation'),
          p('role', 'live_captions', 'pending procurement', modality='observation')),
        pref(9, 'Live captions in team meetings are a must-have for me.',
             p('candidate', 'live_captions', 'team meetings', modality='preference_constraint',
               scope={'priority': 'must_have'})),
    ], 'Captions are pending; ask for confirmation before treating the meeting requirement as met.', [
        claim('A', 'Captions are pending', p('role', 'live_captions', 'pending procurement')),
        claim('B', 'ask for confirmation before treating the meeting requirement as met',
              p('candidate', 'compatible', 'role meeting captions', modality='evaluation_instruction',
                scope={'condition': 'confirmation_required'}), stance='recommended_as_fact'),
    ], 'pass', 'The instruction preserves the explicit pending status and does not count unprovided captions as a fit.', tags=['uncertainty', 'positive_advice']),

    c(10, 'Question with two supported premises', [
        j(10, 'The employer publishes an annual learning allowance of $900.',
          p('employer', 'learning_allowance', 'annual', measure=m('amount', 'USD', 900, 900), scope={'annual': True})),
        pref(10, 'I want an annual learning allowance of at least $700; that is a nice-to-have.',
             p('candidate', 'learning_allowance', 'minimum', modality='preference_constraint',
               measure=m('amount', 'USD', 700, None), scope={'priority': 'nice_to_have', 'annual': True})),
    ], 'The listing states $900 annually and your preferred floor is $700; would you still ask which courses qualify?', [
        claim('A', 'listing states $900 annually',
              p('employer', 'learning_allowance', 'annual', measure=m('amount', 'USD', 900, 900), scope={'annual': True})),
        claim('B', 'your preferred floor is $700',
              p('candidate', 'learning_allowance', 'minimum', modality='preference_constraint',
                measure=m('amount', 'USD', 700, None), scope={'priority': 'nice_to_have', 'annual': True})),
        claim('C', 'would you still ask which courses qualify?',
              p('candidate', 'learning_allowance', 'eligible courses', modality='evaluation_instruction'), stance='question'),
    ], 'pass', 'The two premises are explicit and the question makes no claim about eligible courses.', tags=['nonassertive', 'premise_split']),

    c(11, 'Permitted remote schedule with approval caveat', [
        j(11, 'Staff may request up to four remote days per week; a manager approves each schedule.',
          p('role', 'remote_work', 'up to four days', modality='permission',
            measure=m('frequency', 'day', 0, 4, 'week'), scope={'condition': 'manager_approval'})),
        pref(11, 'I would like two remote days weekly, if the manager approves; this is a nice-to-have.',
             p('candidate', 'remote_work', 'two days', modality='preference_constraint',
               measure=m('frequency', 'day', 2, 2, 'week'), scope={'priority': 'nice_to_have', 'condition': 'manager_approval'})),
    ], 'Two remote days fit the stated four-day limit, subject to manager approval.', [
        claim('A', 'Two remote days fit the stated four-day limit',
              p('role remote permission', 'compatible', 'candidate two-day wish', modality='record_assessment',
                scope={'condition': 'manager_approval'})),
        claim('B', 'subject to manager approval',
              p('role', 'remote_work', 'manager approval', modality='requirement')),
    ], 'pass', 'Two is within the permitted maximum, and the answer preserves the approval condition.', tags=['permission', 'narrower_scope']),

    c(12, 'Bounded demo schedule', [
        j(12, 'The only required training demos are Wednesdays from 15:00 to 16:00 local time.',
          p('role', 'training_demo', 'Wednesday 15:00-16:00', modality='requirement',
            scope={'required_demos_only': True})),
        pref(12, 'I cannot attend required training demos after 18:00 local time.',
             p('candidate', 'training_demo', 'after 18:00', modality='preference_constraint',
               polarity='negative', scope={'priority': 'must_have'})),
    ], 'The specified Wednesday training demos end before your 18:00 cutoff.', [
        claim('A', 'Wednesday training demos end before your 18:00 cutoff',
              p('role demos', 'compatible', 'candidate demo cutoff', modality='record_assessment',
                scope={'required_demos_only': True})),
    ], 'pass', 'The statement is limited to the only required demos, whose stated end time is 16:00.', tags=['time_bound', 'narrower_scope']),

    c(13, 'Permission inflated into a guarantee', [
        j(13, 'Employees may request remote days, subject to manager approval; the posting specifies no guaranteed number.',
          p('role', 'remote_work', 'requestable', modality='permission', scope={'condition': 'manager_approval'}),
          p('role', 'remote_work', 'guaranteed count', polarity='negative')),
        pref(13, 'I require three guaranteed remote days per week.',
             p('candidate', 'remote_work', 'guaranteed minimum', modality='preference_constraint',
               measure=m('frequency', 'day', 3, None, 'week'), scope={'priority': 'must_have'})),
    ], 'Remote requests are allowed, so your three remote days are guaranteed.', [
        claim('A', 'Remote requests are allowed',
              p('role', 'remote_work', 'requestable', modality='permission', scope={'condition': 'manager_approval'})),
        claim('B', 'your three remote days are guaranteed',
              p('role', 'remote_work', 'three days', modality='guarantee',
                measure=m('frequency', 'day', 3, 3, 'week'))),
    ], 'fail', 'Permission to request does not guarantee approval or three days.', ['B'], tags=['guarantee_inflation']),

    c(14, 'Unofficial note given rule authority', [
        j(14, 'The job posting requires two station days each week.',
          p('role', 'station_attendance', 'required', modality='requirement', measure=m('frequency', 'day', 2, 2, 'week'))),
        j('14N', 'An informal staff note says some teams might try fewer station days. It does not amend the posting.',
          p('staff note J14N', 'supersedes', 'posting J14', polarity='negative'),
          p('some teams', 'station_attendance', 'fewer days trial', modality='possibility'),
          kind='employer_update', observed_at='2026-09-21T10:00:00Z'),
        pref(14, 'I can attend the station at most once a week.',
             p('candidate', 'station_attendance', 'maximum', modality='preference_constraint',
               measure=m('frequency', 'day', None, 1, 'week'), scope={'priority': 'must_have'})),
    ], 'The staff note replaces the two-day rule, so the role meets your one-day cap.', [
        claim('A', 'staff note replaces the two-day rule',
              p('staff note J14N', 'supersedes', 'posting J14')),
        claim('B', 'role meets your one-day cap',
              p('role attendance', 'compatible', 'candidate one-day ceiling', modality='record_assessment')),
    ], 'fail', 'The note explicitly lacks authority to amend the two-day requirement.', ['A', 'B'], tags=['authority', 'rule_change']),

    c(15, 'Required on-call reversed', [
        j(15, 'Every support engineer takes one overnight on-call shift each week.',
          p('role', 'on_call', 'overnight', modality='requirement', measure=m('frequency', 'shift', 1, 1, 'week'))),
        pref(15, 'I cannot take overnight on-call shifts.',
             p('candidate', 'on_call', 'overnight', modality='preference_constraint',
               polarity='negative', scope={'priority': 'must_have'})),
    ], 'The role has no overnight on-call duty and satisfies your constraint.', [
        claim('A', 'no overnight on-call duty',
              p('role', 'on_call', 'overnight', modality='requirement', polarity='negative')),
        claim('B', 'satisfies your constraint',
              p('role on-call', 'compatible', 'candidate overnight ban', modality='record_assessment')),
    ], 'fail', 'The posting explicitly requires the duty that the candidate excludes.', ['A', 'B'], tags=['polarity', 'duty']),

    c(16, 'Candidate request misattributed to employer', [
        j(16, 'The interview platform has optional live captions, but the employer has not committed to enabling them for team meetings.',
          p('meeting platform', 'live_captions', 'optional feature', modality='ability'),
          p('employer', 'live_captions', 'enabled for team meetings', polarity='negative', modality='commitment')),
        pref(16, 'I require employer-enabled live captions for team meetings.',
             p('candidate', 'live_captions', 'team meetings', modality='preference_constraint',
               scope={'priority': 'must_have'})),
    ], 'The platform supports captions, and the employer will enable them in every team meeting.', [
        claim('A', 'platform supports captions',
              p('meeting platform', 'live_captions', 'optional feature', modality='ability')),
        claim('B', 'employer will enable them in every team meeting',
              p('employer', 'live_captions', 'enabled', modality='commitment', scope={'quantifier': 'all', 'meeting_type': 'team'})),
    ], 'fail', 'A platform feature and candidate requirement do not establish an employer commitment.', ['B'], tags=['attribution', 'commitment']),

    c(17, 'Annual amount treated as monthly', [
        j(17, 'The personal internet stipend is $900 per year.',
          p('employer', 'published_stipend', 'personal internet', measure=m('amount', 'USD', 900, 900), scope={'annual': True})),
        pref(17, 'I need at least $200 a month for an internet stipend.',
             p('candidate', 'personal_stipend', 'personal internet', modality='preference_constraint',
               measure=m('amount', 'USD', 200, None, 'calendar_month'), scope={'priority': 'must_have'})),
    ], 'The $900 stipend meets your $200 monthly minimum.', [
        claim('A', '$900 stipend',
              p('employer', 'published_stipend', 'personal internet', measure=m('amount', 'USD', 900, 900), scope={'annual': True})),
        claim('B', 'meets your $200 monthly minimum',
              p('role stipend', 'compatible', 'candidate monthly internet minimum', modality='record_assessment')),
    ], 'fail', 'The $900 is annual, only $75 per month if evenly spread, below the $200 monthly minimum.', ['B'], tags=['time_scale', 'amount']),

    c(18, 'Expense category expanded', [
        j(18, 'The $1,200 annual learning allowance reimburses certification exam fees only; conference travel is excluded.',
          p('employer', 'learning_allowance', 'certification exam fees', modality='permission',
            measure=m('amount', 'USD', 0, 1200), scope={'annual': True}),
          p('employer', 'learning_allowance', 'conference travel', modality='permission', polarity='negative')),
        pref(18, 'My must-have is at least $800 annually for conference travel.',
             p('candidate', 'learning_allowance', 'conference travel', modality='preference_constraint',
               measure=m('amount', 'USD', 800, None), scope={'priority': 'must_have', 'annual': True})),
    ], 'The allowance is $1,200 for exams, so it can cover your conference travel.', [
        claim('A', 'allowance is $1,200 for exams',
              p('employer', 'learning_allowance', 'certification exam fees', modality='permission',
                measure=m('amount', 'USD', 0, 1200), scope={'annual': True})),
        claim('B', 'it can cover your conference travel',
              p('employer', 'learning_allowance', 'conference travel', modality='permission')),
    ], 'fail', 'The stated allowance expressly excludes conference travel.', ['B'], tags=['scope', 'expense_category']),

    c(19, 'Offer language admits two readings', [
        j(19, 'The posting says two remote days may be agreed after a trial period.',
          p('role', 'remote_work', 'two days after trial', modality='possibility',
            measure=m('frequency', 'day', 2, 2, 'week'), scope={'condition': 'agreement_after_trial'})),
        pref(19, 'I require at least two remote days weekly after any trial.',
             p('candidate', 'remote_work', 'minimum after trial', modality='preference_constraint',
               measure=m('frequency', 'day', 2, None, 'week'), scope={'priority': 'must_have'})),
    ], 'The role offers two remote days after the trial.', [
        claim('A', 'offers two remote days after the trial', readings=[
            p('role', 'remote_work', 'two days after trial', modality='possibility',
              measure=m('frequency', 'day', 2, 2, 'week'), scope={'condition': 'agreement_after_trial'}),
            p('role', 'remote_work', 'two days after trial', modality='guarantee',
              measure=m('frequency', 'day', 2, 2, 'week')),
        ]),
    ], 'needs_review', 'Offers could preserve the contingent option or imply a firm benefit; the fragment does not decide which.',
      review_reason='Clarify whether offers means possible agreement or guaranteed post-trial schedule.', tags=['modality_ambiguity']),

    c(20, 'Caption availability admits two readings', [
        j(20, 'Live captions can be enabled for team meetings when an attendee requests them in advance.',
          p('role', 'live_captions', 'team meetings', modality='permission',
            scope={'condition': 'advance_request'})),
        pref(20, 'I require live captions in every team meeting.',
             p('candidate', 'live_captions', 'team meetings', modality='preference_constraint',
               scope={'priority': 'must_have', 'quantifier': 'all'})),
    ], 'Live captions are available for your team meetings.', [
        claim('A', 'Live captions are available for your team meetings', readings=[
            p('role', 'live_captions', 'team meetings', modality='permission',
              scope={'condition': 'advance_request'}),
            p('role', 'live_captions', 'team meetings', modality='guarantee',
              scope={'quantifier': 'all'}),
        ]),
    ], 'needs_review', 'Available may mean requestable under the stated condition or routinely supplied at every meeting.',
      review_reason='Clarify whether available refers to requestable captions or unconditional provision.', tags=['condition_ambiguity']),
]


if __name__ == '__main__':
    save_family('preference-fit', cases,
                {'author': 'preference-fit worker', 'basis': 'manual fictional authoring',
                 'prior_eval_access': False, 'checker_access': False,
                 'runtime_predictions_seen': False})
