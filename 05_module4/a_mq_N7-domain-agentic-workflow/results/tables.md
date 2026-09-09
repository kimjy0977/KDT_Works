### 세팅별 비교

| 세팅 | n | 승인 도달 | 게이트 통과 | 중복 탐지 | 환각 Q번호 | 평균 스텝 | 평균 도구 | 평균 초 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ① 기준 (fulltext · 보정 없음) | 40 | 48% | 13% | 50% | 53% | 5 | 4 | 34 |
| ② + autoRepair (중복확인 자동보정) | 40 | 48% | 25% | 58% | 53% | 6 | 5 | 30 |
| ④ 모델 교체 — qwen2.5:3b | 40 | 18% | 3% | 38% | 45% | 10 | 9 | 35 |
| ③ 모델 교체 — llama3.2:1b | 40 | 93% | 0% | 93% | 0% | 3 | 2 | 2 |
| ⑤ 예산 절반 (스텝 6 · 90초) | 40 | 48% | 25% | 58% | 53% | 5 | 4 | 34 |

### 필드 정확도 — 아카이브 982점이 정답지

| 세팅 | origTitle | artist | era | inception | material | collection | people |
|---|---:|---:|---:|---:|---:|---:|---:|
| base | 45% (18/40) | 45% (18/40) | 5% (2/40) | 18% (7/40) | 28% (11/40) | 18% (7/39) | 19% (5/26) |
| repair | 45% (18/40) | 45% (18/40) | 5% (2/40) | 18% (7/40) | 28% (11/40) | 18% (7/39) | 19% (5/26) |
| other3b | 13% (5/40) | 10% (4/40) | 0% (0/40) | 8% (3/40) | 3% (1/40) | 3% (1/39) | 12% (3/26) |
| smaller | 0% (0/40) | 0% (0/40) | 0% (0/40) | 0% (0/40) | 0% (0/40) | 0% (0/39) | 0% (0/26) |
| tight | 45% (18/40) | 45% (18/40) | 5% (2/40) | 18% (7/40) | 28% (11/40) | 18% (7/39) | 19% (5/26) |

### ★자료의 천장별 — 섞어 놓고 한 숫자로 말하면 둘 다 오해가 된다

| 세팅 | 구간 | n | 승인 도달 | 작가 정확 | 중복 탐지 |
|---|---|---:|---:|---:|---:|
| base | strong | 10 | 70% | 70% | 60% |
| base | weak | 23 | 48% | 43% | 39% |
| base | none | 7 | 14% | 14% | 71% |
| repair | strong | 10 | 70% | 70% | 70% |
| repair | weak | 23 | 48% | 43% | 48% |
| repair | none | 7 | 14% | 14% | 71% |
| other3b | strong | 10 | 30% | 30% | 50% |
| other3b | weak | 23 | 17% | 4% | 39% |
| other3b | none | 7 | 0% | 0% | 14% |
| smaller | strong | 10 | 90% | 0% | 90% |
| smaller | weak | 23 | 91% | 0% | 91% |
| smaller | none | 7 | 100% | 0% | 100% |
| tight | strong | 10 | 70% | 70% | 70% |
| tight | weak | 23 | 48% | 43% | 48% |
| tight | none | 7 | 14% | 14% | 71% |

### 실패 분류

| 세팅 | 유형 |
|---|---|
| base | `useless_repetition` ×4 · `budget_exhausted` ×4 · `gate_blocked` ×14 · `other:other` ×5 · `gave_up_not_found` ×6 · `gave_up_license` ×1 · `backend_error:timeout` ×1 |
| repair | `useless_repetition` ×4 · `budget_exhausted` ×4 · `gate_blocked` ×9 · `other:other` ×5 · `gave_up_not_found` ×6 · `gave_up_license` ×1 · `backend_error:timeout` ×1 |
| other3b | `gave_up_not_found` ×2 · `budget_exhausted` ×23 · `gate_blocked` ×6 · `other:already_researched` ×1 · `gave_up_license` ×3 · `backend_error:timeout` ×2 · `format_broken` ×1 · `useless_repetition` ×1 |
| smaller | `gate_blocked` ×37 · `format_broken` ×3 |
| tight | `useless_repetition` ×2 · `budget_exhausted` ×6 · `gate_blocked` ×9 · `other:other` ×5 · `gave_up_not_found` ×6 · `gave_up_license` ×1 · `backend_error:timeout` ×1 |
