"""소스 성적표 + 깔때기 통과율 — 12강 「운영: 지표 남기기」의 «집계» 쪽.

`store/metrics.jsonl` 에 쌓인 실행 기록만 읽는다. **새 도구도 새 호출도 없다.**

  python 04_scorecard.py                      # 기본 프로필(AI)
  PROFILE=discovery python 04_scorecard.py    # 「발견」 프로필

★이 스크립트가 답하는 질문 셋
  1. 어떤 소스가 «실제로 발행까지» 올라가나  — 몇 주째 0건이면 비용만 쓰는 것
  2. 각 단계가 «몇 %» 를 통과시키나        — 절대 건수는 출렁여도 비율은 안정적이다
  3. 선별 기준이 «의도대로» 동작했나        — 탈락 사유를 세어 본다
"""
import io
import json
import os
import re
import sys
from collections import Counter

# ★윈도 콘솔 기본이 cp949 라 한글·괘선이 UnicodeEncodeError 로 죽는다.
#   「돌려보면 알겠지」가 아니라 «누가 돌려도» 되게 여기서 막는다.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "store", "metrics.jsonl")
WANT = os.environ.get("PROFILE", "").strip()


def load():
    if not os.path.exists(PATH):
        raise SystemExit("기록이 없습니다: %s — 먼저 run.py 를 한 번 돌리세요." % PATH)
    return [json.loads(l) for l in io.open(PATH, encoding="utf-8") if l.strip()]


def profile_sources():
    """지금 프로필의 소스 이름 목록과 주제 집합."""
    import yaml
    sf = "settings_%s.yaml" % WANT if WANT else "settings.yaml"
    path = os.path.join(HERE, sf)
    if not os.path.exists(path):
        raise SystemExit("설정이 없습니다: %s" % sf)
    cfg = yaml.safe_load(io.open(path, encoding="utf-8"))
    src = cfg.get("sources") or []
    return [s["name"] for s in src], set(s.get("group") for s in src if s.get("group")), sf


_GRP = re.compile(r"예선 \[([^\]]+)\]")


def mine(r, names, groups):
    """★이 실행이 «지금 프로필» 것인가 — 기억이 아니라 «기록»으로 판정한다.

    metrics.jsonl 의 옛 행에는 `profile` 필드가 없다(뒤에 추가한 필드다).
    없는 필드를 「아마 이거겠지」로 메우지 않고, 남아 있는 «흔적»으로 가린다:
      ① 발행이 있으면 — 발행된 소스 이름이 이 프로필 목록에 드는가
      ② 발행이 0건이면 — 예선 로그의 주제 이름(`예선 [우주]`)이 이 프로필 것인가
    둘 다 못 가리면 «모름»(None) 으로 두고 집계에서 «뺀다».
    ⇒ 섞어 세면 분모가 부풀어 「이 소스는 한 번도 못 올라갔다」가 거짓이 된다.

    ★`profile` «이름»으로는 판정하지 않는다.
      같은 설정을 `settings_discovery.yaml` 로도 `settings.yaml` 로도 부를 수 있어서,
      **이름은 갈리는데 내용은 같은** 경우가 실제로 생긴다(이 저장소가 그렇다).
      이름이 아니라 «무엇을 수집했나»가 실체다.
    """
    src = set((r.get("by_source") or {}).keys())
    if src:
        return bool(src & set(names))
    seen = set()
    for line in r.get("log") or []:
        m = _GRP.search(line)
        if m and m.group(1) != "_":
            seen.add(m.group(1))
    if seen:
        return bool(seen & groups)
    return None


def bar(ratio, width=22):
    n = int(round(max(0.0, min(1.0, ratio)) * width))
    return "█" * n + "·" * (width - n)


def pad(s, w):
    """한글은 두 칸을 차지한다 — %-22s 로는 표가 어긋난다."""
    wide = sum(2 if ord(c) > 0x1100 else 1 for c in s)
    return s + " " * max(0, w - wide)


