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
    # ★목록은 compare.py 한 곳에만 — 옛 이름으로 10개만 모아
    #   잡음을 22.9%p 로 계산하고 헛경고를 냈다.
    from compare import 같은설정_원시값
    pool = 같은설정_원시값(rows)
    잡음 = (max(pool) - min(pool)) * 100 if pool else None
    if 잡음 is not None:
        for d in ("README.md", "REPORT.md"):
            t = rd(d) or ""
            # ⚠검사가 «화면에 찍히는 형태»와 달라 헛경고를 냈다.
            #   표는 「잡음 폭 25.6%p」로 쓴다 — ★실제 문자열을 찾는다.
            _찾 = "잡음 폭 %.1f%%p" % 잡음
            친다("%s 잡음 수치" % d, OK if _찾 in t else WARN,
               "본문이 %.1f%%p 를 말한다" % 잡음 if _찾 in t
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

# ── ⑧ 접근성 — 대비 (DESIGN.md 의 값을 «실제로» 잰다) ──────────
try:
    from ui import C as UIC

    def lum(h):
        h = h.lstrip("#")
        r, g, b = [int(h[k:k + 2], 16) / 255 for k in (0, 2, 4)]
        f = lambda c: c / 12.92 if c <= .03928 else ((c + .055) / 1.055) ** 2.4
        return .2126 * f(r) + .7152 * f(g) + .0722 * f(b)

    def cr(a, b):
        l = sorted([lum(a), lum(b)], reverse=True)
        return (l[0] + .05) / (l[1] + .05)

    bg = UIC["paper"]
    for k, need in (("ink", 12.0), ("ink60", 4.5), ("ink40", 3.0),
                    ("mark", 4.5)):
        v = cr(UIC[k], bg)
        친다("대비 %s" % k, OK if v >= need else BAD,
           "%.2f:1 (요구 %.1f)" % (v, need))
    v = cr(UIC["mark"], UIC["markbg"])
    친다("대비 경보 글자", OK if v >= 4.5 else BAD,
       "%.2f:1 (경보 바탕 위)" % v)
    친다("순백·순흑 금지",
       OK if not any(x.lower() in ("#ffffff", "#000000")
                     for x in UIC.values()) else BAD,
       "배경 %s · 본문 %s" % (UIC["paper"], UIC["ink"]))
    친다("유채색 개수",
       OK if len([1 for k in UIC if k in ("mark", "markbg")]) <= 2 else WARN,
       "mark 하나 + 경보 바탕 (조사관은 «선 모양»으로 가른다)")
except Exception as e:
    친다("대비", BAD, str(e)[:60])

# ── ⑨ ★AI 생성물 표식 16개 — 조사해서 넣었다 ────────────────────
#   2판 「성좌 필사본」이 이 중 ★9개를 밟고 있었다. 검사로 박아 둔다.
#   출처 — 2026 「AI design slop」 16 patterns
css = rd("ui.py") or ""
# ★선언만 추린다 — 주석·설명문은 «검사 대상이 아니다»
선언 = " ".join(l for l in css.splitlines() if "font-family" in l or "fonts.googleapis" in l or "family=" in l)
ap2 = ap + css
표식 = [
    ("#5 영구 다크모드", "base = \"dark\"" in (rd(".streamlit/config.toml") or "")),
    ("#7 그라디언트", "gradient" in css),
    ("#8 컬러 글로우·그림자", "box-shadow:0 0" in css or "filter:blur" in css),
    ("#11 카드 왼쪽 컬러 보더", "border-left:3px" in css
     or "border-left:4px" in css),
    ("#14 스탯 배너 줄", "st.metric" in ap),
    ("#15 사이드바 이모지", False),
    ("#16 올캡스 라벨", "text-transform:uppercase" in css),
    # ⚠오탐 주의 — 주석에 「안 쓴다」고 적은 글자가 잡힌 적이 있다.
    #   ★«실제 선언»만 본다: font-family 줄과 폰트 URL.
    ("기본 서체(Inter·Geist·Space Grotesk·Instrument Serif)",
     any(x in 선언 for x in ("Inter", "Geist", "Space+Grotesk",
                            "Instrument+Serif"))),
]
밟은 = [n for n, hit in 표식 if hit]
친다("AI 표식 16개 중", OK if not 밟은 else BAD,
   "0개 (검사 %d항목)" % len(표식) if not 밟은 else "★" + ", ".join(밟은))
친다("DESIGN.md 있나", OK if rd("DESIGN.md") else BAD,
   "디자인 결정의 출처가 파일로 있다")

# ── ⑨-1 구조 아이콘에 이모지 ───────────────────────────────────
강조 = set("★⚠⛔⇒·—«»①②③④⑤⑥⑦⑧⑨●")
구조자리 = re.findall(
    r'(?:st\.(?:button|tabs|radio|checkbox|selectbox|metric)'
    r'|class="(?:idx|ttl|cap|mk|d )")[^\n]{0,160}', ap)
emo = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF]")
쓴것 = sorted({c for blk in 구조자리 for c in emo.findall(blk)} - 강조)
친다("구조 아이콘에 이모지", OK if not 쓴것 else BAD,
   "0개" if not 쓴것 else "★" + " ".join(쓴것))

