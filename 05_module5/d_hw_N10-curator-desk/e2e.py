# -*- coding: utf-8 -*-
"""★전 과정을 «실제로» 돌린다 — 「된다」를 말이 아니라 기록으로 남긴다.

  python e2e.py            수집은 건너뛰고(캐시) 세탁→조회→작성→관문→그래프
  python e2e.py --수집     위키미디어부터 다시 (느리고 429 를 만날 수 있다)

⛔「통과」를 «출력»으로 판정하지 않는다 — 종료코드로 판정한다.
  노드9 피어리뷰 지적 — 경고만 찍고 0 으로 끝나면 e2e 가 통과로 센다.
  ★그리고 파이프 뒤에서 종료코드를 보지 않는다(§A-8) — 여기서 직접 받는다.
"""
import argparse
import io
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
실패 = []
기록 = []


def 돈다(이름, args, 필수=True):
    t0 = time.time()
    r = subprocess.run([PY] + args, cwd=HERE, capture_output=True,
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    초 = time.time() - t0
    out = (r.stdout or b"").decode("utf-8", "replace")
    err = (r.stderr or b"").decode("utf-8", "replace")
    ok = r.returncode == 0
    # ★«실패로 세지 않는 것»을 «실패처럼» 찍지 않는다.
    #   ⛔전에는 필수가 아닌 단계도 ⛔FAIL 로 찍혔다. 그래서 화면에
    #     「⛔FAIL」이 있는데 요약은 「실패 0」이었다 — ★보고가 서로 다른 말을 했다.
    #   읽는 사람은 둘 중 하나를 «틀린 것»으로 여긴다. 어느 쪽도 안 틀렸는데.
    표 = "OK  " if ok else ("⛔FAIL" if 필수 else "⚠넘김")
    print("  %-26s %s  %5.1f초  (exit %d)" % (이름, 표, 초, r.returncode))
    if not ok:
        print("      " + (err.strip().splitlines() or ["(빈 오류)"])[-1][:120])
        if 필수:
            실패.append(이름)
        else:
            print("      ⤷ 이 단계는 실패해도 «진행»합니다 — 요약의 실패 수에 안 듭니다")
    기록.append({"단계": 이름, "명령": " ".join(args), "종료코드": r.returncode,
               "초": round(초, 1), "끝줄": (out.strip().splitlines() or [""])[-1][:120]})
    return ok, out


def 본다(이름, 조건, 설명=""):
    print("  %-26s %s  %s" % (이름, "OK  " if 조건 else "⛔FAIL", 설명))
    if not 조건:
        실패.append(이름)


def _j(rel):
    p = os.path.join(HERE, rel)
    return json.load(io.open(p, encoding="utf-8")) if os.path.exists(p) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--수집", action="store_true")
    a = ap.parse_args()

    print("═══ e2e — 전 과정 ═══")
    print()
    if a.수집:
        돈다("① 수집", ["fetch_art.py"])
    else:
        본다("① 수집 (캐시 사용)", os.path.exists(os.path.join(HERE, "data/corpus.json")),
           "--수집 으로 다시 받을 수 있습니다")

    돈다("② 세탁", ["normalize.py"])
    돈다("③ 작가 조회", ["enrich.py"])
    돈다("④ 작성 — 소박", ["write.py"])
    돈다("⑤ 작성 — 조심", ["write.py", "--조심"])
    # ★LLM 은 «키가 있고 캐시가 있을 때만» — 돈이 드는 것을 매번 부르지 않는다.
    #   캐시가 있으면 호출 0 이라 공짜다. 없으면 건너뛴다.
    if os.path.exists(os.path.join(HERE, "data/_llm_cache.json")):
        돈다("⑤-2 작성 — ★llm (캐시)", ["write.py", "--llm"], 필수=False)
    else:
        print("  %-26s %s  키·캐시가 없어 건너뜁니다"
              % ("⑤-2 작성 — llm", "SKIP"))
    돈다("⑥ 관문", ["gates.py", "--입력", "data/written_소박.json"])
    돈다("⑦ 비교표", ["compare.py"])
    # ★청소 실패는 «치명»이 아니다 — streamlit 이 sqlite 를 쥐고 있으면
    #   못 지운다. 올림은 같은 thread_id 를 덮어써서 이어 간다.
    ok청소, _ = 돈다("⑧ 그래프 청소", ["graph.py", "--청소"], 필수=False)
    if not ok청소:
        print("      (streamlit 이 떠 있으면 정상입니다 — 이어서 씁니다)")
    ok, out = 돈다("⑨ 그래프 올림", ["graph.py", "--올린다"])
    돈다("⑩ 대기 목록", ["graph.py", "--목록"])

    print()
    print("── 결과가 «말이 되는가» ──")

    깬 = _j("data/clean.json")
    본다("세탁 결과가 있다", bool(깬) and 깬["수"] > 0)
    e = _j("data/enriched.json")
    본다("작가 조회가 붙었다",
       bool(e) and all("작가조회" in m for m in e["작품"]))
    미 = sum(1 for m in (e or {}).get("작품", [])
           if (m.get("작가조회") or {}).get("상태") == "미조회")
    본다("미조회 0건", 미 == 0, "%d건 — 429 였다면 enrich.py 를 다시" % 미)

    소 = _j("data/written_소박.json")
    조 = _j("data/written_조심.json")
    본다("두 작성기 결과가 다르다",
       bool(소) and bool(조)
       and any(x["해설"] != y["해설"] for x, y in zip(소["작품"], 조["작품"])),
       "같으면 비교표에 쓸 것이 없다")

    c = _j("output/compare.json")
    # ⛔모드 목록을 «굳히지» 않는다 — llm 이 늘었을 때 여기가 터졌다(§F-8-D).
    본다("비교표가 «만든 모드를 다» 담았다",
       bool(c) and set(c["모드별"]) >= {"소박", "조심"},
       "담긴 것 %s" % sorted((c or {}).get("모드별", {})))
    있는모드 = {m for m in ("소박", "조심", "llm")
             if os.path.exists(os.path.join(HERE, "data/written_%s.json" % m))}
    본다("★만든 모드가 «빠짐없이» 재어졌다",
       bool(c) and set(c["모드별"]) == 있는모드,
       "파일 %s vs 표 %s" % (sorted(있는모드),
                          sorted((c or {}).get("모드별", {}))))

    if c:
        # ★기준을 다 켜면 «놓침이 0» 이어야 한다. 아니면 기준이 못 잡는 위험이 있다.
        for 모드 in c["모드별"]:
            for 갈래, d in c["모드별"][모드]["갈래별"].items():
                전부 = max(d["행"], key=lambda r: len(r["기준"]))
                본다("%s/%s — 전부 켜면 놓침 0" % (모드, 갈래),
                   전부["놓침"] == 0, "놓침 %d건" % 전부["놓침"])
        # ★그리고 «아무것도 안 켜면» 놓쳐야 한다 — 아니면 정답이 비어 있다는 뜻
        빈판 = [(모드, 갈래)
              for 모드 in c["모드별"]
              for 갈래, d in c["모드별"][모드]["갈래별"].items()
              if d["정답_멈춰야할것"] == 0]
        print("  %-26s %s  정답이 0 인 칸 %d개 — 그 갈래는 비교가 무의미하다"
              % ("정답이 실재하는가", "OK  " if len(빈판) <= 2 else "⚠WARN",
                 len(빈판)))

    색인 = _j("output/threads.json")
    본다("thread 가 «작품 × 갈래» 로 생겼다",
       bool(색인) and len(색인) > 0
       and all(":" in k for k in 색인))
    대기 = sum(1 for v in (색인 or {}).values() if "끝남" not in v)
    본다("자동 처리와 대기가 «둘 다» 있다",
       0 < 대기 < len(색인 or {1: 1}),
       "대기 %d / 전체 %d — 한쪽이 0 이면 기준이 무르거나 빡빡하다"
       % (대기, len(색인 or {})))
    본다("체크포인터가 «파일»에 있다",
       os.path.exists(os.path.join(HERE, "output/checkpoints.sqlite")),
       "SqliteSaver — 껐다 켜도 대기 건이 남는다")

    # ★재개가 «실제로» 되는지 한 건 돌려 본다
    print()
    print("── 재개 (interrupt → Command(resume=)) ──")
    sys.path.insert(0, HERE)
    import graph
    graph._앱 = None
    w = graph.대기목록()
    본다("대기 판정이 snapshot.next 로 나온다", bool(w),
       "%d건" % len(w))
    if w:
        전 = len(w)
        r = graph.답한다(w[0]["id"], "반려", "e2e 시험")
        후 = len(graph.대기목록())
        본다("답하면 대기가 하나 준다", 후 == 전 - 1, "%d → %d" % (전, 후))
        본다("반려는 «바깥으로 안 나간다»",
           "안 나감" in (r.get("결과") or ""), r.get("결과"))

    # ★응답 넷이 «실제로» 다른가 — 이름만 다르면 자동화 근거가 무너진다
    print()
    print("── 응답 넷이 «서로 다른가» ──")
    w = graph.대기목록()
    쓴것 = {}
    for 답 in ("발행", "수정 후 발행"):
        후보 = [x for x in graph.대기목록() if x["id"] not in 쓴것]
        if not 후보:
            break
        tid = 후보[0]["id"]
        쓴것[tid] = 답
        메모 = "★e2e 가 고쳐 넣은 문장입니다." if 답 == "수정 후 발행" else None
        r = graph.답한다(tid, 답, 메모)
        본다("「%s」 가 결과를 낸다" % 답, bool(r.get("결과")),
           (r.get("결과") or "")[:70])

    # ★「다시 해설」은 «결과를 내면 안 된다» — 다시 쓰고 «다시 멈춘다».
    #   ⛔처음엔 「결과를 낸다」로 단정했다가 실패했다. ★내 단정이 틀렸다.
    #     다시 쓴 글을 사람이 «또» 보는 것이 이 응답의 뜻이다.
    후보 = [x for x in graph.대기목록() if x["id"] not in 쓴것]
    if 후보:
        tid = 후보[0]["id"]
        쓴것[tid] = "다시 해설"
        전글 = (후보[0].get("물음") or {}).get("대상")
        graph.답한다(tid, "다시 해설")
        남 = {x["id"]: x for x in graph.대기목록()}
        본다("★「다시 해설」은 «다시 멈춘다» (반려와 다르다)", tid in 남,
           "여전히 대기 중이어야 한다 — 다시 쓴 글을 사람이 또 본다")
        st = graph.만든다().get_state(graph._cfg(tid))
        본다("★다시 쓴 글이 «상태에» 들어갔다",
           bool((st.values or {}).get("다시쓴글")),
           (str((st.values or {}).get("다시쓴글"))[:64]))
        본다("다시 쓴 횟수가 «세어진다»",
           ((st.values or {}).get("다시횟수") or 0) >= 1,
           "다시횟수=%s" % (st.values or {}).get("다시횟수"))

    로그 = []
    _p = os.path.join(HERE, "output/published.jsonl")
    if os.path.exists(_p):
        로그 = [json.loads(l) for l in io.open(_p, encoding="utf-8")]
    수정건 = [x for x in 로그 if x["결정"] == "수정 후 발행"]
    본다("★「수정 후 발행」이 «메모를 실제로 쓴다»",
       bool(수정건) and "e2e 가 고쳐 넣은" in (수정건[-1]["내용"] or ""),
       (수정건[-1]["내용"][:60] if 수정건 else "기록이 없다"))
    결정들 = {x["결정"] for x in 로그}
    본다("기록에 «사람이 누른» 결정이 남는다",
       len(결정들 - {"자동통과"}) >= 2, str(sorted(결정들)))

    # ★재개하면 «멈춘 단계»가 처음부터 다시 도는가 — REPORT 의 주장을 «실증»
    print()
    print("── 멈춘 «단계»가 처음부터 다시 도는가 (강의 2강) ──")
    본 = []
    원래관문 = graph.관문

    def 세는관문(s):
        본.append(s["슬러그"] + ":" + s["갈래"])
        return 원래관문(s)

    graph.관문 = 세는관문
    graph._앱 = None                       # 그래프를 다시 짜야 훅이 걸린다
    남 = [x for x in graph.대기목록() if x["id"] not in 쓴것]
    if 남:
        tid = 남[0]["id"]
        본.clear()
        graph.답한다(tid, "반려", "재실행 시험")
        본다("재개하면 관문 노드가 «다시» 실행된다", len(본) >= 1,
           "관문 %d회 — ⇒ ⛔관문 «안»에서 바깥으로 나가면 두 번 나간다"
           % len(본))
    graph.관문 = 원래관문
    graph._앱 = None

    # ★재개 시험이 «대기 건을 실제로 처리»해서 상태가 바뀌었다(266 → 261).
    #
    # ⛔전에는 여기서 «문서 수치를 다시 찍었다». 주석까지 이렇게 달려 있었다 —
    #   「안 그러면 e2e 가 자기가 바꾼 것 때문에 자기 검사에 걸린다」.
    #   ★문제를 «알면서 반대로» 푼 것이다. 그 결과 문서에
    #   「261건 대기」가 박혔다 — ★시험 중 상태가 제출물에 새겨졌다.
    #   채점자가 e2e 를 한 번 돌리면 README 수치가 틀어진다.
    #
    # ⇒ ★시험은 «자기가 어지른 것을 치운다». 문서를 고치지 않는다.
    #   치우고 나면 수치가 원래대로라, sync 는 «검사»만 해도 통과한다.
    #
    # ⛔`graph.py --청소` 를 쓰지 않는다 — 실측으로 알았다.
    #   청소는 checkpoints.sqlite 를 «지우려» 하는데, ★이 시험 자신이
    #   그 파일을 열고 있어서 못 지우고 종료코드 2 로 끝난다.
    #   ⇒ 여기서는 «지울 필요»도 없다. 올림이 같은 thread_id 를 덮어쓴다.
    #     실측 — 올림만으로 688 / 대기 266 / 자동 422 가 그대로 돌아온다.
    #   ⚠ 대신 «발행 기록»은 덮어써지지 않고 «쌓이므로» 잘라 둔다.
    for _f in ("output/published.jsonl", "output/catalog.json"):
        _p = os.path.join(HERE, _f)
        if os.path.exists(_p):
            os.remove(_p)
    돈다("⑪ ★상태 되돌리기 (올림)", ["graph.py", "--올린다"])
    돈다("⑫ 수치 동기화 — ★검사만", ["sync_numbers.py", "--검사"])
    돈다("⑬ 레드팀", ["redteam.py"])

    os.makedirs(os.path.join(HERE, "output"), exist_ok=True)
    io.open(os.path.join(HERE, "output/e2e.json"), "w",
            encoding="utf-8", newline="").write(
        json.dumps({"단계": 기록, "실패": 실패,
                    "python": sys.version.split()[0]},
                   ensure_ascii=False, indent=1))

    print()
    print("═" * 60)
    print("  실패 %d" % len(실패))
    if 실패:
        print("  ⛔" + " · ".join(실패[:6]))
    print("  → output/e2e.json")
    return 1 if 실패 else 0


if __name__ == "__main__":
    sys.exit(main())
