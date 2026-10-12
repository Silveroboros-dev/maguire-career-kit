# V3: проверка ручного разбора 16 фрагментов

Известные примеры разработки. Gold и нормализация проверены агентами; человек их не утверждал. Автоматического извлечения и оценки целых ответов нет.

| Ожидаемая категория | Всего | pass | fail | needs_review | invalid |
| --- | ---: | ---: | ---: | ---: | ---: |
| fail | 13 | 0 | 13 | 0 | 0 |
| pass | 2 | 2 | 0 | 0 | 0 |
| needs_review | 1 | 0 | 0 | 1 | 0 |

Пропущенные ошибки (ошибочный фрагмент получил pass): нет.
Ложные отказы (допустимый фрагмент получил fail): нет.
На review: ['D16'].
Принудительные решения на неоднозначности: нет.
Invalid/execution errors: нет.

Ожидаемые ошибочные атомы с совпавшими relation и span: 18/18.
Ложные замечания к отдельным атомам: нет.
Расхождения отношений: нет.
Отдельные атомы на review: ['D13/c2', 'D16/c1'].

Совпадение отношения и места не заменяет содержательной проверки причины.

| Пример | Исходный ответ | Ожидалось | Получено | Замечания: claim / rule |
| --- | --- | --- | --- | --- |
| D01 | CF2-01/answer_04 | fail | fail | c1 / evidence_gap |
| D02 | CF2-03/answer_04 | fail | fail | c2 / evidence_gap |
| D03 | CF2-04/answer_03 | fail | fail | c2 / evidence_gap |
| D04 | CF2-04/answer_04 | fail | fail | c1 / evidence_gap |
| D05 | CF2-05/answer_04 | fail | fail | c1 / source_role_boundary; c2 / evidence_gap |
| D06 | PF2-02/answer_03 | fail | fail | c1 / evidence_gap |
| D07 | PF2-02/answer_04 | fail | fail | c2 / evidence_gap |
| D08 | PF2-03/answer_03 | fail | fail | c1 / hard_preference_conflict |
| D09 | PF2-05/answer_04 | fail | fail | c1 / frequency_ceiling |
| D10 | PF2-06/answer_01 | pass | pass | — |
| D11 | PF2-06/answer_02 | pass | pass | — |
| D12 | PF2-06/answer_03 | fail | fail | c1 / evidence_gap; c2 / evidence_gap; c3 / evidence_gap |
| D13 | PF2-06/answer_04 | fail | fail | c1 / evidence_gap; c3 / evidence_gap |
| D14 | PF2-08/answer_03 | fail | fail | c1 / evidence_gap |
| D15 | PF2-08/answer_04 | fail | fail | c1 / evidence_gap; c2 / evidence_gap |
| D16 | PF2-02/answer_01 | needs_review | needs_review | — |

D10/D11 повторяют одну формулировку в двух ответах. Количество записей не равно количеству независимых смысловых проверок.
Fail может сосуществовать с неоднозначностью другого атома: уже установленный дефект не отменяется. Needs_review не считается обнаруженной ошибкой.
Сохранённые пакеты не содержат example/case/answer IDs или ожидаемых решений. Хеши подтверждают локальную неизменность, не внешнюю подпись.
