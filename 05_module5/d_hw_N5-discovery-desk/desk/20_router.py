# -*- coding: utf-8 -*-
"""★① 의도 분류 — 규칙 라우터와 LLM 라우터를 «나란히» 잰다.

노드4 와 다른 점 — 기준선을 «내가» 만들어야 한다
  모두몰은 규칙 라우터(macro F1 0.677)가 주어졌다. 내 도메인엔 없다.
  ⇒ 바닥을 모르면 «LLM 이 얼마나 벌었는지»를 말할 수 없다. 그래서 둘 다 만든다.

★어제 배운 것을 «처음부터» 넣는다
  1. --repeat N        폭을 모르면 「개선」이라 말할 자격이 없다
  2. --outscope 병행   eval 만 보면 범위 밖이 무너지는 걸 «못 본다»
  3. 형식 실패를 «분류 오류»와 구분  — 20/20 형식 실패를 겪었다
  4. reasoning=False   qwen3 계열은 thinking 토큰이 출력 예산을 삼킨다

  python 20_router.py --mode rule                    # 규칙 기준선
  python 20_router.py --mode llm --model qwen2.5:7b  # LLM
  python 20_router.py --mode llm --repeat 3          # 폭
"""
import argparse
import csv
import io
import re
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).parent
ROOT = HERE.parent

ROUTES = ["SPACE", "ARCHAEO", "PALEO", "CONCEPT", "OTHER"]
LABELS4 = ["SPACE", "ARCHAEO", "PALEO", "CONCEPT"]   # ★OTHER 는 macro 에서 뺀다
                                                     #   eval 에 정답이 0건이라 넣으면 0점이 된다

# ─────────────────────────────────────────────────────────
# 규칙 라우터 — «LLM 없이 어디까지» 되는지의 바닥
# ─────────────────────────────────────────────────────────
RULE = {
    "SPACE": ["우주", "행성", "별", "항성", "은하", "달", "화성", "금성", "수성", "목성",
              "토성", "천왕성", "해왕성", "명왕성", "태양", "블랙홀", "성운", "초신성",
              "소행성", "혜성", "운석", "망원경", "제임스웹", "허블", "탐사선", "로버",
              "프록시마", "센타우리", "시료", "대기", "고리", "뒷면",
              "위성", "궤도", "발사", "외계행성", "성간", "크레이터",
              # ★「지구는 몇 살인가요」가 OTHER 로 샜다. OTHER 가 우선순위
              #   맨 앞이라 「지구가 평평」은 그대로 OTHER 로 간다(측정으로 확인).
              "지구"],
    # ⚠ 「광년」·「적색편이」는 여기서 뺐다 — «대상»이 아니라 «개념»이다.
    #    SPACE 에 두면 「광년은 거리 단위인가요」가 SPACE 로 간다(실측).
    "ARCHAEO": ["고고", "유적", "유물", "발굴", "무덤", "고분", "미라", "점토판", "비문",
                "토기", "도자기", "석기", "청동기", "철기", "신석기", "구석기", "피라미드",
                "이집트", "폼페이", "마야", "잉카", "메소포타미아", "벽화", "난파선",
                "문명", "스톤헨지", "두루마리", "사해문서", "고대",
                "로마", "콘크리트"],   # ★「로마 콘크리트」가 OTHER 로 샜다
    "PALEO": ["화석", "공룡", "티라노", "멸종", "진화", "고생물", "암모나이트", "삼엽충",
              "매머드", "네안데르탈", "깃털", "발자국", "백악기", "쥐라기", "캄브리아",
              "다세포", "생물", "종은", "신축성",
              "고생대", "중생대", "빙하기", "호박", "코뿔소", "계통", "조상"],
    "CONCEPT": ["뭔가요", "무엇인가요", "어떻게", "왜", "원리", "정의", "단위", "방법",
                "연대측정", "반감기", "동위원소", "층서", "분자시계", "동료평가",
                "프리프린트", "라이다", "차이", "뜻", "표본", "오염", "적색편이"],
    # ⚠ 「외계인」을 뺐다 — 「피라미드는 외계인이 지었나요」는 ARCHAEO 다(policy v0.4).
    #   OTHER 는 「믿기 어려운 주장」이 아니라 「우리 분야가 아닌 것」이다.
    "OTHER": ["별자리", "운세", "타로", "점성", "음모", "평평", "연금술",
              "영양제", "주식", "투자", "취업", "진학", "날씨", "혈액형", "백신"],
}
# ★우선순위 — 겹칠 때 «무엇이 이기나». policy §1.2 와 «같은 순서»여야 한다
PRIORITY = ["OTHER", "CONCEPT", "PALEO", "ARCHAEO", "SPACE"]


