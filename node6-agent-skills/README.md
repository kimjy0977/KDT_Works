# 노드 6 과제 · AI 에이전트 스킬집

> 「바이브 코딩으로 웹 만들기 2 — AI 에이전트 도구」 노드 6 과제.
> 과제 요건은 "매번 반복하던 일을 스킬 하나로 만들어 GitHub에 올리기"지만,
> 실제로 반복하던 작업이 여러 개라 **스킬집(5종)**으로 만들었습니다.

**🔗 배포 페이지:** https://kjuyoung77.github.io/ModuWorks/node6-agent-skills/
**📁 갤러리:** https://kjuyoung77.github.io/ModuWorks/

## 스킬이란

폴더 1개 + `SKILL.md`(머리말 `name`·`description` + 본문 절차). AI는 평소 이름·설명만 알고 있다가(점진 공개), 관련 작업을 만나면 본문을 꺼내 쓴다. 좋은 후보 = **매번 똑같이 설명·지시하던 일**(재프롬프트 없애기).

## 이 스킬집의 5종 — 무슨 불편을, 어떻게 없앴나

각 스킬은 실제 프로젝트 운영에서 **매번 반복해 지시하던 절차**를 고정한 것입니다. (공개 저장소라 일반 절차만 담고, 비공개 값·내부 세부는 제외했습니다.)

| 스킬 | 계열 | 불편 → 해결 |
|---|---|---|
| **`session-bootstrap`** | 인프라 | 세션이 끊길 때마다 맥락·미처리 건을 손으로 되짚음 → 재무장·in-flight 점검·상태 복원을 한 순서로 고정 |
| **`irreversible-gate`** | 인프라 | push·배포·삭제 같은 비가역 액션을 무심코 실행 → 실행 직전 가역/비가역 판별 + 승인 게이트 |
| **`watcher-arm`** | 인프라 | 감시기를 매번 다르게 짜다 빠뜨림 → 표준 형태(자기발신 제외·heartbeat)로 재현 |
| **`myth-cosign-check`** | 콘텐츠 | 신화·미술 사실검증을 매번 즉흥으로 → 귀속·환각·전거 층위·헷지 체크리스트로 고정 |
| **`docent-tone`** | 콘텐츠 | 도록 톤이 사람마다 흔들림 → 서사체 톤 규칙으로 통일 |

## 폴더 구조

```
node6-agent-skills/
├─ README.md            ← 이 파일 (왜 만들었나)
├─ TESTS.md             ← 최소 합격시험 결과 (감사관 권고 반영)
├─ scripts/
│  └─ ensure_single_watcher.sh   ← watcher-arm 결정론적 헬퍼(단일 인스턴스)
└─ skills/
   ├─ session-bootstrap/SKILL.md
   ├─ irreversible-gate/SKILL.md
   ├─ watcher-arm/SKILL.md
   ├─ myth-cosign-check/SKILL.md
   └─ docent-tone/SKILL.md
```

## 쓰는 법 (Claude Code 기준)

`skills/<이름>/` 폴더를 프로젝트의 `.claude/skills/`에 두면 자동 인식된다. 다른 대화에서 **슬래시 명령**으로 발동 — `/session-bootstrap`, `/myth-cosign-check` 등.

> ⚠️ 최상위 `.claude/skills/`를 **최초로 생성**한 직후엔 도구를 한 번 재시작해야 인식된다.

## 강건성 (르주엔 코덱스 감사 반영, 2026-07-22)

외부 감사관 검토를 받아 실운영 수준으로 보강했다 — session-bootstrap을 **오케스트레이터**로(무조건 재무장 금지), watcher-arm에 **단일 인스턴스 lease 계약**(PID·mtime 생존판정), irreversible-gate에 **위험등급 + 승인 SHA 결속**, myth-cosign-check에 **재현 가능 증거 + 사실/권리 분리**. 검증 결과는 [`TESTS.md`](./TESTS.md). ※ 스킬은 조언 계층 — 실제 차단은 permission/hook/branch protection 병행.

## 회고

- MCP를 'USB-C'에 빗대면, 가장 먼저 꽂고 싶은 것 = 내 프로젝트의 메시지함/상태 파일(session-bootstrap가 그걸 읽는다).
- 매번 반복해 설명하던 일 = 세션 이어받기와 사실검증 — 그래서 그 둘을 헤드라이너로 삼았다.
- 새 AI 도구가 쏟아질 때 덜 휩쓸릴 기준 = "이 도구에 내 스킬·규칙을 얹을 수 있나(하네스가 열려 있나)".
