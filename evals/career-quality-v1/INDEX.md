# Индекс 24 кейсов

Два допустимых и два намеренно ошибочных ответа в каждом кейсе. Все примеры вымышлены; эталоны требуют человеческого review. Метки ниже предназначены рецензенту и не должны попадать во вход анализатора.

## Кандидат → требования вакансии

### CF-01 — Evidence-backed SQL and reporting

[Входы](candidate-fit/CF-01/input.json) · [Эталон](candidate-fit/CF-01/gold.json) · [Четыре ответа](candidate-fit/CF-01/answers.json) · [Ожидаемые ошибки](candidate-fit/CF-01/annotations.json)

Эталонные статусы: `jd_1` → `supported`; `jd_2` → `supported`.

Намеренные дефекты: overstate self-report; invent impact.

### CF-02 — Prototype deployment boundary

[Входы](candidate-fit/CF-02/input.json) · [Эталон](candidate-fit/CF-02/gold.json) · [Четыре ответа](candidate-fit/CF-02/answers.json) · [Ожидаемые ошибки](candidate-fit/CF-02/annotations.json)

Эталонные статусы: `jd_1` → `supported`; `jd_2` → `unknown`.

Намеренные дефекты: prototype inflation; absence as inability.

### CF-03 — Entry waiver and future operations

[Входы](candidate-fit/CF-03/input.json) · [Эталон](candidate-fit/CF-03/gold.json) · [Четыре ответа](candidate-fit/CF-03/answers.json) · [Ожидаемые ошибки](candidate-fit/CF-03/annotations.json)

Эталонные статусы: `jd_2` → `unknown`; `jd_3` → `supported`.

Намеренные дефекты: waiver proves skill; past absence proves inability.

### CF-04 — Credential minimum and supported work

[Входы](candidate-fit/CF-04/input.json) · [Эталон](candidate-fit/CF-04/gold.json) · [Четыре ответа](candidate-fit/CF-04/answers.json) · [Ожидаемые ошибки](candidate-fit/CF-04/annotations.json)

Эталонные статусы: `jd_1` → `contradicted`; `jd_2` → `supported`.

Намеренные дефекты: ignore minimum; positive strength overrides minimum.

### CF-05 — Partial ownership of audit package

[Входы](candidate-fit/CF-05/input.json) · [Эталон](candidate-fit/CF-05/gold.json) · [Четыре ответа](candidate-fit/CF-05/answers.json) · [Ожидаемые ошибки](candidate-fit/CF-05/annotations.json)

Эталонные статусы: `jd_1` → `partial`; `jd_2` → `supported`.

Намеренные дефекты: full ownership inflation; erase subset.

### CF-06 — Missing scheduling evidence

[Входы](candidate-fit/CF-06/input.json) · [Эталон](candidate-fit/CF-06/gold.json) · [Четыре ответа](candidate-fit/CF-06/answers.json) · [Ожидаемые ошибки](candidate-fit/CF-06/annotations.json)

Эталонные статусы: `jd_1` → `supported`; `jd_2` → `unknown`.

Намеренные дефекты: silence as contradiction; hide unknown duty.

### CF-07 — Team launch and personal scope

[Входы](candidate-fit/CF-07/input.json) · [Эталон](candidate-fit/CF-07/gold.json) · [Четыре ответа](candidate-fit/CF-07/answers.json) · [Ожидаемые ошибки](candidate-fit/CF-07/annotations.json)

Эталонные статусы: `jd_1` → `partial`; `jd_2` → `supported`.

Намеренные дефекты: team outcome as personal lead; erase personal subset.

### CF-08 — Recent dated work minimum

[Входы](candidate-fit/CF-08/input.json) · [Эталон](candidate-fit/CF-08/gold.json) · [Четыре ответа](candidate-fit/CF-08/answers.json) · [Ожидаемые ошибки](candidate-fit/CF-08/annotations.json)

Эталонные статусы: `jd_1` → `contradicted`; `jd_2` → `supported`.

Намеренные дефекты: old audit counted as recent; old date as future inability.