# ── ⑨-3 ★UX — 과업(비교)을 지원하나 ────────────────────────────
친다("회차를 쌓나", OK if 'session_state.setdefault("회차"' in ap else BAD,
   "다시 돌려도 앞 회차가 안 덮인다" if 'setdefault("회차"' in ap
   else "★한 칸이라 덮인다 — 비교를 못 한다")
친다("잡음 띠", OK if "compare.띠" in ap else BAD,
   "결과 «옆»에서 읽을 수 있는 차이인지 말한다")
친다("데모 실행 기록", OK if "runs.jsonl" in ap else BAD,
   "app 실행도 runs.jsonl 에 남는다")
친다("진행 표시", OK if "st.status" in ap else WARN,
   "6노드 중 어디인지 보인다" if "st.status" in ap else "spinner 하나뿐")


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



# ── ⑪ ★«그려 본다» — 파싱은 실행이 아니다 ─────────────────────
#   ui.css() 는 % 포매팅을 쓴다. CSS 에 맨 % 를 적으면 ast.parse 는
#   통과하지만 «부르는 순간» TypeError 로 죽는다. 실제로 그랬다.
try:
    import ui as _ui
    _css = _ui.css()
    assert len(_css) > 2000 and "--paper" in _css
    친다("ui.css() 실제 호출", OK, "%d자 · 토큰 꽂힘" % len(_css))
except Exception as e:
    친다("ui.css() 실제 호출", BAD, "%s: %s" % (type(e).__name__, str(e)[:44]))

#   ★전역 클래스 이름이 겹치면 «먼 곳»이 조용히 망가진다.
#   .sub 를 새로 지었다가 괘선()·표제가 쓰던 것과 부딪혀
#   안내문의 <b> 가 전부 flex 항목이 되어 줄줄이 끊겼다.
try:
    import re as _re
    _본문 = _ui.css()
    _본문 = _본문[:_본문.index("@media (prefers-reduced-motion")]
    _뿌리 = _re.findall(r"^\.([a-z][a-z0-9-]*)\{", _본문, _re.M)
    _겹침 = sorted({c for c in _뿌리 if _뿌리.count(c) > 1})
    친다("전역 클래스 이름 겹침", BAD if _겹침 else OK,
       ("★" + " · ".join(_겹침)) if _겹침 else "겹치는 최상위 클래스 없음")
except Exception as e:
    친다("전역 클래스 이름 겹침", WARN, str(e)[:50])

#   ★WCAG 1.4.11 — 조작요소 «경계»는 바탕 대비 3:1.
#   「뭘 눌러야 하는지 모르겠다」를 «잴 수 있는 것»으로 바꾼 자리다.
try:
    def _L(h):
        h = h.lstrip("#")
        v = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        v = [c / 12.92 if c <= .03928 else ((c + .055) / 1.055) ** 2.4
             for c in v]
        return .2126 * v[0] + .7152 * v[1] + .0722 * v[2]
    _x = sorted([_L(_ui.C["fieldline"]), _L(_ui.C["paper"])], reverse=True)
    _r = (_x[0] + .05) / (_x[1] + .05)
    친다("조작요소 경계 대비 (WCAG 1.4.11)", OK if _r >= 3.0 else BAD,
       "%.2f:1 (요구 3.0)" % _r)
except Exception as e:
    친다("조작요소 경계 대비 (WCAG 1.4.11)", WARN, str(e)[:50])