def main():
    allrows = load()
    names, groups, sf = profile_sources()
    rows = [r for r in allrows if mine(r, names, groups) is True]
    other = len(allrows) - len(rows)

    print("=" * 74)
    print("소스 성적표 — 프로필 %s (%s)" % (WANT or "(기본)", sf))
    print("  실행 %d회 · 총 %.1f분   ※ 다른 프로필·판정불가 %d회는 뺐다"
          % (len(rows), sum(r.get("elapsed_s", 0) for r in rows) / 60, other))
    print("=" * 74)
    if not rows:
        print()
        print("이 프로필로 돌린 기록이 없습니다.")
        return

    # ── 1. 소스별 발행 기여 ────────────────────────────────────
    pub = Counter()
    for r in rows:
        for k, v in (r.get("by_source") or {}).items():
            pub[k] += v
    total = sum(pub.values())
    print()
    print("### 1. 소스별 «발행까지» 올라간 건수")
    print(pad("소스", 20) + "  발행   비중")
    print("-" * 74)
    top = max(pub.values()) if pub else 1
    for name, n in pub.most_common():
        print("%s %5d  %4.0f%%  %s" % (pad(name, 20), n, 100 * n / total, bar(n / top)))
    print("-" * 74)
    print("  합계 %d건 · 소스 %d곳 중 %d곳이 기여" % (total, len(names), len(pub)))

    never = [n for n in names if n not in pub]
    if never:
        print()
        print("  ⚠ 이 %d회 동안 «한 번도» 발행에 못 올라간 소스 %d곳:" % (len(rows), len(never)))
        print("      " + " · ".join(never))
        print("    ⇒ 실행 %d회는 «며칠치»다. 0건이 곧 «쓸모없다»는 뜻은 아니다." % len(rows))
        print("      몇 주가 지나도 0이면 그때 뺀다 — 매일 수집·예선 토큰만 쓰는 것이므로.")

    # ── 2. 깔때기 통과율 ──────────────────────────────────────
    print()
    print("### 2. 깔때기 — 단계별 «통과율»")
    print("    절대 개수는 그날 뉴스 양에 따라 출렁이지만 «비율»은 안정적이다.")
    print("    한 단계 비율이 갑자기 변하면 그 단계나 «바로 앞» 단계가 바뀐 것이다.")
    print()
    print("%-14s %6s %6s %6s %6s   %s" % ("실행", "수집", "선별", "취재", "발행", "선별율"))
    print("-" * 74)
    for r in rows:
        c, p, d, b = r["collected"], r["picked"], r["drafted"], r["published"]
        ratio = p / c if c else 0
        print("%-14s %6d %6d %6d %6d   %5.1f%%  %s"
              % (r["run_id"][5:16], c, p, d, b, 100 * ratio, bar(ratio, 12)))
    print("-" * 74)
    tc = sum(r["collected"] for r in rows)
    tp = sum(r["picked"] for r in rows)
    td = sum(r["drafted"] for r in rows)
    tb = sum(r["published"] for r in rows)
    print("  합계   수집 %d → 선별 %d → 취재 %d → 발행 %d" % (tc, tp, td, tb))
    print("  평균 통과율   선별 %.1f%%   취재 %.1f%%   검수 %.1f%%"
          % (100 * tp / max(tc, 1), 100 * td / max(tp, 1), 100 * tb / max(td, 1)))
    print()
    print("  읽는 법 — 수집→선별의 낙폭이 큰 건 «정상»이다(그게 선별의 일).")
    print("            취재→발행의 낙폭이 크면 본문 추출이나 검수에서 «조용히» 빠지는 것이다.")

    # ── 3. 탈락 사유 ─────────────────────────────────────────
    print()
    print("### 3. 탈락 사유 — 코드로 건 규칙이 «실제로» 걸렸나")
    why = Counter()
    for r in rows:
        for line in r.get("log") or []:
            m = re.search(r"(주제 상한|매체 상한|같은 사건|본문 부족|한국어 실패)", line)
            if m:
                why[m.group(1)] += 1
            if "[규칙]" in line:
                why["검수 — 규칙검사"] += 1
            elif line.strip().startswith("✗"):
                why["검수 — LLM 대조"] += 1
            if "재생성 후 합격" in line:
                why["★재생성으로 회복"] += 1
            elif "재생성해도 불합격" in line:
                why["재생성해도 불합격"] += 1
            if "취재 중단(재시도 무의미)" in line:
                why["★취재 중단(유형 판정)"] += 1
    if not why:
        print("  (탈락 기록 없음)")
    else:
        top = max(why.values())
        for k, v in why.most_common():
            print("  %s %4d  %s" % (pad(k, 22), v, bar(v / top)))
        print("-" * 74)
        print("  ⇒ 프롬프트에 «적은» 부탁이 아니라 «코드로 센» 규칙이 걸린 횟수다.")
        print("    0 이면 그 규칙은 «있으나 마나»였다는 뜻이다 — 지웠는지 확인한다.")

    # ── 3-B. ★재생성이 «왜» 실패하나 ─────────────────────────
    #   회복률만 보면 「0건」인데, 그게 «프롬프트 문제»인지 «애초에 대상이 아닌 것»인지
    #   구분이 안 된다. 대응이 정반대라 반드시 갈라야 한다 (피어리뷰 질문에서 나온 축).
    rd = Counter()
    for r in rows:
        for line in r.get("log") or []:
            if "재생성 실패 → 스킵:" in line:
                tail = line.split("스킵:", 1)[1].strip()
                if "본문" in tail:
                    rd["본문이 짧아 «대상이 아님»"] += 1
                elif "한국어" in tail:
                    rd["한국어로 못 씀 — 프롬프트 문제"] += 1
                elif "중단" in tail:
                    rd["재시도 무의미(연결·타임아웃)"] += 1
                else:
                    rd["기타: " + tail[:24]] += 1
            elif "재생성해도 불합격" in line:
                rd["다시 써도 검수 불합격"] += 1
            elif "재생성 후 합격" in line:
                rd["★회복 성공"] += 1
    if rd:
        print()
        print("### 3-B. 재생성(redraft)이 «왜» 실패했나")
        top = max(rd.values())
        for k, v in rd.most_common():
            print("  %s %4d  %s" % (pad(k, 30), v, bar(v / top)))
        print("-" * 74)
        rec = rd.get("★회복 성공", 0)
        tot = sum(rd.values())
        print("  회복률 %d/%d — 「끌 것인가」는 이 «사유 분포»를 보고 정한다." % (rec, tot))
        print("    · 「프롬프트 문제」가 다수면 → 프롬프트를 고친다(끄지 않는다)")
        print("    · 「대상이 아님」이 다수면  → 재생성 «조건»을 좁힌다")
        print("    · 「다시 써도 불합격」이 다수면 → 모델 한계. 더 큰 모델에서 재측정")

    # ── 4. 주제 배분 ─────────────────────────────────────────
    grp = Counter()
    for r in rows:
        for k, v in (r.get("by_group") or {}).items():
            grp[k] += v
    if grp:
        print()
        print("### 4. 주제별 발행 배분 — group_caps 가 실제로 자리를 나눴나")
        top = max(grp.values())
        for k, v in grp.most_common():
            print("  %s %4d건  %s" % (pad(k, 10), v, bar(v / top)))
    elif groups:
        print()
        print("### 4. 주제별 발행 배분")
        print("  (옛 기록에는 by_group 이 없다 — 이 필드는 나중에 넣었다. 다음 실행부터 쌓인다.)")


if __name__ == "__main__":
    main()
