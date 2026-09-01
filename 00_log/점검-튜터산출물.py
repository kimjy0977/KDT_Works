# -*- coding: utf-8 -*-
"""튜터 산출물 전수 점검 — 노트·과제·문서·하네스를 한 번에 훑는다

왜 있나. 2026-08-31 전수 검사에서 **눈으로는 안 보이는 결함 5종**이 나왔다.
  · 강의노트 m2n2 의 안 닫힌 <div> 2곳 — 안내 상자가 뒤 문단을 삼키고 있었다
  · 여는 <p> 없는 떠돌이 </p> 3곳
  · README·PRD 가 «43점 · 130청크»라고 말하는데 실물은 982점 · 2,978청크
  · 사라진 통합본 myth-docs.json 을 가리키는 파일 목록·재현 절차
  · ★하네스에 제어문자(0x00·0x01)가 박혀 **grep 이 파일을 바이너리로 취급** —
    규칙 점검이 조용히 실패하고 있었다 (감시기 방법론 A-3-① 과 같은 함정)

전부 «문서가 실물과 다른데 아무도 모르는» 종류다. 그래서 기계로 센다.

실행:  python 00_log/점검-튜터산출물.py
       종료코드 0 = 이상 없음 / 1 = HIGH 있음

⚠️ 오탐을 남기지 않는다. 검사기가 늑대 소년이 되면 다음부터 아무도 안 본다.
   금지 문구와 모범 예시를 구별하고, 과거 기록과 현재 주장을 구별한다.
"""
import io, json, os, re, subprocess, sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
N5 = os.path.join(REPO, "04_module3", "a_mq_N5-myth-rag-guide")
TUTOR = os.path.join(os.path.dirname(os.path.dirname(REPO)), "02_tutor")

issues = []
def note(sev, where, msg): issues.append((sev, where, msg))
def rd(p): return io.open(p, encoding="utf-8").read()


# ══ 1. 제어문자 — grep 을 무력화하는 가장 조용한 결함 ═══════════════════
def check_control_chars():
    """★고정 목록이 아니라 «훑는다» (§F-8-D).
    계기: 2026-09-02 빌더가 «브리지 전부 0» 이라 보고했으나 자기 집 파일 2개가
    오염돼 있었다. 점검 «범위»가 좁으면 «없다»가 아니라 «안 봤다»가 된다.
    같은 날 정본(KDT-공통운영규칙.md)에도 6개가 있었다 — 하필 «점검 명령» 줄에."""
    EXT = (".md", ".py", ".html", ".ps1", ".txt", ".json",
           ".ts", ".tsx", ".css", ".mjs", ".js")
    SKIP = ("node_modules", ".git", ".venv", "venv", "dist", "__pycache__",
            "assets", "legacy-handmade")
    KDT = os.path.abspath(os.path.join(TUTOR, os.pardir))
    # ★«튜터 관할 폴더»를 통째로 넣는다. 하위를 골라 넣으면 또 샌다.
    # 2026-09-02 2차 확대 — 1차 확대 때도 04_module3 의 src/tools 만 넣어
    # README·PRD·node5-requirements 를 빼먹었다. 01_onboarding·02_module1 도 통째로 빠져 있었다.
    # 매니저 실측: «범위를 좁게 잡는 실수»가 3세션에서 3회. 하위 선택을 하지 않는다.
    roots = [(TUTOR, "02_tutor"),
             (os.path.join(KDT, "00_shared", "bridge"), "브리지")]
    roots += [(os.path.join(REPO, d), d) for d in
              ("00_log", "01_onboarding", "02_module1", "04_module3", "99_domain-dev")]
    seen, n = set(), 0
    for root, _label in roots:
        if not os.path.isdir(root):
            continue
        for dp, dns, fns in os.walk(root):
            dns[:] = [d for d in dns if not any(x in d for x in SKIP)]
            DATA = ("myth-docs", "chunks.json", "eval-hits", "variant-",
                    "experiment-", "package-lock.json")
            for f in fns:
                if not f.endswith(EXT):
                    continue
                if any(x in f for x in DATA):
                    continue
                p = os.path.abspath(os.path.join(dp, f))
                if p in seen:
                    continue
                seen.add(p)
                # 큰 데이터 파일은 건너뛴다 (벡터스토어 등)
                try:
                    if os.path.getsize(p) > 4_000_000:
                        continue
                    raw = io.open(p, "rb").read()
                except Exception as e:
                    note("MED", os.path.basename(p), f"읽기 실패: {type(e).__name__}")
                    continue
                n += 1
                bad = [(k, b) for k, b in enumerate(raw)
                       if b < 0x09 or 0x0b <= b <= 0x0c or 0x0e <= b <= 0x1f]
                if bad:
                    ln = raw[:bad[0][0]].count(b"\n") + 1
                    note("HIGH", os.path.relpath(p, KDT),
                         f"제어문자 {len(bad)}개 (첫 위치 {ln}행 0x{bad[0][1]:02x})"
                         f" — grep 이 바이너리로 본다")
    print(f"[제어문자] {n}개 파일 훑음")