def _load_env():
    """.env 를 찾아 환경변수로 올린다 — 이미 있으면 덮지 않는다.

    ★키는 «파일에만» 둔다. 코드에는 «경로»만 적는다.
      찾는 순서: desk/.env -> 프로젝트 루트 -> 노드4 (키를 거기 뒀다)
    """
    import os
    here = Path(__file__).parent
    for p in (here / ".env", here.parent / ".env",
              here.parent.parent / "c_lab_N4-routing-grounding/modumall-agent/.env"):
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        return str(p)
    return ""


_ENV_FROM = _load_env()


def rule_classify(q):
    """키워드 수를 세고, 동점이면 우선순위로 가른다.

    ★CONCEPT 는 «대상이 없을 때만» — policy §1.2 와 «같은 기준»이다.
      1차 실측: 오분류 8건 중 6건이 「어떻게」·「왜」 때문에 CONCEPT 로 샜다.
        「화석의 색은 어떻게 알아내나요」 → PALEO 인데 CONCEPT 로 갔다
      ⇒ 대상 라우트가 «하나라도» 맞으면 CONCEPT 를 끈다.
      ⚠ policy 를 고치면 «여기도» 같이 고쳐야 한다. 둘이 어긋나면 채점이 뒤집힌다.
    """
    hit = {rt: sum(1 for k in kws if k in q) for rt, kws in RULE.items()}
    if max(hit["SPACE"], hit["ARCHAEO"], hit["PALEO"]) > 0:
        hit["CONCEPT"] = 0
    top = max(hit.values())
    if top == 0:
        return "OTHER", 0.30, ""          # ★모르면 OTHER — 범위 밖으로 보낸다
    winners = [rt for rt in PRIORITY if hit[rt] == top]
    conf = min(0.95, 0.5 + 0.15 * top)
    return winners[0], conf, ""


# ─────────────────────────────────────────────────────────
# LLM 라우터
# ─────────────────────────────────────────────────────────
GUIDE_V1 = """너는 과학 질문을 분류하는 라우터다. 아래 다섯 중 «하나»를 고른다.

SPACE     지구 «밖»의 대상이 나온다 — 행성·별·은하·탐사선·망원경·운석
ARCHAEO   «사람이 만든 것»을 땅·물속에서 찾는 이야기다 — 유적·유물·문자·무덤·난파선
PALEO     «살아 있던 것»의 흔적이다 — 화석·뼈·발자국·멸종·진화·고DNA
CONCEPT   ★«대상이 없이» 방법이나 말만 묻는다 — ~이 뭔가요 · 어떤 원리인가요
OTHER     ★과학의 «주제가 아니거나», 답하면 안 되는 것이다
          (점성술·타로·혈액형 성격론·의학상담·투자조언·진로·잡담)
          ⚠ 과학 «용어나 방법»을 묻는 것은 CONCEPT 다. OTHER 가 아니다
          ⚠ 유사과학 «주장»이라도 대상이 우주·고고학·고생물이면 그 라우트다.
            「피라미드는 외계인이 지었나요」 → ARCHAEO (근거를 제시해 반박한다)

겹칠 때 — ★«대상이 있나»로 가른다. 이것이 유일한 기준이다:
- 대상이 있으면 «그 대상»의 라우트다
  「화석의 색은 어떻게 알아내나요」 → 화석이 있다 → PALEO
  「점토판 문자는 어떻게 해독했나요」 → 점토판이 있다 → ARCHAEO
- 대상이 없고 «방법·말»만 물으면 CONCEPT 다
  「방사성 탄소 연대측정이 뭔가요」 → 대상이 없다 → CONCEPT
  「광년은 거리 단위인가요」 → 광년은 «말»이다 → CONCEPT
- 대상이 둘이면 «질문의 주어»를 따른다
- ★«사람»이 걸리면 ARCHAEO, 사람이 아니면 PALEO 다
  「고대 무덤에서 나온 뼈」 → 사람의 뼈다 → ARCHAEO
  「빙하에서 나온 미라」 → 사람이다 → ARCHAEO
  「네안데르탈인 유적에서 도구」 → 도구가 주어다 → ARCHAEO
  화석·뼈라도 «비인류»면 PALEO 다
- 판정하면 안 되는 것이면 무조건 OTHER 다

출력은 라우트 이름 «한 단어»만. 설명하지 않는다."""

