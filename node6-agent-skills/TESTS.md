# 최소 합격시험 결과 (Codex 감사관 권고 반영)

> 르주엔 코덱스 감사관 `CODEX-KDT-NODE6-SKILLS-REVIEW-01`의 6건 권고를 반영한 뒤,
> 감사관이 제시한 "최소 합격시험"을 확인한 결과. (2026-07-22)

| # | 합격 기준 | 결과 | 근거 |
|---|---|---|---|
| 1 | bootstrap 연속 2회 실행해도 heartbeat writer **정확히 1개** | ✅ PASS | 헬퍼 2차 실행이 `reuse` + exit 0, lease의 `pid=` 라인 1개 |
| 2 | 살아있는 lease는 **선점 안 하고 stale만 회수** | ✅ PASS | 죽은 PID(999999) lease → `armed`(회수) / 살아있는 lease → `reuse` |
| 3 | 같은 thread 여러 차수·양방향에서 **open·closed 정확 구분** | ✅ 규약 | `session-bootstrap` 4단계 = (스레드ID+차수+방향) 복합키, 반대방향 다음차수 회신=닫힘, superseded/withdrawn 반영, 최신 우선·dedup |
| 4 | **승인 SHA ≠ 실행 SHA면 push·deploy 대기** | ✅ 규약 | `irreversible-gate` 승인 결속(대상·환경·SHA…), "대상 바뀌면 재승인" 명시 |
| 5 | FACT PASS 나와도 **권리 증거 없으면 RIGHTS 미판정** | ✅ 규약 | `myth-cosign-check` = `FACT PASS/FAIL` 과 `RIGHTS NOT ASSESSED` 분리 |
| 6 | 5개 스킬 **frontmatter·Pages 링크 재통과** | ✅ PASS | 5개 `name`·`description` 전부 존재 확인, Pages index.html 유지 |

## 1·2 실행 로그 (헬퍼 `scripts/ensure_single_watcher.sh`)

```
# TEST B — stale lease(죽은 PID) 회수
armed: 새 감시기 lease 획득 pid=2016 ... poll=3s        ← stale 회수됨

# TEST A — 살아있는 감시기 있을 때 2차 실행
2차 exit code = 0
reuse: 살아있는 감시기 lease 재사용 ...                   ← 선점 안 하고 재사용
writer 수(lease의 pid= 라인) = 1                          ← 정확히 1개
```

## 3 복합키 판정 예 (open vs closed)

- `SKILLREC 차수1` (KDT→매니저) 뒤에 **매니저→KDT `SKILLREC 차수1-회신`** 존재 → 반대 방향 다음 차수 회신 있음 = **closed**.
- `SKILLREC 차수2` (KDT→매니저) 뒤 매니저 회신 존재 = **closed**.
- `SKILLREVIEW 차수1` (매니저→KDT, 회신요망=예)에 대한 KDT→매니저 회신이 아직 없음 = **open**.
→ `회신요망=예` 텍스트만 보면 차수1도 열림으로 오판하지만, 복합키(방향+차수 대응)로 보면 닫힘.

## 한계 명시
`irreversible-gate`는 조언 계층이며 강제장치가 아니다 — 실제 차단은 permission/hook/branch protection 병행. (README·각 스킬에 명시)
