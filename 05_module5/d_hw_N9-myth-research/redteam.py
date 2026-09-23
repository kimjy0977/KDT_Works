# -*- coding: utf-8 -*-
"""★레드팀 — 「내가 채점자라면 어디를 칠까」를 «코드로» 친다.

  python redteam.py

왜 스크립트로 만드나
  머리로 훑으면 «눈에 띄는 것»만 본다. 노드8 에서 겪었다 —
  「범위를 넓히는 경주는 이길 수 없다」. 그래서 ★항목을 박아 두고 «돌린다».

⛔이 파일이 통과한다고 «좋은 제출물»이라는 뜻이 아니다.
  이건 그물이다. 잣대는 사람이 읽어서 댄다.
"""
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OK, WARN, BAD = "OK  ", "WARN", "★BAD"
결과 = []


def 친다(이름, 판정, 말):
    결과.append((판정, 이름, 말))


def rd(p):
    q = os.path.join(HERE, p)
    return io.open(q, encoding="utf-8").read() if os.path.exists(q) else None


def jd(p):
    s = rd(p)
    return json.loads(s) if s else None


# ── ① 재현 — 채점자가 첫 줄에서 막히나 ──────────────────────────
for f in ("requirements.txt", ".env.example", "README.md", "REPORT.md",
          "config.json", "data/questions.json", "data/corpus.json"):
    친다("파일 %s" % f, OK if rd(f) is not None else BAD,
       "있다" if rd(f) is not None else "★README 가 시키는데 «없다»")

rm = rd("README.md") or ""
for cmd in re.findall(r"^python ([a-z_]+\.py)", rm, re.M):
    친다("README 명령 %s" % cmd,
       OK if os.path.exists(os.path.join(HERE, cmd)) else BAD,
       "파일 있다" if os.path.exists(os.path.join(HERE, cmd))
       else "★README 가 시키는 파일이 없다")

# ── ② 비밀 — 키가 섞여 갔나 ────────────────────────────────────
pat = re.compile(r"sk-(proj|ant)-[A-Za-z0-9_-]{20}|ghp_[A-Za-z0-9]{36}|AKIA[0-9A-Z]{16}")
샌것 = []
for root, ds, fs in os.walk(HERE):
    ds[:] = [d for d in ds if d not in ("__pycache__", ".venv", ".git")]
    for f in fs:
        if f == ".env" or f.endswith((".png", ".pyc")):
            continue
        p = os.path.join(root, f)
        try:
            if pat.search(io.open(p, encoding="utf-8", errors="ignore").read()):
                샌것.append(os.path.relpath(p, HERE))
        except Exception:
            pass
친다("API 키 유출", OK if not 샌것 else BAD,
   "0건" if not 샌것 else "★" + ", ".join(샌것))
친다(".env 가 무시되나", OK if ".env" in (rd(".gitignore") or "") else BAD,
   ".gitignore 에 있다")

# ── ③ 문서가 «지금»을 말하나 ───────────────────────────────────
ab = jd("output/ablation.json")
if ab:
    rows = ab["rows"]
    같은 = ("전부 켬 (기준선)", "★기준선 (재측정)", "★축 A — 주제 (우리 설정)")
    pool = [x["근거율"] for r in rows if r["조건"] in 같은
            for x in r.get("_회차별", [])]
    잡음 = (max(pool) - min(pool)) * 100 if pool else None
    if 잡음 is not None:
        for d in ("README.md", "REPORT.md"):
            t = rd(d) or ""
            친다("%s 잡음 수치" % d,
               OK if ("%.1f%%p" % 잡음) in t else WARN,
               "본문이 %.1f%%p 를 말한다" % 잡음 if ("%.1f%%p" % 잡음) in t
               else "★sync_numbers.py --write 를 안 돌렸나")
    친다("회차별 원시값 보존", OK if rows[0].get("_회차별") else BAD,
       "%d회분 남아 있다" % len(rows[0].get("_회차별", [])))