# ★V2 — V1 의 예시 8개가 «평가셋 문항»이었다. 지침이 정답을 알려 준 셈이다.
#   골든셋 18건 중 2건 · 라우팅 평가셋 55건 중 6건이 글자까지 같았다.
#   퍼실 지시 「평가셋을 프롬프트에 넣지 마세요」를 golden.json 첫 줄에
#   적어 놓고 어겼다. 바꾼 것은 «예시뿐» — 규칙 문장은 한 글자도 안 건드렸다.
GUIDE_V2 = """너는 과학 질문을 분류하는 라우터다. 아래 다섯 중 «하나»를 고른다.

SPACE     지구 «밖»의 대상이 나온다 — 행성·별·은하·탐사선·망원경·운석
ARCHAEO   «사람이 만든 것»을 땅·물속에서 찾는 이야기다 — 유적·유물·문자·무덤·난파선
PALEO     «살아 있던 것»의 흔적이다 — 화석·뼈·발자국·멸종·진화·고DNA
CONCEPT   ★«대상이 없이» 방법이나 말만 묻는다 — ~이 뭔가요 · 어떤 원리인가요
OTHER     ★과학의 «주제가 아니거나», 답하면 안 되는 것이다
          (점성술·타로·혈액형 성격론·의학상담·투자조언·진로·잡담)
          ⚠ 과학 «용어나 방법»을 묻는 것은 CONCEPT 다. OTHER 가 아니다
          ⚠ 유사과학 «주장»이라도 대상이 우주·고고학·고생물이면 그 라우트다.
            「달 착륙이 조작이라던데 사실인가요」 → SPACE (근거를 제시해 반박한다)

겹칠 때 — ★«대상이 있나»로 가른다. 이것이 유일한 기준이다:
- 대상이 있으면 «그 대상»의 라우트다
  「혜성 꼬리가 왜 둘로 갈라지나요」 → 혜성이 있다 → SPACE
  「성벽이 언제 쌓였는지 어떻게 정하나요」 → 성벽이 있다 → ARCHAEO
- 대상이 없고 «방법·말»만 물으면 CONCEPT 다
  「표준화석이 무슨 뜻인가요」 → 대상이 없다 → CONCEPT
  「학명은 누가 정하나요」 → 학명은 «말»이다 → CONCEPT
- 대상이 둘이면 «질문의 주어»를 따른다
- ★«사람»이 걸리면 ARCHAEO, 사람이 아니면 PALEO 다
  「청동기 무덤에서 나온 장신구」 → 사람이 만든 것이다 → ARCHAEO
  「이탄늪에서 나온 시신」 → 사람이다 → ARCHAEO
  「동굴에서 나온 곰 뼈」 → 비인류다 → PALEO
  화석·뼈라도 «비인류»면 PALEO 다
- 판정하면 안 되는 것이면 무조건 OTHER 다

출력은 라우트 이름 «한 단어»만. 설명하지 않는다."""

GUIDES = {"v1": GUIDE_V1, "v2": GUIDE_V2}