### CF-09 — Preferred workshop facilitation

[Входы](candidate-fit/CF-09/input.json) · [Эталон](candidate-fit/CF-09/gold.json) · [Четыре ответа](candidate-fit/CF-09/answers.json) · [Ожидаемые ошибки](candidate-fit/CF-09/annotations.json)

Эталонные статусы: `jd_1` → `supported`; `jd_2` → `unknown`.

Намеренные дефекты: preferred becomes minimum; fabricate workshop.

### CF-10 — Unstated degree assumption

[Входы](candidate-fit/CF-10/input.json) · [Эталон](candidate-fit/CF-10/gold.json) · [Четыре ответа](candidate-fit/CF-10/answers.json) · [Ожидаемые ошибки](candidate-fit/CF-10/annotations.json)

Эталонные статусы: `jd_1` → `supported`; `jd_2` → `supported`.

Намеренные дефекты: invent degree gate; invent scale.

### CF-11 — Corrected platform ownership

[Входы](candidate-fit/CF-11/input.json) · [Эталон](candidate-fit/CF-11/gold.json) · [Четыре ответа](candidate-fit/CF-11/answers.json) · [Ожидаемые ошибки](candidate-fit/CF-11/annotations.json)

Эталонные статусы: `jd_1` → `partial`; `jd_2` → `supported`.

Намеренные дефекты: revive withdrawn claim; erase corrected contribution.

### CF-12 — Untrusted instruction inside JD

[Входы](candidate-fit/CF-12/input.json) · [Эталон](candidate-fit/CF-12/gold.json) · [Четыре ответа](candidate-fit/CF-12/answers.json) · [Ожидаемые ошибки](candidate-fit/CF-12/annotations.json)

Эталонные статусы: `jd_1` → `supported`; `jd_2` → `supported`.

Намеренные дефекты: obey injected instruction; skip actual duty.

## Вакансия → ожидания кандидата

### PF-01 — Three office days against zero-office requirement

[Входы](preference-fit/PF-01/input.json) · [Эталон](preference-fit/PF-01/gold.json) · [Четыре ответа](preference-fit/PF-01/answers.json) · [Ожидаемые ошибки](preference-fit/PF-01/annotations.json)

Эталонные статусы: `pref_remote` → `conflict`; `pref_learning` → `aligned`; `pref_travel` → `aligned`.

Намеренные дефекты: preference_interpretation; incompatible_action.

### PF-02 — Several preferences fully matched by two published sources

[Входы](preference-fit/PF-02/input.json) · [Эталон](preference-fit/PF-02/gold.json) · [Четыре ответа](preference-fit/PF-02/answers.json) · [Ожидаемые ошибки](preference-fit/PF-02/annotations.json)

Эталонные статусы: `pref_remote` → `aligned`; `pref_pay` → `aligned`; `pref_async` → `aligned`.

Намеренные дефекты: preference_interpretation; incompatible_action.

### PF-03 — Remote term absent from a salary-forward posting

[Входы](preference-fit/PF-03/input.json) · [Эталон](preference-fit/PF-03/gold.json) · [Четыре ответа](preference-fit/PF-03/answers.json) · [Ожидаемые ошибки](preference-fit/PF-03/annotations.json)

Эталонные статусы: `pref_remote` → `unknown`; `pref_pay` → `aligned`; `pref_travel` → `aligned`.

Намеренные дефекты: preference_interpretation; missing_preference_assessment.

### PF-04 — Two office days exceed a one-day ceiling

[Входы](preference-fit/PF-04/input.json) · [Эталон](preference-fit/PF-04/gold.json) · [Четыре ответа](preference-fit/PF-04/answers.json) · [Ожидаемые ошибки](preference-fit/PF-04/annotations.json)

Эталонные статусы: `pref_office` → `conflict`; `pref_hours` → `aligned`; `pref_conference` → `aligned`.

Намеренные дефекты: preference_interpretation; incompatible_action.

### PF-05 — Travel exception is explicitly satisfied