# ── ⑫ ★제출물의 «정리» — 채점자가 폴더를 열면 무엇이 보이나 ────
#   전부 「목록이 자란다」의 같은 얼굴이다. 줄을 더하지 말고 «센다».
_RM = rd("README.md")
try:
    _블록 = _RM[_RM.index("## 폴더"):]
    _블록 = _블록[:_블록.index("```", _블록.index("```") + 3)]
except ValueError:
    _블록 = ""
_빠짐 = sorted(f for f in os.listdir(HERE)
             if f.endswith(".py") and f not in _블록)
친다("README 폴더 목록 = 실제 파일", BAD if _빠짐 else OK,
   ("★빠짐 " + " · ".join(_빠짐)) if _빠짐
   else "%d개 전부 적혀 있다" % len([f for f in os.listdir(HERE)
                               if f.endswith(".py")]))

#   ★고아 — 만들어는 놨는데 아무 문서도 안 가리키는 것.
#   채점자에겐 «왜 있는지 모를 파일»이다. 지우거나, 설명하거나 둘 중 하나.
#   ⛔어느 문서가 «세는지»를 열거하지 않는다 — 문서는 는다(§F-8-D 1단계).
#   실제로 README·REPORT·DESIGN 만 셌더니 docs/CHECK.md 가 가리키는
#   hero.jpg 를 ★고아라고 잘못 불렀다. ⇒ .md 는 «전부» 센다.
_글 = ""
for _r, _ds, _fs in os.walk(HERE):
    if ".git" in _r or "__pycache__" in _r:
        continue
    for _f in _fs:
        if _f.endswith(".md"):
            _글 += io.open(os.path.join(_r, _f), encoding="utf-8",
                          errors="ignore").read()
for _d in ("docs", "output"):
    _p = os.path.join(HERE, _d)
    if os.path.exists(_d):
        _안내 = os.path.join(_p, "README.md")
        _글2 = _글 + (rd("%s/README.md" % _d)
                    if os.path.exists(_안내) else "")
        _고아 = sorted(f for f in os.listdir(_p)
                     if os.path.isfile(os.path.join(_p, f))
                     and f != "README.md" and f not in _글2)
        친다("%s/ 안 가리키는 파일" % _d, BAD if _고아 else OK,
           ("★" + " · ".join(_고아[:5])) if _고아 else "전부 문서가 가리킨다")

#   ★clone 하면 깨지는 경로 — 설정이 «이 폴더 밖»을 가리키면 안 된다.
#   실제로 launch.json 이 이웃 프로젝트의 .venv 를 가리키고 있었다.
_밖 = []
for _f in (".claude/launch.json", ".streamlit/config.toml"):
    _fp = os.path.join(HERE, _f)
    if os.path.exists(_fp) and ".." in rd(_f):
        _밖.append(_f)
친다("설정이 폴더 «밖»을 가리키나", BAD if _밖 else OK,
   ("★" + " · ".join(_밖)) if _밖 else "전부 폴더 안")


#   ⛔★손으로 적은 «항목 수» — 이 프로젝트에서 다섯 번 샌 바로 그 실수.
#   README 에 「(59항목)」이 박혀 있었고 실제로는 69개였다.
#   수는 «돌리면» 나온다. 문서에 박지 않는다.
_박힘 = []
for _f in ("README.md", "REPORT.md", "DESIGN.md"):
    if not os.path.exists(os.path.join(HERE, _f)):
        continue
    for _m in re.finditer(r"(\d+)\s*항목", rd(_f)):
        # 찍어내는 블록(<!-- RED:START --> 안) 은 예외다 — 거기가 «출처»다
        _본 = rd(_f)
        _앞 = _본[:_m.start()]
        if _앞.count("<!-- RED:START -->") > _앞.count("<!-- RED:END -->"):
            continue
        # ⛔헛경고를 만들지 않는다 — 「루브릭 3항목」은 검사 수가 아니다.
        #   ★절반이 헛경고면 사람이 경고를 «안 읽는다».
        _창 = _본[max(0, _m.start() - 40):_m.end() + 20]
        if not re.search(r"레드팀|redteam|합계|검사|점검", _창):
            continue
        _박힘.append("%s:%s항목" % (_f, _m.group(1)))
친다("문서에 «손으로» 박은 항목 수", BAD if _박힘 else OK,
   ("★" + " · ".join(_박힘)) if _박힘 else "없다 — 수는 돌리면 찍힌다")

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