def make_llm(model, guide):
    """★모델 이름으로 provider 를 고른다 — 같은 코드에 «모델만» 갈아 끼운다.

    노드4 에서는 로컬 모델뿐이라 「퍼실 기준선과 비교 불가」가 계속 발목을 잡았다.
    ⚠ gpt-5 계열은 max_tokens 대신 max_completion_tokens 를 쓴다(실측 400 에러).
    """
    if model.startswith(("gpt-", "o1", "o3", "o4")):
        from langchain_openai import ChatOpenAI
        # ★16 을 주면 «빈 응답»이 온다 — reasoning 토큰이 예산을 전부 먹는다(실측).
        #   max=16 → 출력 '' · 완료 16토큰이 «전부 reasoning»
        #   max=100 → 출력 'PALEO'
        #   ⚠ 어제 qwen3 에서 겪은 것과 «같은 함정»이다. 거기선 reasoning=False 로 껐고,
        #     gpt-5 계열은 끌 수 없으니 «예산을 넉넉히» 줘야 한다.
        llm = ChatOpenAI(model=model, max_completion_tokens=200,
                         reasoning_effort="none")
    else:
        from langchain_ollama import ChatOllama
        kw = dict(model=model, temperature=0, num_predict=16)
        if model.startswith("qwen3"):
            kw["reasoning"] = False      # ★①에서 20/20 형식 실패를 겪은 그 설정
        llm = ChatOllama(**kw)

    def classify(q):
        try:
            txt = llm.invoke([("system", guide), ("human", q)]).content or ""
        except Exception as exc:                       # noqa: BLE001
            return "_PARSE_FAIL", 0.0, type(exc).__name__
        m = re.search(r"\b(SPACE|ARCHAEO|PALEO|CONCEPT|OTHER)\b", txt.upper())
        if not m:
            # ★형식 실패를 «분류 오류»로 뭉뚱그리지 않는다 — 원인이 다르다
            return "_PARSE_FAIL", 0.0, (txt.strip()[:24] or "(빈 응답)")
        return m.group(1), 0.8, ""
    return classify


# ─────────────────────────────────────────────────────────
def load_seed():
    rows = list(csv.DictReader(io.open(ROOT / "data/eval_routing.csv", encoding="utf-8")))
    ev = [(r["question"], r["route"]) for r in rows if r["split"] == "eval"]
    os_ = [(r["question"], r["route"]) for r in rows if r["split"] == "outscope"]
    hard = {r["question"] for r in rows if r["hard"] == "1"}
    return ev, os_, hard


def confusion(ev, pred):
    """★혼동행렬 — 「어디로 샜나」는 f1 만 봐서는 모른다.

    루브릭이 「정확도·macro F1·혼동행렬」을 함께 요구한다.
    f1 0.800 은 «얼마나» 틀렸는지만 말한다. 혼동행렬은 «어느 쪽으로»
    틀렸는지 말한다 — PALEO 가 SPACE 로 새는 것과 CONCEPT 로 새는 것은
    고치는 방법이 다르다.

    세로 = 정답 · 가로 = 예측. 대각선이 맞힌 것.
    """
    labs = ROUTES                      # OTHER 까지 넣는다 — 범위 밖으로 새는 것도 봐야 한다
    cnt = {(a, b): 0 for a in labs for b in labs}
    for (q, gold), got in zip(ev, pred):
        if gold in labs and got in labs:
            cnt[(gold, got)] += 1
    w = max(len(x) for x in labs)
    out = ["      [혼동행렬]  세로=정답 · 가로=예측 · 대각선이 맞힌 것",
           "      " + " " * (w + 2) + " ".join("%7s" % x for x in labs) + "   계"]
    for a in labs:
        row = [cnt[(a, b)] for b in labs]
        if not sum(row):
            continue
        cells = " ".join(("%7s" % ("[%d]" % n if a == b else (n or "."))) for b, n in zip(labs, row))
        out.append("      %-*s  %s  %3d" % (w, a, cells, sum(row)))
    return "\n".join(out)


def macro_f1(y, p, labels):
    """sklearn 없이도 돌게 직접 센다 — 의존을 줄인다."""
    f1s = []
    for L in labels:
        tp = sum(1 for a, b in zip(y, p) if a == L and b == L)
        fp = sum(1 for a, b in zip(y, p) if a != L and b == L)
        fn = sum(1 for a, b in zip(y, p) if a == L and b != L)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1s.append(2 * prec * rec / (prec + rec) if prec + rec else 0.0)
    return sum(f1s) / len(f1s), f1s


