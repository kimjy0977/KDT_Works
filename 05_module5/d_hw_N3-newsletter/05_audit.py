"""제출본 전수검사 — 노드3 요건·루브릭·완결성을 «기계»로 센다.

  python 05_audit.py [제출본경로]

★왜 스크립트인가
  눈으로 훑으면 «본 곳»만 본다. 내가 실제로 그렇게 빠뜨렸다(§F-8-D).
  범위를 기억으로 정하지 않고 «세어서» 정한다.

★판정 기호
  OK    확인됨            WARN  봐야 할 것       FAIL  고쳐야 할 것
"""
import io
import json
import os
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ★경로를 박지 않는다 — 기본값은 «이 스크립트가 놓인 곳».
#   남이 clone 해서 그냥 돌려도 자기 자신을 검사한다.
ROOT = (sys.argv[1] if len(sys.argv) > 1
        else os.path.dirname(os.path.abspath(__file__)))
ROOT = ROOT.replace("\\", "/").rstrip("/")


def _find_repo(start):
    """.git 을 위로 올라가며 찾는다. 없으면 git 검사는 건너뛴다."""
    d = start
    for _ in range(8):
        if os.path.isdir(os.path.join(d, ".git")):
            return d
        up = os.path.dirname(d)
        if up == d:
            break
        d = up
    return None


REPO = _find_repo(ROOT)
PREFIX = (ROOT[len(REPO) + 1:] + "/") if REPO and ROOT.startswith(REPO) else ""

R = []          # (레벨, 항목, 메시지)


def rec(level, item, msg):
    R.append((level, item, msg))
    print("  %-5s %-34s %s" % (level, item, msg))


def head(t):
    print()
    print("═" * 86)
    print("  " + t)
    print("═" * 86)


def read(rel):
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        return None
    return io.open(p, encoding="utf-8", errors="replace").read()


def walk():
    """제출본에 «실제로 있는» 파일 전수. 기억이 아니라 센다."""
    out = []
    for dp, dns, fns in os.walk(ROOT):
        dns[:] = [d for d in dns if d not in (".venv", "__pycache__", ".git")]
        for fn in fns:
            p = os.path.join(dp, fn).replace("\\", "/")
            out.append(p[len(ROOT) + 1:])
    return sorted(out)