# ══ 2. 강의노트 구조 ════════════════════════════════════════════════════
def check_notes():
    s = rd(os.path.join(HERE, "강의노트-모두연.html"))   # 4집합은 script 안을 읽어야 해 원본
    head = set(re.findall(r'class="section coursehead" id="([a-z0-9]+)"', s))
    datag = set(re.findall(r'tocgroup" data-g="([a-z0-9]+)"', s))
    names = set(re.findall(r"'([a-z0-9]+)':'", re.search(r"var names=\{.*?\};", s, re.S).group(0)))
    order = re.findall(r"'([a-z0-9]+)'", re.search(r"var order=\[.*?\]", s, re.S).group(0))
    print(f"[모두연] 노드 {len(head)} · 강 {len(re.findall(r'class=.section. id=.(?:adn|m.n).-.', s))}")
    if not (head == datag == names == set(order)):
        note("HIGH", "모두연", f"4집합 불일치 — head^names={head ^ names} head^order={head ^ set(order)}")
    if len(order) != len(set(order)):
        note("HIGH", "모두연", "order 배열에 중복")

    # ★<script>·<style> 안은 HTML 이 아니다. 안 걷어내면 JS 의 «ar.top<tr.top» 을
    #   <tr> 태그로, «href="#"+id» 를 죽은 링크로 읽는다(2026-08-31 오탐 3건).
    strip = lambda x: re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", x)

    for fn in ("강의노트-모두연.html", "강의노트-오라일리.html", "강의노트-앤트로픽.html"):
        t = strip(rd(os.path.join(HERE, fn)))
        for tag in ("div", "section", "table", "details", "p", "ul", "ol", "li", "tr", "td", "th"):
            o = len(re.findall(r"<" + tag + r"\b", t)); c = t.count("</" + tag + ">")
            if o != c:
                note("HIGH", fn, f"<{tag}> 태그 불균형 {o}/{c} (차이 {o - c})")
        # 죽은 내부 링크 — id 는 **어느 요소든** 셈한다(section 만 보면 오탐)
        ids = set(re.findall(r'\bid="([^"]+)"', t))
        anchors = {a for a in re.findall(r'href="#([^"]+)"', t) if a}
        dead = anchors - ids
        if dead:
            note("HIGH", fn, f"죽은 내부 링크 {len(dead)}건: {sorted(dead)[:8]}")
        # 없는 파일로 가는 링크
        for L in set(re.findall(r'href="([^":#?]+\.html)"', t)):
            if not os.path.exists(os.path.join(HERE, L)):
                note("HIGH", fn, f"없는 파일로 링크: {L}")

    hub = rd(os.path.join(HERE, "index.html"))
    for n in [f for f in os.listdir(HERE) if f.startswith("강의노트-") and f.endswith(".html")]:
        if n not in hub:
            note("MED", "허브", f"허브에서 링크되지 않는 노트: {n}")
    nums = re.findall(r'class="num">(\d+)<', hub)
    if len(nums) != len(set(nums)):
        note("MED", "허브", f"카드 번호 중복: {nums}")


