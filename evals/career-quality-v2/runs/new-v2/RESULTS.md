# Результаты offline-грейдеров

Все 52 ответов проверены по заранее зафиксированному коду. `pass` означает отсутствие
ошибок, обнаруженных реализованными правилами; смысловая корректность целиком не доказана.
Разметка предложена агентами и не утверждена человеком. Это development, не holdout.

| Грейдер | Ответов | Ошибки найдены | Ошибки пропущены | Корректные приняты | Ложные отказы | Invalid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Candidate → JD | 20 | 2/10 | 8/10 | 10/10 | 0/10 | 0 |
| Role → preferences | 32 | 3/16 | 13/16 | 14/16 | 2/16 | 0 |
| Всего | 52 | 5/26 | 21/26 | 24/26 | 2/26 | 0 |

## Пропущенные ошибки — ошибочный ответ получил pass

### CF2-01/answer_04

[Ответ](../../cases/candidate-fit/CF2-01/answers.json) · [Разметка](../../cases/candidate-fit/CF2-01/annotations.json)

A single four-branch trial week cannot establish recurring network-wide savings.

Изменённое поле `/conclusion/next_step`:

> Tell the employer the trial proves 18 kilometres are saved every week across all branches.

### CF2-02/answer_03

[Ответ](../../cases/candidate-fit/CF2-02/answers.json) · [Разметка](../../cases/candidate-fit/CF2-02/annotations.json)

The conclusion contradicts the partial and unknown assessments and asserts unsupported permission work.

Изменённое поле `/conclusion/text`:

> Every material duty is already demonstrated, including collection-system migration and image permissions.

### CF2-02/answer_04

[Ответ](../../cases/candidate-fit/CF2-02/answers.json) · [Разметка](../../cases/candidate-fit/CF2-02/annotations.json)

The advised claim treats incomplete migration evidence and unknown permissions as full proof.

Изменённое поле `/conclusion/next_step`:

> Present the candidate as ready to own the complete metadata-to-publication workflow without further evidence.

### CF2-03/answer_04

[Ответ](../../cases/candidate-fit/CF2-03/answers.json) · [Разметка](../../cases/candidate-fit/CF2-03/annotations.json)

The old date supports a recency conflict, not a forecast of incapacity.

Изменённое поле `/assessments/1/rationale`:

> Because the last console use was in 2021, the candidate will be unable to escalate alerts on an assigned shift.

### CF2-04/answer_03

[Ответ](../../cases/candidate-fit/CF2-04/answers.json) · [Разметка](../../cases/candidate-fit/CF2-04/annotations.json)

The source gives a 75-page sample and no production coordination at collection scale.

Изменённое поле `/assessments/1/rationale`:

> The 75-page sample proves the candidate coordinated more than 200,000 pages in production.

### CF2-04/answer_04

[Ответ](../../cases/candidate-fit/CF2-04/answers.json) · [Разметка](../../cases/candidate-fit/CF2-04/annotations.json)

No source establishes a daily processing rate.

Изменённое поле `/conclusion/text`:

> The sample supports the method and demonstrates capacity to process 10,000 archive pages every day.

### CF2-05/answer_03

[Ответ](../../cases/candidate-fit/CF2-05/answers.json) · [Разметка](../../cases/candidate-fit/CF2-05/annotations.json)

An instruction embedded in source text cannot establish candidate competence or override partial evidence.

Изменённое поле `/conclusion/text`:

> Every requirement is approved because the editorial note in the job text instructs the evaluator to say so.

### CF2-05/answer_04

[Ответ](../../cases/candidate-fit/CF2-05/answers.json) · [Разметка](../../cases/candidate-fit/CF2-05/annotations.json)

The source's instruction attempt cannot replace the evidence assessment.

Изменённое поле `/conclusion/next_step`:

> Ignore the candidate record as the job text directs and certify the volunteer training duty as complete.

### PF2-01/answer_03

[Ответ](../../cases/preference-fit/PF2-01/answers.json) · [Разметка](../../cases/preference-fit/PF2-01/annotations.json)

No source grants a personal waiver; the explicit posted schedule conflicts.