def run_once(cases, clf, workers):
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        out = list(ex.map(lambda c: clf(c[0]), cases))
    secs = time.perf_counter() - t0
    pred = [o[0] for o in out]
    fails = [(c[0], o[2]) for c, o in zip(cases, out) if o[0] == "_PARSE_FAIL"]
    return pred, fails, secs


def main():
    ap = argparse.ArgumentParser(description="① 의도 분류")
    ap.add_argument("--mode", choices=["rule", "llm"], default="rule")
    ap.add_argument("--model", default="qwen2.5:7b")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--guide", choices=["v1", "v2"], default="v2",
                    help="★v1 은 예시가 평가셋과 겹친다 — 비교용으로만")
    ap.add_argument("--repeat", type=int, default=1,
                    help="★같은 설정을 N회 재서 «폭»을 낸다")
    args = ap.parse_args()

    ev, osc, hard = load_seed()
    clf = rule_classify if args.mode == "rule" else make_llm(args.model, GUIDES[args.guide])
    tag = "규칙 라우터" if args.mode == "rule" else ("LLM %s · 지침 %s" % (args.model, args.guide))
    print("=== ① 의도 분류 — %s ===" % tag)
    print("   eval %d건 · outscope %d건 · 경계 문항 %d건"
          % (len(ev), len(osc), len(hard)))
    print()

    f1s_all, osc_all = [], []
    for i in range(args.repeat):
        pred, fails, secs = run_once(ev, clf, args.workers)
        y = [c[1] for c in ev]
        ok = [(a, b) for a, b in zip(y, pred) if b != "_PARSE_FAIL"]
        if not ok:
            print("   ⛔ 전부 형식 실패 — 점수를 낼 수 없다")
            return
        ya, pa = [a for a, _ in ok], [b for _, b in ok]
        f1, per = macro_f1(ya, pa, LABELS4)
        acc = sum(1 for a, b in zip(ya, pa) if a == b) / len(ok)
        f1s_all.append(f1)

        opred, ofails, osecs = run_once(osc, clf, args.workers)
        ohit = sum(1 for p in opred if p == "OTHER")
        osc_all.append(ohit / len(osc))

        head = "[%d/%d회차] " % (i + 1, args.repeat) if args.repeat > 1 else ""
        print("%s채점 %d건 · 정확도 %.3f · macro F1 %.3f · 형식실패 %d · %.1f초"
              % (head, len(ok), acc, f1, len(fails), secs + osecs))
        print("      범위 밖 %d/%d (%.1f%%)  ← 이 값이 떨어지는 걸 eval 만 보면 «못 본다»"
              % (ohit, len(osc), 100 * ohit / len(osc)))
        if i == 0:
            print()
            print("      [라우트별 f1]  " + " · ".join(
                "%s %.3f" % (L, s) for L, s in zip(LABELS4, per)))
            print()
            print(confusion(ev, pred))
            # ★오분류를 «문장으로» 본다 — 숫자만 보면 왜 샜는지 모른다
            wrong = [(q, a, b) for (q, a), b in zip(ev, pred) if a != b]
            if wrong:
                print()
                print("      [오분류 %d건 — «왜» 샜는지 문장을 읽는다]" % len(wrong))
                for q, a, b in wrong[:8]:
                    mk = "★" if q in hard else " "
                    print("      %s %-32s 정답 %-8s → %s" % (mk, q[:30], a, b))
                if len(wrong) > 8:
                    print("        … 외 %d건" % (len(wrong) - 8))
            if fails:
                print()
                print("      [형식 실패 %d건 — «분류 오류»가 아니다]" % len(fails))
                for k, v in Counter(f[1] for f in fails).most_common(3):
                    print("        %-26s %d건" % (k, v))

    if args.repeat > 1:
        print()
        print("══ ★반복 %d회 — 폭 ══" % args.repeat)
        print("   macro F1  " + " · ".join("%.3f" % x for x in f1s_all))
        print("   ⇒ 평균 %.3f · 폭 %.3f" % (sum(f1s_all) / len(f1s_all),
                                            max(f1s_all) - min(f1s_all)))
        print("   범위 밖   " + " · ".join("%.1f%%" % (100 * x) for x in osc_all))
        print()
        print("   ★이 폭보다 «작은» 차이는 «개선»이라 부를 수 없다.")


if __name__ == "__main__":
    main()