# ── ④ ★대조군이 «묶이지» 않았나 (요건이 직접 경고) ────────────────
bl = [json.loads(l) for l in (rd("output/baseline.jsonl") or "").splitlines()
      if l.strip()]
if bl:
    f = bl[-1].get("공정성", {})
    친다("대조군 예산 소진",
       OK if f.get("실제읽음", 0) >= f.get("요구예산", 1) else BAD,
       "요구 %s / 실제 %s" % (f.get("요구예산"), f.get("실제읽음")))
    cfg = jd("config.json")
    친다("대조군 모델 동일",
       OK if f.get("모델") == cfg["모델"] else BAD, str(f.get("모델")))
else:
    친다("대조군 기록", WARN, "★baseline.jsonl 이 없다 — 돌린 적이 없나")

# ── ⑤ ★판정이 «한 곳»에만 있나 (UI 만들다 드러난 것) ──────────────
mt = rd("metrics.py") or ""
ap = rd("app.py") or ""
친다("절 판정 단일화",
   OK if "절판정" in mt and "절판정" in ap else BAD,
   "app 이 metrics.절판정 을 쓴다" if "절판정" in ap
   else "★화면과 계기판이 «다른 말»을 할 수 있다")

# ── ⑥ 지표마다 «어느 장치»인가 (요건) ───────────────────────────
try:
    sys.path.insert(0, HERE)
    from metrics import 지표사전
    빠진 = [k for k, v in 지표사전.items()
          if not v.get("장치") or not v.get("한 줄")]
    친다("지표사전 완전성", OK if not 빠진 else BAD,
       "%d개 전부 장치·한 줄 있음" % len(지표사전) if not 빠진 else str(빠진))
    경보수 = sum(1 for v in 지표사전.values() if "경보" in v["종류"])
    친다("신호/경보 분리", OK if 경보수 else BAD, "경보 %d · 신호 %d"
       % (경보수, len(지표사전) - 경보수))
except Exception as e:
    친다("지표사전", BAD, str(e)[:60])

# ── ⑦ ★루브릭 3항목을 문서가 «대답»하나 ─────────────────────────
rp = rd("REPORT.md") or ""
루브릭 = [
    ("① 여러 편을 나란히 읽고 자기 말로",
     ["나란히", "직접", "자기 말"]),
    ("① 마음에 안 드는 대목을 어느 절·자료까지 추적",
     ["마음에 안 드는", "추적"]),
    ("② 형식이 아닌 내용 단위로 나눴나",
     ["형식", "내용 단위", "축"]),
    ("② 역할·시작 자료·예산 배정",
     ["역할", "시작문서", "예산"]),
    ("③ 엔드투엔드 오류 없이",
     ["fetch_corpus", "run.py", "ablation"]),
]
for 이름, kws in 루브릭:
    hit = [k for k in kws if k in rp]
    친다("루브릭 %s" % 이름, OK if len(hit) >= 2 else WARN,
       "REPORT 에 %d/%d 키워드" % (len(hit), len(kws)))

# ── ⑧ 접근성 — 대비 (디자인 토큰) ──────────────────────────────
try:
    from ui import C

    def lum(h):
        h = h.lstrip("#")
        r, g, b = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        f = lambda c: c / 12.92 if c <= .03928 else ((c + .055) / 1.055) ** 2.4
        return .2126 * f(r) + .7152 * f(g) + .0722 * f(b)

    def cr(a, b):
        l = sorted([lum(a), lum(b)], reverse=True)
        return (l[0] + .05) / (l[1] + .05)

    for k, need in (("text", 4.5), ("dim", 4.5), ("faint", 3.0),
                    ("brass", 4.5), ("navy", 3.0)):
        v = cr(C[k], C["bg"])
        친다("대비 %s" % k, OK if v >= need else BAD,
           "%.2f:1 (요구 %.1f)" % (v, need))
    친다("순흑 금지", OK if C["bg"].lower() != "#000000" else BAD, C["bg"])