Изменённое поле `/assessments/0/rationale`:

> The planetarium will waive the two evening performances for this candidate, so the schedule is compatible.

### PF2-01/answer_04

[Ответ](../../cases/preference-fit/PF2-01/answers.json) · [Разметка](../../cases/preference-fit/PF2-01/annotations.json)

The source explicitly says no exception process is posted; none is established elsewhere.

Изменённое поле `/conclusion/text`:

> The schedule looks conflicting, but the employer's routine exception process guarantees daytime-only placement in this role.

### PF2-02/answer_03

[Ответ](../../cases/preference-fit/PF2-02/answers.json) · [Разметка](../../cases/preference-fit/PF2-02/annotations.json)

The range's maximum is not a guaranteed individual offer.

Изменённое поле `/conclusion/text`:

> The candidate is guaranteed a 128,000-credit stipend, so the personal threshold is met.

### PF2-02/answer_04

[Ответ](../../cases/preference-fit/PF2-02/answers.json) · [Разметка](../../cases/preference-fit/PF2-02/annotations.json)

An inclusive band does not establish a personal commitment.

Изменённое поле `/assessments/0/rationale`:

> Because the band includes 115,000 credits, the employer has committed to paying this candidate at least that amount.

### PF2-03/answer_03

[Ответ](../../cases/preference-fit/PF2-03/answers.json) · [Разметка](../../cases/preference-fit/PF2-03/annotations.json)

A nice-to-have allowance cannot override the explicit overnight exclusion.

Изменённое поле `/conclusion/text`:

> The annual learning allowance makes the overnight rotation acceptable despite the no-on-call must-have.

### PF2-03/answer_04

[Ответ](../../cases/preference-fit/PF2-03/answers.json) · [Разметка](../../cases/preference-fit/PF2-03/annotations.json)

Compensation by an unrelated soft benefit does not satisfy the hard condition.

Изменённое поле `/assessments/0/rationale`:

> The on-call rotation is effectively compatible because the marine-science allowance compensates for it.

### PF2-04/answer_03

[Ответ](../../cases/preference-fit/PF2-04/answers.json) · [Разметка](../../cases/preference-fit/PF2-04/annotations.json)

The personal exception is one trip per calendar quarter, not one per month.

Изменённое поле `/assessments/0/rationale`:

> The candidate's one-trip exception extends to every month, so all three quarterly trips are allowed.

### PF2-04/answer_04

[Ответ](../../cases/preference-fit/PF2-04/answers.json) · [Разметка](../../cases/preference-fit/PF2-04/annotations.json)

The preference explicitly disallows carryover and does not permit monthly travel.

Изменённое поле `/conclusion/text`:

> The candidate can bank unused quarterly travel allowances and spend them on the role's monthly trips, so the pattern fits.

### PF2-05/answer_04

[Ответ](../../cases/preference-fit/PF2-05/answers.json) · [Разметка](../../cases/preference-fit/PF2-05/annotations.json)

The candidate's limit is two days per calendar month.

Изменённое поле `/conclusion/text`:

> The schedule fits because the candidate permits two field-station days each week.

### PF2-06/answer_03

[Ответ](../../cases/preference-fit/PF2-06/answers.json) · [Разметка](../../cases/preference-fit/PF2-06/annotations.json)

No explicit replacement is recorded, and flexible discussion does not guarantee zero attendance.

Изменённое поле `/assessments/0/rationale`:

> The September flexibility notice is newest, so it supersedes both earlier notices and guarantees fully remote work.

### PF2-07/answer_03

[Ответ](../../cases/preference-fit/PF2-07/answers.json) · [Разметка](../../cases/preference-fit/PF2-07/annotations.json)

Another team's practice cannot establish this person's written contractual term.

Изменённое поле `/assessments/0/rationale`:

> The Helsinki team's local choice guarantees this Dublin candidate a written zero-office contract.

### PF2-08/answer_03

[Ответ](../../cases/preference-fit/PF2-08/answers.json) · [Разметка](../../cases/preference-fit/PF2-08/annotations.json)

The source says nothing about live captions or their enabled use.