def git(*args):
    if not REPO:
        return ""
    try:
        return subprocess.run(["git", "-C", REPO] + list(args),
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace").stdout
    except Exception as exc:
        return "((git 실패: %s))" % exc


# ══════════════════════════════════════════════════════════════
# A. 비밀 누출 — 가장 먼저. 여기서 걸리면 나머지는 의미가 없다
# ══════════════════════════════════════════════════════════════
def a_secrets(files):
    head("A. 비밀 누출 — 웹훅 주소·API 키  ★주소 자체가 열쇠다")
    pats = [
        ("Discord 웹훅", re.compile(r"discord(?:app)?\.com/api/webhooks/\d+/[\w-]+")),
        ("OpenAI 키", re.compile(r"sk-[A-Za-z0-9_-]{20,}")),
        ("Anthropic 키", re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}")),
        ("Slack 웹훅", re.compile(r"hooks\.slack\.com/services/[\w/]+")),
        ("일반 Bearer", re.compile(r"Bearer\s+[A-Za-z0-9._-]{30,}")),
    ]
    hit = 0
    for rel in files:
        p = os.path.join(ROOT, rel)
        try:
            txt = io.open(p, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        for name, pat in pats:
            for m in pat.finditer(txt):
                hit += 1
                rec("FAIL", "누출 " + name, "%s — %s" % (rel, m.group(0)[:50]))
    if not hit:
        rec("OK", "현재 트리", "파일 %d개 전수 — 누출 0" % len(files))

    # 과거 커밋에도 없어야 한다. 한 번 올라가면 지워도 히스토리에 남는다.
    for name, pat in pats[:2]:
        raw = git("log", "--all", "-p", "--", PREFIX or ".")
        found = pat.findall(raw or "")
        if found:
            rec("FAIL", "git 히스토리 " + name, "과거 커밋에 %d건" % len(found))
        else:
            rec("OK", "git 히스토리 " + name, "과거 커밋에도 없음")

    # .env 가 등재되지 않았는가
    tracked = (git("ls-files", PREFIX or ".") or "").split()
    envs = [t for t in tracked if t.endswith("/.env")]
    rec("FAIL" if envs else "OK", ".env 등재",
        "★%s" % envs if envs else "추적되지 않음 (.gitignore 유효)")
    return tracked


# ══════════════════════════════════════════════════════════════
# B. 요건 ①~⑤ + 제외 목록
# ══════════════════════════════════════════════════════════════
BANNED = {"openai.com": "OpenAI", "deepmind.google": "DeepMind",
          "techcrunch.com": "TechCrunch", "theverge.com": "The Verge",
          "technologyreview.com": "MIT TR", "aitimes.com": "AI타임스"}


def b_requirements():
    head("B. 노드3 필수 구현 ①~⑤ + 제외 목록")
    import yaml
    st = yaml.safe_load(read("settings.yaml") or "{}")
    au = yaml.safe_load(read("audience.yaml") or "{}")
    src = st.get("sources") or []

    # ① 소스 3개 이상
    rec("OK" if len(src) >= 3 else "FAIL", "① 소스 3곳 이상", "%d곳" % len(src))

    # ① 제외 목록 — 호스트 기준. 이름이 아니라 «주소»로 센다
    bad = []
    for s in src:
        u = s.get("url", "")
        for hostpart, label in BANNED.items():
            if hostpart in u:
                bad.append("%s(%s)" % (s.get("name"), label))
    rec("FAIL" if bad else "OK", "① 제외 목록 준수",
        "★겹침 %s" % bad if bad else "금지 6곳과 겹침 0 (호스트 대조)")

    # ② 3~5건
    t = st.get("target")
    rec("OK" if t and 3 <= t <= 5 else "FAIL", "② 핵심 3~5건", "target=%s" % t)

    # ② 기준이 의도대로 동작했다는 근거
    has_caps = bool(st.get("group_caps")) and st.get("media_cap") is not None
    rec("OK" if has_caps else "WARN", "② 선별 근거 장치",
        "group_caps=%s · media_cap=%s" % (st.get("group_caps"), st.get("media_cap")))

    # ③ 독자 관점 인사이트 — why 칸
    g = read("graph.py") or ""
    rec("OK" if "why" in g and "class Draft" in g else "FAIL", "③ 인사이트 칸(why)",
        "Draft 스키마에 why 있음" if "why" in g else "★없음")

    # ④ 자동 검수 3겹 + 불통과 대안
    layers = [("규칙검사", "def rule_check"), ("숫자지목", "_nums_ko"),
              ("LLM 대조", "Verdict")]
    miss = [n for n, k in layers if k not in g]
    rec("FAIL" if miss else "OK", "④ 자동 검수 3겹",
        "★빠짐 %s" % miss if miss else "규칙검사 + 숫자지목 + LLM 대조")
    alt = [("재생성", "def redraft"), ("스킵+로그", "→ 스킵")]
    miss2 = [n for n, k in alt if k not in g]
    rec("FAIL" if miss2 else "OK", "④ 불통과 시 대안",
        "★빠짐 %s" % miss2 if miss2 else "재생성 1회 → 그래도 안 되면 스킵(사유 로그)")

    # ⑤ 발행 확인
    rec("OK" if "def send" in g and "204" in (read("REPORT.md") or "") else "WARN",
        "⑤ 발행 채널 전달 확인", "send() 있음 · REPORT 에 HTTP 204 기재")

    # 독자 정의
    rec("OK" if au.get("독자") or au.get("누구") else "WARN", "① 독자 정의",
        "audience.yaml 키: %s" % list(au.keys())[:5])
    return st


# ══════════════════════════════════════════════════════════════
# C. 제출물 구조 + REPORT 6항목
# ══════════════════════════════════════════════════════════════
def c_structure(files):
    head("C. 제출물 구조 · REPORT.md 6항목")
    must = ["graph.py", "run.py", "audience.yaml", "settings.yaml",
            "requirements.txt", "REPORT.md"]
    for m in must:
        rec("OK" if m in files else "FAIL", "필수 " + m,
            "있음" if m in files else "★없음")
    has_metrics = any(f.startswith("store/metrics") for f in files)
    rec("OK" if has_metrics else "FAIL", "필수 store/metrics.jsonl",
        "있음" if has_metrics else "★없음")

    rp = read("REPORT.md") or ""
    six = [("1 분야·독자 정의", r"분야 및 독자 정의"),
           ("2 소스 채택표", r"소스 채택표"),
           ("3 선별 로직 설계", r"선별 로직 설계"),
           ("4 파이프라인 구조도", r"파이프라인 구조도"),
           ("5 실행 기록", r"##\s*5\.\s*실행 기록"),
           ("6 프로젝트 회고", r"프로젝트 회고")]
    for label, pat in six:
        rec("OK" if re.search(pat, rp) else "FAIL", "REPORT " + label,
            "섹션 있음" if re.search(pat, rp) else "★섹션 없음")

    # 4번은 «구조도가 실제로 있는가»까지 본다
    has_mermaid = "```mermaid" in rp or "graph TD" in rp or "flowchart" in rp
    rec("OK" if has_mermaid else "FAIL", "REPORT 4 구조도 실물",
        "mermaid 블록 있음" if has_mermaid else "★제목만 있고 그림이 없다")

    # ★구조도가 «실제 그래프»와 같은가 — 그림만 있고 틀리면 없느니만 못하다
    mm = re.search(r"```mermaid(.*?)```", rp, re.S)
    if mm:
        drawn_nodes = set(re.findall(r"^\s*(\w+)[(\[]", mm.group(1), re.M))
        drawn_nodes -= {"classDef", "graph", "flowchart"}
        drawn_edges = set()
        for a, b in re.findall(r"(\w+)\s*-[.\->|]*>\s*(?:\|[^|]*\|)?\s*(\w+)",
                               mm.group(1)):
            drawn_edges.add((a, b))
        g = read("graph.py") or ""
        real_nodes = set(re.findall(r'for n in \(([^)]+)\)', g))
        real_nodes = set(re.findall(r'"(\w+)"', real_nodes.pop())) if real_nodes else set()
        real_edges = set(re.findall(r'add_edge\(\s*"?(\w+)"?\s*,\s*"?(\w+)"?\s*\)', g))
        cond = re.findall(r'add_conditional_edges\(\s*"(\w+)",\s*\w+,\s*\[([^\]]+)\]', g)
        for src_n, targets in cond:
            for t in re.findall(r'"(\w+)"', targets):
                real_edges.add((src_n, t))
        real_edges = {(a.replace("START", "__start__").replace("END", "__end__"),
                       b.replace("START", "__start__").replace("END", "__end__"))
                      for a, b in real_edges}
        miss_n = real_nodes - drawn_nodes
        extra_n = drawn_nodes - real_nodes - {"__start__", "__end__"}
        rec("FAIL" if (miss_n or extra_n) else "OK", "구조도 ↔ 실제 노드",
            "★그림에 없음%s 그림에만%s" % (miss_n or "-", extra_n or "-")
            if (miss_n or extra_n) else "노드 %d개 일치 %s" % (len(real_nodes), sorted(real_nodes)))
        miss_e = real_edges - drawn_edges
        rec("FAIL" if miss_e else "OK", "구조도 ↔ 실제 엣지",
            "★그림에 없는 연결 %s" % sorted(miss_e) if miss_e
            else "엣지 %d개 전부 그려짐" % len(real_edges))

    # 5번은 «캡처가 실제로 있는가 · 진짜 열리는 파일인가»까지 본다
    imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", rp)
    for rel in imgs:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            rec("FAIL", "REPORT 이미지 실재", "%s  ★파일 없음" % rel)
            continue
        b = io.open(p, "rb").read()
        okpng = b[:8] == b"\x89PNG\r\n\x1a\n" and b[-8:-4] == b"IEND"
        rec("OK" if okpng else "FAIL", "REPORT 이미지 유효",
            "%s · %dKB%s" % (rel, len(b) // 1024,
                             "" if okpng else "  ★PNG 가 아니거나 잘렸다"))
    if not imgs:
        rec("FAIL", "REPORT 5 캡처 실물", "★이미지 링크가 없다")


# ══════════════════════════════════════════════════════════════
# D. 문서 ↔ 실물 참조 무결성
# ══════════════════════════════════════════════════════════════
def d_refs(files):
    head("D. 문서가 «언급한» 것이 실제로 있는가")
    fileset = set(files)
    bases = {os.path.basename(f) for f in fileset}
    gi = read(".gitignore") or ""
    # ★「문서가 가리키는 것」과 「문서가 설명하는 것」은 다르다.
    #   실행하면 «생기는» 파일은 저장소에 없는 게 정상이다. 규칙으로 가린다 —
    #   목록으로 열거하면 새 산출물이 생길 때마다 샌다(§F-8-D 1단계).
    PLACEHOLDER = re.compile(r"[A-Z]{4,}")          # run-YYYYMMDD-HHMM.log 같은 «형식 설명»
    pat = re.compile(r"`([\w./\-*]+\.(?:py|yaml|yml|txt|md|jsonl|log|png|example))`")
    for doc in ("README.md", "REPORT.md"):
        txt = read(doc)
        if txt is None:
            rec("FAIL", doc, "★없음")
            continue
        named = sorted(set(pat.findall(txt)))
        miss, skipped = [], []
        for n in named:
            base = os.path.basename(n)
            if PLACEHOLDER.search(base):            # 형식 설명이지 파일명이 아니다
                skipped.append(n + " (형식 설명)")
            elif "*" in n:                          # 글롭 — basename 으로 맞춘다
                stem = base.split("*")[0]
                if not any(b.startswith(stem) for b in bases):
                    miss.append(n)
            elif n in fileset or base in bases:
                pass
            elif base in gi or n in gi:             # .gitignore 대상 = 런타임 산출물
                skipped.append(n + " (gitignore·런타임 산출물)")
            else:
                miss.append(n)
        rec("FAIL" if miss else "OK", doc + " 파일 참조",
            "★실물 없음 %s" % miss if miss else
            "언급 %d개 실재%s" % (len(named) - len(skipped),
                                 " · 제외 %s" % skipped if skipped else ""))

        cmds = re.findall(r"^\s*python\s+([\w.\-]+\.py)", txt, re.M)
        cmiss = [c for c in sorted(set(cmds)) if c not in fileset]
        rec("FAIL" if cmiss else "OK", doc + " 명령어 대상",
            "★없는 파일 %s" % cmiss if cmiss else "python 명령 %d종 전부 실재"
            % len(set(cmds)))

    # 문서에 없는 «고아 파일»
    docs = (read("README.md") or "") + (read("REPORT.md") or "")
    orphan = [f for f in files
              if f.endswith(".py") and os.path.basename(f) not in docs]
    rec("WARN" if orphan else "OK", "문서에 안 적힌 .py",
        "%s" % orphan if orphan else "없음")


# ══════════════════════════════════════════════════════════════
# E. 코드 건강
# ══════════════════════════════════════════════════════════════
def e_code(files):
    head("E. 코드 — 구문 · 불러오기 안전성 · 이식성")
    import ast
    pys = [f for f in files if f.endswith(".py")]
    broken = []
    for f in pys:
        try:
            ast.parse(io.open(os.path.join(ROOT, f), encoding="utf-8").read())
        except SyntaxError as exc:
            broken.append("%s:%s" % (f, exc.lineno))
    rec("FAIL" if broken else "OK", "구문",
        "★깨짐 %s" % broken if broken else "%d개 전부 OK" % len(pys))

    # 11강 — graph.py 는 불러오기만 해도 안전해야 한다
    g = read("graph.py") or ""
    top_run = re.search(r"^(?!def |class |#|\s)\s*(run\(|build\(\)\.compile\(\)\.invoke)",
                        g, re.M)
    rec("FAIL" if top_run else "OK", "graph.py 불러오기 안전",
        "★모듈 최상위에서 실행" if top_run else "최상위 실행 없음 (11강)")

    # 이식성 — 남의 컴퓨터에서 깨질 것
    for f in pys + [x for x in files if x.endswith((".md", ".yaml", ".txt"))]:
        txt = io.open(os.path.join(ROOT, f), encoding="utf-8", errors="replace").read()
        for m in re.finditer(r"[A-Za-z]:[/\\]Users[/\\][\w-]+", txt):
            rec("WARN", "절대경로 " + f, m.group(0))
            break

    # 제어문자 (§F-8-B)
    dirty = []
    for f in files:
        b = io.open(os.path.join(ROOT, f), "rb").read()
        if any(c < 32 and c not in (9, 10, 13) for c in b) and not f.endswith(".png"):
            dirty.append(f)
    rec("FAIL" if dirty else "OK", "제어문자 오염",
        "★%s" % dirty if dirty else "%d개 전수 — 0" % len(files))


# ══════════════════════════════════════════════════════════════
# F. 수치 일관성 — REPORT 의 숫자 ↔ metrics 실측
# ══════════════════════════════════════════════════════════════
def f_numbers():
    head("F. REPORT 의 숫자가 «실측»과 맞는가")
    rows = [json.loads(l) for l in
            io.open(os.path.join(ROOT, "store/metrics.jsonl"), encoding="utf-8")
            if l.strip()]
    import yaml
    st = yaml.safe_load(read("settings.yaml") or "{}")
    names = set(s["name"] for s in st.get("sources") or [])
    groups = set(s.get("group") for s in st.get("sources") or [] if s.get("group"))

    def mine(r):
        s = set((r.get("by_source") or {}).keys())
        if s:
            return bool(s & names)
        seen = set(m.group(1) for line in (r.get("log") or [])
                   for m in [re.search(r"예선 \[([^\]]+)\]", line)]
                   if m and m.group(1) != "_")
        return bool(seen & groups) if seen else None

    ours = [r for r in rows if mine(r) is True]
    tc = sum(r["collected"] for r in ours)
    tp = sum(r["picked"] for r in ours)
    td = sum(r["drafted"] for r in ours)
    tb = sum(r["published"] for r in ours)
    real = "수집 %d → 선별 %d → 취재 %d → 발행 %d" % (tc, tp, td, tb)
    rec("OK", "metrics 실측", "행 %d (그중 이 프로필 %d) · %s" % (len(rows), len(ours), real))

    rp = read("REPORT.md") or ""
    m = re.search(r"합계\s+수집 (\d+) → 선별 (\d+) → 취재 (\d+) → 발행 (\d+)", rp)
    if not m:
        rec("WARN", "REPORT 깔때기 합계", "문장을 못 찾음 — 형식이 바뀌었나")
    else:
        got = tuple(int(x) for x in m.groups())
        rec("OK" if got == (tc, tp, td, tb) else "FAIL", "REPORT 깔때기 합계",
            "문서 %s ↔ 실측 %s" % (str(got), str((tc, tp, td, tb))))

    m2 = re.search(r"선별 ([\d.]+)%\s+취재 ([\d.]+)%\s+검수 ([\d.]+)%", rp)
    if m2:
        want = (round(100 * tp / max(tc, 1), 1), round(100 * td / max(tp, 1), 1),
                round(100 * tb / max(td, 1), 1))
        got = tuple(float(x) for x in m2.groups())
        rec("OK" if got == want else "FAIL", "REPORT 통과율",
            "문서 %s ↔ 실측 %s" % (str(got), str(want)))

    m3 = re.search(r"«?발견»?\s*프로필\s*\*\*(\d+)회\*\*", rp) or \
        re.search(r"프로필 \*\*(\d+)회\*\* 기준", rp)
    if m3:
        rec("OK" if int(m3.group(1)) == len(ours) else "FAIL", "REPORT 실행 횟수",
            "문서 %s회 ↔ 실측 %d회" % (m3.group(1), len(ours)))

    # 발행 실증 — HTTP 2xx 가 실제 기록에 있는가
    sent = [r for r in ours if any("HTTP 2" in l for l in (r.get("log") or []))]
    rec("OK" if sent else "FAIL", "실제 발행 기록",
        "%d회 (%s)" % (len(sent), ", ".join(r["run_id"][11:16] for r in sent)))


# ══════════════════════════════════════════════════════════════
# G. 재현성
# ══════════════════════════════════════════════════════════════
def g_repro(files):
    head("G. 남이 받아서 돌릴 수 있는가")
    req = read("requirements.txt")
    if not req:
        rec("FAIL", "requirements.txt", "★없음")
    else:
        lines = [l.strip() for l in req.splitlines()
                 if l.strip() and not l.strip().startswith("#")]
        pinned = [l for l in lines if re.search(r"[=><~]=", l)]
        rec("OK" if len(pinned) == len(lines) else "WARN", "의존성 버전 고정",
            "%d개 중 %d개 고정" % (len(lines), len(pinned)))
        # 실제로 설치돼 있는가
        import importlib
        alias = {"pyyaml": "yaml", "python-dotenv": "dotenv",
                 "beautifulsoup4": "bs4", "langchain-openai": "langchain_openai",
                 "langchain-ollama": "langchain_ollama", "langchain-core": "langchain_core"}
        # ★import 이름으로 확인하면 «서브패키지»를 못 잡는다.
        #   langgraph-checkpoint 는 `import langgraph.checkpoint` 이지
        #   `import langgraph_checkpoint` 가 아니다 — 설치돼 있는데 「없음」이 뜬다.
        #   ⇒ 설치 여부는 «배포 메타데이터»로 본다. 그게 pip 이 아는 진실이다.
        import importlib.metadata as md
        missing = []
        for l in lines:
            name = re.split(r"[=><~\[]", l)[0].strip()
            try:
                md.version(name)
            except Exception:
                mod = alias.get(name.lower(), name.replace("-", "_"))
                try:
                    importlib.import_module(mod)
                except Exception:
                    missing.append(l)
        rec("WARN" if missing else "OK", "의존성 설치 확인",
            "이 환경에 없음: %s" % missing if missing else
            "%d개 전부 설치 확인 (배포 메타데이터 기준)" % len(lines))

    ex = read(".env.example")
    if not ex:
        rec("WARN", ".env.example", "★없음 — 어떤 키가 필요한지 알 수 없다")
    else:
        g = read("graph.py") or ""
        used = set(re.findall(r"os\.environ(?:\.get)?[(\[]\s*[\"']([A-Z_]+)[\"']", g))
        used |= set(re.findall(r"getenv\(\s*[\"']([A-Z_]+)[\"']", g))
        doc = set(re.findall(r"^([A-Z_]+)\s*=", ex, re.M))
        miss = sorted(u for u in used if u not in doc and u not in ("PROFILE",))
        rec("WARN" if miss else "OK", ".env.example 완전성",
            "코드가 쓰는데 예시에 없음: %s" % miss if miss else
            "코드가 읽는 환경변수 %d개 모두 기재" % len(used))

    gi = read(".gitignore") or ""
    for need in (".env", "__pycache__"):
        rec("OK" if need in gi else "WARN", ".gitignore " + need,
            "있음" if need in gi else "★없음")


# ══════════════════════════════════════════════════════════════
# H. git 등재 — «파일이 있다» ≠ «올라갔다»
# ══════════════════════════════════════════════════════════════
def h_git(files, tracked):
    head("H. 로컬에 있는 것이 «실제로 push 됐는가»")
    pref = PREFIX
    tset = set(t[len(pref):] for t in tracked if t.startswith(pref))
    local = set(f for f in files if not f.endswith(".pyc"))
    untracked = sorted(local - tset)
    ignored = [u for u in untracked
               if u.endswith((".env", "last_quiet.txt")) or "__pycache__" in u]
    real = [u for u in untracked if u not in ignored]
    rec("FAIL" if real else "OK", "미등재 파일",
        "★%s" % real if real else "로컬 %d개 = 추적 %d개 (의도적 제외: %s)"
        % (len(local), len(tset), ignored or "없음"))

    st = git("status", "--short", "--", pref).strip()
    rec("FAIL" if st else "OK", "미커밋 변경",
        "★\n      " + st.replace("\n", "\n      ") if st else "없음 (작업트리 깨끗)")

    ahead = git("rev-list", "--count", "origin/main..HEAD").strip()
    rec("FAIL" if ahead not in ("0", "") else "OK", "push 상태",
        "origin 보다 %s 커밋 앞섬" % ahead if ahead not in ("0", "")
        else "origin/main 과 동기")


def main():
    print("제출본 전수검사 —", ROOT)
    files = walk()
    print("  대상 파일 %d개 (기억이 아니라 os.walk 로 셌다)" % len(files))
    tracked = a_secrets(files)
    b_requirements()
    c_structure(files)
    d_refs(files)
    e_code(files)
    f_numbers()
    g_repro(files)
    h_git(files, tracked)

    head("판정")
    n = {"OK": 0, "WARN": 0, "FAIL": 0}
    for lv, _, _ in R:
        n[lv] = n.get(lv, 0) + 1
    print("  OK %d · WARN %d · FAIL %d" % (n["OK"], n["WARN"], n["FAIL"]))
    if n["FAIL"]:
        print()
        print("  ★고쳐야 할 것")
        for lv, item, msg in R:
            if lv == "FAIL":
                print("    - %-32s %s" % (item, msg))
    if n["WARN"]:
        print()
        print("  봐야 할 것")
        for lv, item, msg in R:
            if lv == "WARN":
                print("    - %-32s %s" % (item, msg))


if __name__ == "__main__":
    main()