# ══ 3. 노드5 과제 — 문서가 말하는 숫자 == 실물인가 ══════════════════════
def check_n5():
    if not os.path.isdir(N5):
        return
    idx = json.load(io.open(os.path.join(N5, "myth-docs-index.json"), encoding="utf-8"))
    works = sum(s["works"] for s in idx["shards"]); chunks = idx["built"]
    print(f"[노드5] 실물 {works}작품 · {chunks}청크 · starter {idx.get('starter', {}).get('works', '?')}작품")

    for sh in idx["shards"]:
        f = f"myth-docs-{sh['myth']}.json"
        d = json.load(io.open(os.path.join(N5, f), encoding="utf-8"))
        if len(d) != sh["chunks"]:
            note("HIGH", "샤드", f"{f}: 실제 {len(d)} vs index {sh['chunks']}")
        if {len(x["vector"]) for x in d} != {768}:
            note("HIGH", "샤드", f"{f}: 벡터 차원이 768이 아니다")
        if any(set(x) != {"id", "text", "url", "section", "vector"} for x in d):
            note("HIGH", "샤드", f"{f}: 스키마가 5필드가 아니다")
        mism = [x["id"] for x in d
                if not x["url"].rstrip("/").endswith("/" + x["id"].split("#")[0])]
        if mism:
            note("HIGH", "샤드", f"{f}: url 이 자기 슬러그를 안 가리킨다 {len(mism)}건")

    st = json.load(io.open(os.path.join(N5, "myth-docs-starter.json"), encoding="utf-8"))
    ts = rd(os.path.join(N5, "app", "src", "works.ts"))
    shown = set(re.findall(r'slug:\s*"([a-z]+-[a-z0-9]+)"', ts))
    if shown != {x["id"].split("#")[0] for x in st}:
        note("HIGH", "starter", "works.ts 와 starter 가 어긋난다 — 화면에 보이는데 못 답할 수 있다")
    m = re.search(r"CORPUS = \{ works: (\d+), chunks: (\d+)", ts)
    if m and (int(m.group(1)) != works or int(m.group(2)) != chunks):
        note("HIGH", "works.ts", f"CORPUS {m.group(1)}/{m.group(2)} vs 실물 {works}/{chunks}")

    # 배포본 == app/public
    import hashlib
    hp = lambda p: hashlib.md5(io.open(p, "rb").read()).hexdigest()
    pub = os.path.join(N5, "app", "public")
    for f in os.listdir(pub):
        if not f.startswith("myth-docs"): continue
        b = os.path.join(N5, f)
        if not os.path.exists(b):
            note("HIGH", "배포본", f"배포 루트에 없음: {f}")
        elif hp(os.path.join(pub, f)) != hp(b):
            note("HIGH", "배포본", f"public 과 배포본이 다르다: {f}")
    ih = rd(os.path.join(N5, "index.html"))
    for a in re.findall(r'(?:src|href)="\./(assets/[^"]+)"', ih):
        if not os.path.exists(os.path.join(N5, a)):
            note("HIGH", "배포본", f"index.html 이 없는 자산을 가리킨다: {a}")
    stale = [f for f in os.listdir(os.path.join(N5, "assets"))
             if f.endswith((".js", ".css")) and f not in ih]
    if stale:
        note("MED", "배포본", f"안 쓰는 낡은 번들 {len(stale)}개: {stale}")

    # 문서의 낡은 숫자 — ★과거 경로 서술은 제외한다
    HIST = ("→", "처음엔", "v1", "경로:", "넓혔", "시작했")
    for doc in ("README.md", "PRD.md"):
        for i, line in enumerate(rd(os.path.join(N5, doc)).split("\n"), 1):
            if re.search(r"\b43점\b|\b130청크\b", line) and not any(k in line for k in HIST):
                note("MED", doc, f"{i}행: 낡은 값이 현재 상태처럼 쓰였다 — 실물 {works}점/{chunks}청크")
        t = rd(os.path.join(N5, doc))
        for m2 in re.finditer(r"myth-docs\.json", t):
            note("LOW", doc, "사라진 통합본 myth-docs.json 을 아직 언급")
            break


# ══ 4. 하네스·작업기록 규약 ═════════════════════════════════════════════
def check_harness():
    ch = os.path.join(TUTOR, "CLAUDE.md")
    if os.path.exists(ch):
        h = rd(ch)
        for k, label in (("F-11", "작업기록"), ("F-8-A", "잘린 목록"), ("H-4", "규칙·예시"),
                         ("B-2", "프로젝트 경계"), ("폴더 add", "폴더 add 금지")):
            if k not in h:
                note("HIGH", "하네스", f"§{k}({label}) 포인터 없음 — 하네스에 없으면 «없는 규칙»")
        # ★모범 예시로 쓰인 폴더 add 만 잡는다. 금지 문구(<폴더>·금지)는 오탐이므로 제외
        for m in re.finditer(r"`git add ([^`]+)`", h):
            arg = m.group(1)
            ctx = h[max(0, m.start() - 60):m.end() + 20]
            if "금지" in ctx or "<" in arg:
                continue
            if re.search(r"[\w가-힣.-]+/(?:\s|$)", arg) and not re.search(r"\.\w+", arg):
                note("HIGH", "하네스", f"폴더 add 를 예시로 가르친다: git add {arg}")

    wd = os.path.join(TUTOR, "작업기록")
    if os.path.isdir(wd):
        for f in sorted(os.listdir(wd)):
            if not f.endswith(".md"): continue
            t = rd(os.path.join(wd, f))
            blocks = re.split(r"^### ", t, flags=re.M)[1:]
            print(f"[작업기록] {f}: {len(blocks)}항목")
            for b in blocks:
                title = b.split("\n")[0][:44]
                # «왜 (원인)» 처럼 뒤에 괄호가 붙어도 인정한다
                miss = [k for k in ("계정", "무엇을", "왜", "결과", "안 한 것", "다음")
                        if not re.search(r"- \*\*" + re.escape(k) + r"[^*]*\*\*", b)]
                if miss:
                    note("MED", "작업기록", f"«{title}» 항목에 빠짐: {miss}")
            if "직전 파일" not in t or "다음 파일" not in t:
                note("MED", "작업기록", f"{f}: 머리말 체인(직전·다음 파일) 없음")