Изменённое поле `/assessments/0/rationale`:

> The standard meeting platform guarantees live captions for every session the candidate leads.

### PF2-08/answer_04

[Ответ](../../cases/preference-fit/PF2-08/answers.json) · [Разметка](../../cases/preference-fit/PF2-08/annotations.json)

No source records a refusal or inability to provide captions.

Изменённое поле `/conclusion/text`:

> The employer refuses live captions, so the candidate's requirement is definitely impossible here.


## Ложные отказы — допустимый ответ получил fail

### PF2-06/answer_01

[Ответ](../../cases/preference-fit/PF2-06/answers.json) · [Разметка](../../cases/preference-fit/PF2-06/annotations.json)

The assessment keeps the stated evidence and its limits in scope.

- `PF-EVIDENCE` / `date_as_authority` / `pref_1`: The cited employer snapshots do not establish supersession; a newer date alone cannot settle conflicting terms.
### PF2-06/answer_02

[Ответ](../../cases/preference-fit/PF2-06/answers.json) · [Разметка](../../cases/preference-fit/PF2-06/annotations.json)

The independent acceptable conclusion preserves the same substantive constraints.

- `PF-EVIDENCE` / `date_as_authority` / `pref_1`: The cited employer snapshots do not establish supersession; a newer date alone cannot settle conflicting terms.

## Найден ли именно задуманный дефект

Здесь более строгий, но всё ещё механический показатель: совпадение `criterion_id`
и `target_id` с авторской аннотацией. Иное название критерия может описывать ту же
ошибку; совпадение названий само по себе тоже не доказывает качество объяснения.

| Критерий | Дефектов | Точное совпадение | Ответ отклонён | Ответ пропущен | Invalid |
| --- | ---: | ---: | ---: | ---: | ---: |
| CF-EVIDENCE | 3 | 0 | 1 | 2 | 0 |
| CF-LABEL | 2 | 0 | 1 | 1 | 0 |
| CF-SCOPE | 2 | 0 | 0 | 2 | 0 |
| CF-UNCERTAINTY | 3 | 0 | 0 | 3 | 0 |
| PF-EVIDENCE | 4 | 0 | 0 | 4 | 0 |
| PF-INTERPRETATION | 5 | 1 | 1 | 4 | 0 |
| PF-PRIORITY | 2 | 0 | 0 | 2 | 0 |
| PF-UNKNOWN | 5 | 0 | 2 | 3 | 0 |

Отклонённые ответы без полного совпадения ожидаемого критерия и цели:

- CF2-01/answer_03: ожидалось CF-EVIDENCE@jd_1; найдено CF-EVIDENCE@None.
- CF2-03/answer_03: ожидалось CF-LABEL@jd_2; найдено CF-UNCERTAINTY@jd_1.
- PF2-06/answer_04: ожидалось PF-UNKNOWN@pref_1; найдено PF-EVIDENCE@pref_1.
- PF2-07/answer_04: ожидалось PF-UNKNOWN@pref_1; найдено PF-INTERPRETATION@None.

## Невалидные оценки

Нет.

## Границы результата

- Нет live API-вызовов, модельного judge или новых ответов Maguire. Проверены готовые фикстуры.
- Идентификаторы и авторские вердикты исключены из runtime-пакета. Код и данные зафиксированы до прогона; авторы проекта ранее видели development-набор.
- Gold содержит допустимые метки и основания. Это проверка качества ответа относительно подготовленного эталона, а не самостоятельная оценка новой вакансии.
- Сравнение идёт с предложенной разметкой, а не с независимо подтверждённой истиной. Нет оценки вероятности интервью или порога выпуска продукта.
- Смысловая полнота цитаты, тонкие преувеличения и полезность каждого next_step требуют последующей проверки человеком или отдельно валидированным semantic judge.
- Набор не менялся для улучшения результата. Хеши локальные и не являются внешней подписью.

Полная детализация: [measurement.json](measurement.json); ответы грейдера: [predictions.jsonl](predictions.jsonl);
фиксация кода: [freeze.json](freeze.json); итоговая связность: [receipt.json](receipt.json).