except Exception as e:
    친다("대비", WARN, str(e)[:50])

# ── ⑨ 이모지를 «구조 아이콘»으로 쓰나 ──────────────────────────
#   ⚠첫 판은 이모지를 «전부» 세서 ★ ⚠ ⛔ 까지 잡았다 — 그건 본문 «강조 문자»지
#     버튼·네비의 아이콘이 아니다. 규칙이 금지한 것은 «구조 아이콘»이다.
#   ⇒ 하네스에도 적혀 있다 — 「절반이 헛경고면 경고를 안 읽게 된다」.
#     검사기가 헛경고를 내면 ★«검사기를» 고친다.
강조 = set("★⚠⛔⇒·—«»①②③④⑤⑥⑦⑧⑨")
구조자리 = re.findall(
    r'(?:st\.(?:button|tabs|radio|checkbox|selectbox|metric)'
    r'|class="(?:const-n|eyebrow|g |doc|cite)")[^\n]{0,160}', ap)
emo = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF]")
쓴것 = sorted({c for blk in 구조자리 for c in emo.findall(blk)} - 강조)
친다("구조 아이콘에 이모지", OK if not 쓴것 else BAD,
   "0개 — 전부 인라인 SVG (stroke 1.5 통일)" if not 쓴것
   else "★" + " ".join(쓴것))
친다("인라인 SVG 사용", OK if "<svg" in (rd("ui.py") or "") else BAD,
   "ui.icon() 이 SVG 를 낸다")

# ── ⑨-2 ★엔드투엔드 기록이 있나 (루브릭 ③) ─────────────────────
e2 = jd("output/e2e.json")
if e2:
    # ★「통과 == 전체」로 보면 ⛔구조적으로 통과할 수 없다 —
    #   레드팀은 e2e 의 «마지막 단계»라 자기 자신이 아직 안 세어졌다.
    #   (두 번 같은 순환을 만들었다. 두 번째는 판정을 고쳐서 풀었다)
    #   ⇒ 「기록된 단계 중 «실패»가 있나」를 본다.
    실패 = [x["단계"] for x in e2["단계"] if not x["통과"]]
    친다("엔드투엔드 실행 기록", OK if not 실패 else BAD,
       "기록된 %d단계 전부 통과%s" % (len(e2["단계"]),
                                " (fresh)" if e2.get("fresh") else "")
       if not 실패 else "★실패: " + ", ".join(실패))
else:
    친다("엔드투엔드 실행 기록", BAD,
       "★output/e2e.json 이 없다 — python e2e.py 를 돌려라")


# ── ⑩ 문법 ────────────────────────────────────────────────────
import ast
for f in sorted(x for x in os.listdir(HERE) if x.endswith(".py")):
    try:
        ast.parse(rd(f))
        친다("문법 %s" % f, OK, "OK")
    except Exception as e:
        친다("문법 %s" % f, BAD, str(e)[:60])


# ── 출력 ──────────────────────────────────────────────────────
def main():
    print("═══ 레드팀 — 「내가 채점자라면 어디를 칠까」 ═══\n")
    for 판정 in (BAD, WARN, OK):
        묶음 = [r for r in 결과 if r[0] == 판정]
        if not 묶음:
            continue
        print("── %s (%d) ──" % (판정, len(묶음)))
        for _, 이름, 말 in 묶음:
            print("  %-34s %s" % (이름[:34], 말))
        print()
    n_bad = sum(1 for r in 결과 if r[0] == BAD)
    n_w = sum(1 for r in 결과 if r[0] == WARN)
    print("합계 %d항목 · ★BAD %d · WARN %d" % (len(결과), n_bad, n_w))
    print("\n⛔이걸 통과했다고 «좋은 제출물»이라는 뜻이 아니다. 이건 그물이다.")
    sys.exit(1 if n_bad else 0)


if __name__ == "__main__":
    main()