# ══ 5. 핸드오프 · 커밋 SHA ══════════════════════════════════════════════
def check_docs():
    ho = rd(os.path.join(HERE, "HANDOFF-튜터.md"))
    for pat, why in ((r"제출은 아직 안 했다", "제출 완료됨"),):
        if re.search(pat, ho):
            note("HIGH", "핸드오프", f"낡은 값 «{pat}» — {why}")
    for m in re.finditer(r"`((?:tools|data|app)/[\w/.-]+)`", ho):
        if not os.path.exists(os.path.join(N5, m.group(1).replace("/", os.sep))):
            note("MED", "핸드오프", f"없는 파일을 가리킨다: {m.group(1)}")

    docs = {"핸드오프": ho}
    for f in ("README.md", "PRD.md"):
        if os.path.exists(os.path.join(N5, f)):
            docs[f] = rd(os.path.join(N5, f))
    wd = os.path.join(TUTOR, "작업기록")
    if os.path.isdir(wd):
        for f in os.listdir(wd):
            if f.endswith(".md"): docs["작업기록/" + f] = rd(os.path.join(wd, f))
    seen = set()
    for name, t in docs.items():
        for s in set(re.findall(r"`([0-9a-f]{7})`", t)):
            if s in seen: continue
            seen.add(s)
            r = subprocess.run(["git", "cat-file", "-t", s], cwd=REPO,
                               capture_output=True, text=True)
            if r.stdout.strip() != "commit":
                note("MED", name, f"존재하지 않는 커밋 SHA 인용: {s}")
    print(f"[SHA] {len(seen)}개 검증")



def check_bridge_ids():
    """브리지 발신 ID 중복 — 같은 계열·같은 날짜에서 «건수 ≠ 최대번호» 면 중복이거나 결번.
    결번은 안 쓰고 건너뛴 번호라 신호가 아니다(9계열에서 나오는데 진짜는 2건). 중복만 본다.
    정본 §D · 발견 경위 = KBTM-T-20260831-10."""
    BR = os.path.join(os.path.dirname(REPO), os.pardir, "bridge")
    BR = os.path.abspath(BR)
    if not os.path.isdir(BR):
        print("[브리지] 폴더 없음 — 건너뜀"); return
    ID = re.compile(r"^\[(KB[A-Z]+(?:-[A-Z가-힣]+)?)-(\d{8})-(\d+)\]", re.M)
    g, tot = {}, 0
    for f in sorted(os.listdir(BR)):
        if not f.endswith(".md"): continue
        t = io.open(os.path.join(BR, f), encoding="utf-8", errors="replace").read()
        for pre, d, n in ID.findall(t):
            g.setdefault((pre, d), []).append(int(n)); tot += 1
    dup = 0
    for (pre, d), ns in sorted(g.items()):
        for n in sorted(set(x for x in ns if ns.count(x) > 1)):
            dup += 1
            note("MED", "브리지", f"ID 중복 [{pre}-{d}-{n}] x{ns.count(n)} — 원참조로 되짚을 수 없다")
    print(f"[브리지] ID {tot}개 · 계열 {len(g)}개 · 중복 {dup}건")


def main():
    print("튜터 산출물 전수 점검\n" + "─" * 62)
    for fn in (check_control_chars, check_notes, check_n5, check_harness, check_docs, check_bridge_ids):
        try:
            fn()
        except Exception as e:
            note("HIGH", fn.__name__, f"검사 자체가 실패: {type(e).__name__} {e}")
    print("─" * 62)
    if not issues:
        print("✅ 이상 없음")
        return 0
    for sev in ("HIGH", "MED", "LOW"):
        for s, w, m in [i for i in issues if i[0] == sev]:
            print(f"  [{s}] {w} — {m}")
    hi = sum(1 for i in issues if i[0] == "HIGH")
    print(f"\n합계 {len(issues)}건 (HIGH {hi})")
    return 1 if hi else 0


if __name__ == "__main__":
    sys.exit(main())