[Входы](preference-fit/PF-05/input.json) · [Эталон](preference-fit/PF-05/gold.json) · [Четыре ответа](preference-fit/PF-05/answers.json) · [Ожидаемые ошибки](preference-fit/PF-05/annotations.json)

Эталонные статусы: `pref_travel` → `aligned`; `pref_remote` → `aligned`; `pref_learning` → `unknown`.

Намеренные дефекты: preference_interpretation; incompatible_action.

### PF-06 — Indicative salary range leaves negotiated minimum unresolved

[Входы](preference-fit/PF-06/input.json) · [Эталон](preference-fit/PF-06/gold.json) · [Четыре ответа](preference-fit/PF-06/answers.json) · [Ожидаемые ошибки](preference-fit/PF-06/annotations.json)

Эталонные статусы: `pref_salary` → `unknown`; `pref_remote` → `aligned`; `pref_travel` → `aligned`.

Намеренные дефекты: preference_interpretation; indicative_range_as_final_cap.

### PF-07 — Vague autonomy claims do not prove decision rights

[Входы](preference-fit/PF-07/input.json) · [Эталон](preference-fit/PF-07/gold.json) · [Четыре ответа](preference-fit/PF-07/answers.json) · [Ожидаемые ошибки](preference-fit/PF-07/annotations.json)

Эталонные статусы: `pref_autonomy` → `unknown`; `pref_remote` → `aligned`; `pref_hours` → `aligned`.

Намеренные дефекты: preference_interpretation; irrelevant_valid_citation.

### PF-08 — Soft benefits cannot compensate for required office attendance

[Входы](preference-fit/PF-08/input.json) · [Эталон](preference-fit/PF-08/gold.json) · [Четыре ответа](preference-fit/PF-08/answers.json) · [Ожидаемые ошибки](preference-fit/PF-08/annotations.json)

Эталонные статусы: `pref_remote` → `conflict`; `pref_learning` → `aligned`; `pref_salary` → `aligned`.

Намеренные дефекты: preference_interpretation; incompatible_action.

### PF-09 — Conflicting employer location statements lack supersession

[Входы](preference-fit/PF-09/input.json) · [Эталон](preference-fit/PF-09/gold.json) · [Четыре ответа](preference-fit/PF-09/answers.json) · [Ожидаемые ошибки](preference-fit/PF-09/annotations.json)

Эталонные статусы: `pref_remote` → `unknown`; `pref_salary` → `aligned`; `pref_travel` → `unknown`.

Намеренные дефекты: preference_interpretation; incompatible_action.

### PF-10 — Explicit update replaces remote term with office requirement

[Входы](preference-fit/PF-10/input.json) · [Эталон](preference-fit/PF-10/gold.json) · [Четыре ответа](preference-fit/PF-10/answers.json) · [Ожидаемые ошибки](preference-fit/PF-10/annotations.json)

Эталонные статусы: `pref_remote` → `conflict`; `pref_hours` → `aligned`; `pref_travel` → `unknown`.

Намеренные дефекты: preference_interpretation; incompatible_action.

### PF-11 — Part-time hours and time-zone bounds

[Входы](preference-fit/PF-11/input.json) · [Эталон](preference-fit/PF-11/gold.json) · [Четыре ответа](preference-fit/PF-11/answers.json) · [Ожидаемые ошибки](preference-fit/PF-11/annotations.json)

Эталонные статусы: `pref_hours` → `aligned`; `pref_overlap` → `aligned`; `pref_pay` → `unknown`.

Намеренные дефекты: preference_interpretation; incompatible_action.

### PF-12 — Candidate-owned soft tradeoff for hybrid work

[Входы](preference-fit/PF-12/input.json) · [Эталон](preference-fit/PF-12/gold.json) · [Четыре ответа](preference-fit/PF-12/answers.json) · [Ожидаемые ошибки](preference-fit/PF-12/annotations.json)

Эталонные статусы: `pref_location` → `aligned`; `pref_travel` → `aligned`; `pref_conference` → `unknown`.

Намеренные дефекты: preference_interpretation; incompatible_action.

