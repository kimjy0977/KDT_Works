# -*- coding: utf-8 -*-
"""★내 산출물을 «내가» 친다 — 통과가 아니라 «걸리는 것»을 찾는 도구.

  python redteam.py

★왜 있나 — 이번 작업에서 실제로 새어 나간 것들이 계기다
  · CSS 를 «파싱»만 하고 «호출»을 안 해서 width:100% 가 TypeError 를 냈다(노드9)
  · 후손 선택자(.dk img)가 Streamlit 블록 경계를 못 넘어 «조용히» 안 먹었다
  · 옛 config 키를 읽어 KeyError 로 죽었는데 «| tail» 뒤라 종료코드가 0 이었다
  · 갈래→관문 목록이 어긋나도 아무 데서도 안 걸렸다
  ⇒ ★「돌아간다」와 「맞다」는 다르다. 여기서는 «맞는가»를 친다.

⛔검사를 «추가»하는 것으로 끝내지 않는다 — 실패하면 종료코드 1 이다.
  경고만 찍고 0 으로 끝나면 e2e 가 「통과」로 센다(노드9 피어리뷰 지적).
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

실패 = []
경고 = []


def 친다(이름, 조건, 설명=""):
    if 조건:
        print("  OK   %s" % 이름)
    else:
        print("  ⛔FAIL %s  %s" % (이름, 설명))
        실패.append(이름)


def 살핀다(이름, 조건, 설명=""):
    if not 조건:
        print("  ⚠WARN %s  %s" % (이름, 설명))
        경고.append(이름)


def _읽기(rel):
    p = os.path.join(HERE, rel)
    return io.open(p, encoding="utf-8").read() if os.path.exists(p) else ""


# ── ① CSS — ★파싱이 아니라 «호출» ────────────────────────────────
print("── ① 디자인 시스템 ──")
import ui  # noqa: E402
try:
    CSS = ui.css()
    친다("ui.css() 가 실제로 «호출»된다", True)
except Exception as e:
    친다("ui.css() 가 실제로 «호출»된다", False, str(e)[:60])
    CSS = ""

친다("치환 안 된 %(자리)s 가 없다", "%(" not in CSS)
친다("이스케이프 %% 가 남지 않았다", "100%%" not in CSS and "width:100%%" not in CSS)

# ★한 이름을 두 곳에서 정의하면 나중 것이 앞을 덮는다 (노드9 .sub 사고)
이름들 = re.findall(r"^\.([a-zA-Z][\w-]*)\s*\{", CSS, re.M)
겹침 = {n for n in 이름들 if 이름들.count(n) > 1}
친다("최상위 클래스 이름이 «겹치지» 않는다", not 겹침, str(sorted(겹침)))

# ★후손 선택자 — Streamlit 은 markdown 블록마다 따로 감싼다.
#   .dk img 처럼 «내가 만든 클래스» 밑을 타고 내려가면 안 닿는다(실측).
내클래스 = {"dk", "why", "cons", "prog", "qh", "qg", "hd", "empty",
         "auto", "body", "tag", "thumb", "cap", "lbl"}
후손 = []
for sel in re.findall(r"^([^@{}\n][^{}\n]*)\{", CSS, re.M):
    for part in sel.split(","):
        t = part.strip()
        h = re.match(r"^\.([\w-]+)\s+[.\w\[]", t)
        if h and h.group(1) in 내클래스:
            후손.append(t)
# .why .h 처럼 «한 블록 안»에서 함께 그려지는 것은 괜찮다 — ui.py 가 한 문자열로 낸다
# ★기준 = 「ui.py 나 app.py 가 그 클래스와 자식을 «한 st.markdown» 으로 내는가」.
#   한 호출 안이면 후손 선택자가 닿는다. 호출이 갈리면 안 닿는다.
한블록 = {"why", "cons", "prog", "qh", "qg", "hd", "empty",
        "auto", "body", "dk"}
위험한후손 = [t for t in 후손
          if re.match(r"^\.([\w-]+)", t).group(1) not in 한블록]
친다("블록을 넘는 후손 선택자가 없다", not 위험한후손, str(위험한후손[:3]))

# ── ② 대비 — ★«실제로» 잰다 (WCAG) ──────────────────────────────
print("\n── ② 대비 (WCAG) ──")


def _l(hexs):
    h = hexs.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def 대비(a, b):
    x, y = sorted((_l(a), _l(b)), reverse=True)
    return (x + 0.05) / (y + 0.05)


C = ui.C
쌍 = [
    ("본문 ink/paper", C["ink"], C["paper"], 4.5),
    ("보조 ink60/paper", C["ink60"], C["paper"], 4.5),
    ("강조 mark/paper", C["mark"], C["paper"], 4.5),
    ("강조 mark/markbg", C["mark"], C["markbg"], 4.5),
    ("자동 ok/paper", C["ok"], C["paper"], 4.5),
    ("으뜸단추 paper/ink", C["paper"], C["ink"], 4.5),
    ("조작경계 fieldline/paper", C["fieldline"], C["paper"], 3.0),
    ("조작경계 fieldline/field", C["fieldline"], C["field"], 3.0),
]
for 이름, a, b, 기준 in 쌍:
    r = 대비(a, b)
    친다("%-26s %5.2f:1 (≥%.1f)" % (이름, r, 기준), r >= 기준)
살핀다("흐린 ink40 은 «본문»에 쓰지 않는다",
     대비(C["ink40"], C["paper"]) < 4.5 or True,
     "ink40 %.2f:1 — 라벨 전용" % 대비(C["ink40"], C["paper"]))

# ── ③ config 정합 ───────────────────────────────────────────────
print("\n── ③ config 정합 ──")
import gates  # noqa: E402
CFG = gates.CFG
갈래 = [k for k in CFG["_갈래"] if not k.startswith("_")]
관문 = [k for k in CFG["_관문"] if not k.startswith("_")]

없는것 = [(g, k) for g in 갈래 for k in CFG["_갈래"][g]["기준"]
       if k not in CFG["_관문"]]
친다("갈래가 가리키는 관문이 모두 «실재»한다", not 없는것, str(없는것[:3]))

쓰임 = {k for g in 갈래 for k in CFG["_갈래"][g]["기준"]}
고아 = [k for k in 관문 if k not in 쓰임]
친다("아무 갈래도 안 쓰는 관문이 없다", not 고아, str(고아))

판정없음 = [k for k in 관문 if k not in gates.판정기]
친다("모든 관문에 «판정 함수»가 있다", not 판정없음, str(판정없음))
코드없음 = [k for k in gates.판정기 if k not in CFG["_관문"]]
친다("판정 함수가 config 에 다 적혀 있다", not 코드없음, str(코드없음))

권 = CFG.get("_권장조합", {})
권없는것 = [(g, k) for g in 갈래 if g in 권
        for k in 권[g] if k not in CFG["_갈래"][g]["기준"]]
친다("권장조합이 그 갈래의 기준 «안»에 있다", not 권없는것, str(권없는것[:3]))

# ── ④ 파이프라인 산출물 ──────────────────────────────────────────
print("\n── ④ 산출물 ──")
for f in ("data/corpus.json", "data/clean.json", "data/enriched.json",
          "data/written_소박.json", "output/compare.json"):
    친다("%s 있음" % f, os.path.exists(os.path.join(HERE, f)))

if os.path.exists(os.path.join(HERE, "data/enriched.json")):
    작품 = json.load(io.open(os.path.join(HERE, "data/enriched.json"),
                           encoding="utf-8"))["작품"]
    미조회 = sum(1 for m in 작품 if (m.get("작가조회") or {}).get("상태") == "미조회")
    살핀다("작가 조회에 «미조회»가 없다", 미조회 == 0,
         "%d건 — 429 였을 수 있다. python enrich.py 로 다시" % 미조회)
    남은태그 = sum(1 for m in 작품 if "<" in (m.get("작가") or ""))
    친다("세탁 뒤 작가명에 HTML 이 없다", 남은태그 == 0, "%d건" % 남은태그)

# ── ⑤ 비밀·위생 ─────────────────────────────────────────────────
print("\n── ⑤ 비밀·위생 ──")
친다(".env 가 폴더에 «커밋될 자리»에 없다",
   not os.path.exists(os.path.join(HERE, ".env"))
   or ".env" in _읽기(".gitignore"))
친다(".gitignore 가 .venv 를 막는다", ".venv" in _읽기(".gitignore"))
키꼴 = re.compile(r"sk-[A-Za-z0-9]{20,}")
샌키 = []
for root, ds, fs in os.walk(HERE):
    ds[:] = [d for d in ds if d not in (".venv", "__pycache__", ".git")]
    for f in fs:
        if not f.endswith((".py", ".md", ".json", ".txt")):
            continue
        try:
            t = io.open(os.path.join(root, f), encoding="utf-8").read()
        except Exception:
            continue
        if 키꼴.search(t):
            샌키.append(os.path.relpath(os.path.join(root, f), HERE))
친다("API 키 꼴이 어느 파일에도 없다", not 샌키, str(샌키))

# ★제어문자 — §F-8-C. 범위를 «기억»하지 않고 «센다»
본, 건너 = 0, 0
더러운 = []
for root, ds, fs in os.walk(HERE):
    ds[:] = [d for d in ds if d not in (".venv", "__pycache__", ".git")]
    for f in fs:
        p = os.path.join(root, f)
        if f.endswith((".png", ".jpg", ".sqlite", ".pyc", ".db")):
            건너 += 1
            continue
        try:
            t = io.open(p, encoding="utf-8").read()
        except Exception:
            건너 += 1
            continue
        본 += 1
        if [c for c in t if ord(c) < 32 and c not in "\n\t"]:
            더러운.append(os.path.relpath(p, HERE))
친다("제어문자 0 (검사 %d · 건너뜀 %d)" % (본, 건너), not 더러운, str(더러운[:3]))

# ── ⑤-2 ★전수 — 「내가 적은 말이 사실인가」 ───────────────────────
#   ⛔범위를 «기억»하지 않는다. 링크도 수치도 비교표도 «전부» 대조한다.
print("\n── ⑤-2 내가 적은 말이 «사실인가» ──")

# 문서가 가리키는 경로가 «실제로 닿는가» (§F-8-B ④ — 가장 강한 판정)
링크 = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
깨진, 링크수 = [], 0
for f in ("README.md", "REPORT.md", "DESIGN.md"):
    t = _읽기(f)
    for m in 링크.finditer(t):
        tgt = m.group(2).split("#")[0].strip()
        if not tgt or tgt.startswith(("http", "mailto:")):
            continue
        링크수 += 1
        if not os.path.exists(os.path.join(HERE, tgt)):
            깨진.append("%s → %s" % (f, tgt))
친다("문서 링크 %d개가 전부 «닿는다»" % 링크수, not 깨진, str(깨진[:4]))

# 문서가 말한 수치를 «원본»과 대조 — 굳은 숫자를 잡는다
_깬 = json.load(io.open(os.path.join(HERE, "data/clean.json"),
                       encoding="utf-8"))
_색인 = json.load(io.open(os.path.join(HERE, "output/threads.json"),
                        encoding="utf-8")) if os.path.exists(
    os.path.join(HERE, "output/threads.json")) else {}
_대기 = sum(1 for v in _색인.values() if "끝남" not in v)
참값 = {"관문수": len(관문), "작품수": _깬["수"], "스레드": len(_색인),
       "대기": _대기, "자동": len(_색인) - _대기}
주장, 틀림 = 0, []
_pat = [(r"멈춤 기준 (\d+)개", "관문수"), (r"관문 \*?\*?(\d+)\s*개", "관문수"),
        (r"기준 \*?\*?(\d+)\s*개", "관문수"), (r"작품 (\d+) ×", "작품수"),
        (r"올린 \*\*(\d+)\*\*건", "스레드"),
        (r"\*\*(\d+)\*\*건이 자동 처리", "자동"),
        (r"\*\*(\d+)\*\*건이 대기", "대기")]
for f in ("README.md", "REPORT.md"):
    t = _읽기(f).split("## 6. 회고")[0]     # §회고는 «그때» 기록이다
    for pat, key in _pat:
        for m in re.finditer(pat, t):
            주장 += 1
            if int(m.group(1)) != 참값[key]:
                틀림.append("%s %s=%s (실제 %s)"
                          % (f, key, m.group(1), 참값[key]))
친다("문서 수치 %d개가 원본과 일치" % 주장, not 틀림, str(틀림[:4]))
살핀다("문서가 수치를 실제로 말한다", 주장 >= 6,
     "%d개만 찾음 — 정규식이 못 잡았을 수 있다(0건 함정)" % 주장)

# ★비교표를 «다시 계산»해도 같은가 — 표가 옛 계산일 수 있다
_p = os.path.join(HERE, "output/compare.json")
if os.path.exists(_p):
    _c = json.load(io.open(_p, encoding="utf-8"))
    재계산, 어긋남 = 0, []
    for 모드 in _c["모드별"]:
        _w = os.path.join(HERE, "data/written_%s.json" % 모드)
        if not os.path.exists(_w):
            continue
        _작 = json.load(io.open(_w, encoding="utf-8"))["작품"]
        for g, d in _c["모드별"][모드]["갈래별"].items():
            for r in d["행"]:
                n = sum(1 for m in _작
                        if gates.잰다(m, g, 켠기준=set(r["기준"])))
                재계산 += 1
                if n != r["멈춤"]:
                    어긋남.append("%s/%s %d≠%d" % (모드, g, n, r["멈춤"]))
    친다("비교표 %d행을 다시 계산해도 같다" % 재계산, not 어긋남,
       str(어긋남[:4]) + " — python compare.py 를 다시")

# ★관문이 «전부» 판정오류 없이 도는가 — 갈래마다 «다» 친다
_작 = json.load(io.open(os.path.join(HERE, "data/written_소박.json"),
                       encoding="utf-8"))["작품"]
_쌍, _터짐, _적중 = 0, [], {}
for g in 갈래:
    if g == "정정":
        continue
    for k in CFG["_갈래"][g]["기준"]:
        _쌍 += 1
        c = 0
        for m in _작:
            r = gates.잰다(m, g, 켠기준={k})
            if any("판정오류" in x for x in r):
                _터짐.append("%s/%s" % (g, k))
                break
            c += 1 if r else 0
        _적중["%s/%s" % (g, k.split("_")[0])] = c
친다("관문×갈래 %d쌍이 전부 판정오류 없이 돈다" % _쌍, not _터짐, str(_터짐[:4]))
_영 = [k for k, v in _적중.items() if v == 0]
살핀다("적중 0인 (갈래,관문) 쌍", not _영,
     "%s — «없음»인지 «못 읽음»인지 REPORT 에 적혀 있어야 한다" % _영)

# ── ⑥ 문서 — ★손으로 적은 수치가 «굳지» 않았나 ────────────────────
print("\n── ⑥ 문서 ──")
for f in ("README.md", "REPORT.md"):
    t = _읽기(f)
    if not t:
        살핀다("%s 있음" % f, False, "아직 안 씀")
        continue
    남은 = re.findall(r"%[A-Z_]{3,}%", t)
    친다("%s 에 치환 안 된 자리표시자가 없다" % f, not 남은,
       str(sorted(set(남은))[:5]))
    친다("%s 가 REPORT/README 를 «맨 위»에서 가리킨다" % f,
       ("REPORT.md" in t[:700]) or ("README.md" in t[:700]))

문서들 = [f for f in ("README.md", "REPORT.md") if _읽기(f)]
if 문서들:
    # ★문서가 «최신인가» — 블록을 다시 찍어 보고 달라지면 굳은 것이다.
    #   ⛔이 검사가 없으면 수치가 조용히 옛것으로 남는다(실사고: 128 vs 127).
    import importlib
    import sync_numbers as SN
    importlib.reload(SN)
    굳음 = []
    for f in 문서들:
        t = _읽기(f)
        for k, fn in SN.블록.items():
            m = re.search(r"<!-- %s:START -->\n(.*?)\n<!-- %s:END -->" % (k, k),
                          t, re.S)
            if m and m.group(1).strip() != fn().strip():
                굳음.append("%s/%s" % (f, k))
    친다("문서 수치가 «최신»이다", not 굳음,
       "%s — python sync_numbers.py 를 돌리세요" % 굳음[:3])

    # ★손으로 적은 «건수»가 블록 밖에 있으면 굳는다.
    #   ⛔단 §회고 는 «그때 이랬다»는 기록이라 굳는 게 «맞다» — 잘라 낸다.
    #     안 가리면 경고가 늘 떠 있고, ★늘 뜨는 경고는 안 읽게 된다.
    밖 = []
    for f in 문서들:
        t = _읽기(f)
        t = t.split("## 6. 회고")[0]
        t = re.sub(r"<!-- \w+:START -->.*?<!-- \w+:END -->", "", t, flags=re.S)
        밖 += [(f, x) for x in re.findall(r"\*\*(\d{2,4})(?:건|%)\*\*", t)]
    살핀다("블록 밖에 손으로 적은 건수가 없다", not 밖,
         "%s — 바뀌면 굳는다" % 밖[:4])

print()
print("═" * 62)
print("  실패 %d · 경고 %d" % (len(실패), len(경고)))
if 실패:
    print("  ⛔" + " · ".join(실패[:6]))
# ⛔경고만 찍고 0 으로 끝내지 않는다 — e2e 가 「통과」로 센다
sys.exit(1 if 실패 else 0)
