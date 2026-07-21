# 합격시험 결과 (Codex 재감사 R2 반영)

> R2에서 감사관이 재현한 watcher 실행 결함 2건(동시 실행 레이스 · 하위 변경 누락)을 수정한 뒤,
> R2 합격 조건으로 재검증한 결과. (2026-07-22)

## R2 수정 요약
- 획득을 `mv -f` → **`mkdir` 원자 락**으로(동시 시작 직렬화), 락 안에서 lease 재검사.
- lease에 **owner token**(PID+시작시각+난수) 기록, **owner 일치 시에만 cleanup**(남의 lease 삭제 방지), 루프 중 owner 바뀌면 자기 종료.
- top mtime → **재귀 스냅샷**(하위 타입·경로·크기·mtime 해시)로 하위 수정·신규·rename·삭제 감지.
- irreversible-gate: **등급 중복 시 최고등급 우선**. session-bootstrap: 종결을 **`in_reply_to`/원참조 ID**로 명시.

## 합격 조건별 결과

| R2 합격 조건 | 결과 | 실측 |
|---|---|---|
| 동일 target **10회 동시 시작 → 실행 writer 최대 1개** | ✅ PASS | `armed_count=1 · reuse_count=9 · 고유 owner=1` |
| live owner lease 비선점 · stale 회수 후 writer 1개 | ✅ PASS | 죽은 lease(pid 999999) → `armed`(회수) / live → `reuse` |
| 기존파일 수정·신규·rename/delete·하위경로 변경 각각 감지 | ✅ PASS | 5개 변경 → `change` 5회 |
| owner 일치 cleanup(남의 lease 안 지움) | ✅ PASS | 종료 시 내 owner lease만 반납 |

## 시험 1 — 10회 동시 시작 (poll=2, timeout 4s)
```
armed_count = 1
reuse_count = 9
서로 다른 armed owner 수 = 1
armed: owner=16939_1784678072383731300_2998421589 pid=16939 대상=/tmp/wtest2/tree poll=2s
reuse: 살아있는 감시기 재사용 (owner=16939_1784678072383731300_2998421589 pid=16939)   ← 9회 전부 이 owner 참조
```

## 시험 2 — 재귀 변경 감지 (poll=1)
```
armed: owner=17729_1784678090704448700_59693103 pid=17729 대상=/tmp/wtest3/tree poll=1s
change: ... (기존파일 a.txt 수정)
change: ... (신규 c.txt 추가)
change: ... (하위 sub/b.txt 수정)
change: ... (rename c.txt→c2.txt)
change: ... (삭제 a.txt)
→ change 이벤트 5개 = 변경 5건 각각 감지
```

## 시험 3 — stale 회수 + owner 반납
```
(lease = owner=DEAD_owner pid=999999 선주입)
armed: owner=18178_..._5411695 pid=18178 ...      ← 죽은 lease 회수
종료 후: lease 정상 반납됨(파일 없음)              ← 내 owner였으므로 삭제
```

## 규약(코드 실행 아님) 항목
- **승인 SHA ≠ 실행 SHA → push/deploy 대기**: `irreversible-gate` 승인 결속 + "대상 바뀌면 재승인".
- **FACT PASS라도 권리 증거 없으면 RIGHTS 미판정**: `myth-cosign-check` FACT/RIGHTS 분리.
- **open/closed 복합키 예**: `SKILLREVIEW 차수1`(매니저→KDT, 회신요망=예)에 KDT→매니저 `차수1-회신` 대응 존재 = closed. 대응 없는 최신 차수만 open. `회신요망=예` 텍스트만으로 판단하지 않음.

## 한계
`irreversible-gate`는 조언 계층 — 실제 차단은 permission/hook/branch protection 병행(각 스킬·README 명시).
