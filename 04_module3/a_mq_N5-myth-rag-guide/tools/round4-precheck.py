# -*- coding: utf-8 -*-
"""실험 4바퀴 사전 점검 — 돌리기 전에 조건이 갖춰졌는지 본다 (모듈3 노드5)

왜. 4바퀴는 1시간 30분짜리다. 30분쯤 돌다가 «모델이 없다»로 죽으면 그 시간이 통째로
날아간다. 그리고 더 나쁜 것은 **조건이 어긋난 채로 끝까지 도는 것**이다 —
예를 들어 6신화를 다 안 불러온 상태로 eval-hits 를 뽑으면 3바퀴와 같은 조건이 아닌데
숫자는 멀쩡히 나온다. 그러면 틀린 비교를 믿게 된다.

실행: python tools/round4-precheck.py
전부 ✅ 여야 시작한다.
"""
import io, json, os, shutil, sys, urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
OLLAMA = "http://localhost:11434"
MODEL = "qwen3.5:2b"
MYTHS = ["greek", "norse", "egypt", "meso", "hindu", "chinese"]

rows = []


def ok(cond, name, detail, fix=""):
    rows.append((bool(cond), name, detail, fix))


def get(url, timeout=6):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8", "replace")


# ── 1. Ollama ────────────────────────────────────────────────────────────
try:
    st, body = get(OLLAMA + "/api/tags")
    tags = json.loads(body)
    names = [m["name"] for m in tags.get("models", [])]
    ok(st == 200, "Ollama 응답", f"HTTP {st} · 모델 {len(names)}개",
       "Ollama 앱을 실행한다")
    ok(MODEL in names, f"모델 {MODEL}", ", ".join(names) or "(없음)",
       f"ollama pull {MODEL}")
except Exception as e:
    ok(False, "Ollama 응답", f"연결 실패: {e}", "Ollama 앱을 실행한다")
    ok(False, f"모델 {MODEL}", "확인 불가", f"ollama pull {MODEL}")

# ── 2. 벡터스토어 ────────────────────────────────────────────────────────
idx_path = os.path.join(ROOT, "myth-docs-index.json")
try:
    idx = json.load(io.open(idx_path, encoding="utf-8"))
    have = {s["myth"] for s in idx["shards"]}
    missing = [m for m in MYTHS if m not in have]
    ok(not missing, "샤드 6종",
       f"청크 {idx['built']:,} · 작품 {sum(s['works'] for s in idx['shards']):,}"
       + (f" · 빠짐 {missing}" if missing else ""),
       "python data/harvest.py --broad 후 npm run build:vectors")
    ok("starter" in idx, "starter 샤드",
       str(idx.get("starter", "(없음)")), "tools/build-works.py 후 starter 재생성")
except Exception as e:
    ok(False, "샤드 6종", f"index 읽기 실패: {e}", "myth-docs-index.json 확인")
    ok(False, "starter 샤드", "확인 불가", "")

# ── 3. eval-hits 신선도 ──────────────────────────────────────────────────
hits_path = os.path.join(HERE, "eval-hits.json")
try:
    hits = json.load(io.open(hits_path, encoding="utf-8"))
    myth_of = lambda h: h["id"].split("-")[0]
    seen = {myth_of(h) for x in hits for h in x["hits"]}
    stale = seen <= {"greek"}
    ok(len(hits) == 13, "고정 질문 13문항", f"{len(hits)}문항",
       "문항을 바꾸면 3바퀴와 비교가 끊긴다")
    # ★핵심 — 옛 파일은 그리스로마만 후보였다. 그대로면 4바퀴가 아니다.
    ok(not stale, "eval-hits 가 6신화를 봤나",
       "후보에 든 신화: " + ", ".join(sorted(seen)),
       "★ROUND4.md ①번 — 6신화를 모두 loadMyth 한 뒤 재생성한다")
    r3 = os.path.join(HERE, "eval-hits-r3.json")
    ok(os.path.exists(r3), "3바퀴 백업 보존",
       "eval-hits-r3.json " + ("있음" if os.path.exists(r3) else "★없음"),
       "재생성 전에 cp tools/eval-hits.json tools/eval-hits-r3.json")
except Exception as e:
    ok(False, "고정 질문 13문항", f"읽기 실패: {e}", "")
    ok(False, "eval-hits 가 6신화를 봤나", "확인 불가", "")
    ok(False, "3바퀴 백업 보존", "확인 불가", "")

# ── 4. 3바퀴 결과 보존 ───────────────────────────────────────────────────
keep = [f for f in ("variant-base.json", "variant-prompt.json", "variant-topk5.json",
                    "variant-combo.json", "variant-big.json")
        if os.path.exists(os.path.join(HERE, f))]
ok(len(keep) >= 3, "3바퀴 원자료 보존", f"{len(keep)}개: {', '.join(keep)}",
   "덮어쓰기 전에 variant-*.json 을 r3 접미사로 옮긴다")

# ── 5. 디스크 ────────────────────────────────────────────────────────────
free = shutil.disk_usage(ROOT).free / (1024 ** 3)
ok(free > 5, "디스크 여유", f"{free:.1f} GB", "5GB 이상 확보")

# ── 출력 ────────────────────────────────────────────────────────────────
print("\n실험 4바퀴 사전 점검\n" + "─" * 62)
bad = 0
for good, name, detail, fix in rows:
    print(f"  {'✅' if good else '❌'} {name:<24} {detail}")
    if not good:
        bad += 1
        if fix:
            print(f"      → {fix}")
print("─" * 62)
if bad:
    print(f"❌ {bad}건 미충족 — 위 «→» 를 처리한 뒤 다시 돌린다.\n")
    sys.exit(1)
print("✅ 전부 충족. tools/ROUND4.md 3절 순서대로 시작한다.\n")
