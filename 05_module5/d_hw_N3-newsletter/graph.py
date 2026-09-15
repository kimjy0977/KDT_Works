"""뉴스레터 에이전트 — 수집 · 선별 · 요약 · 검수 · 발행.

모듈5 노드2 교안을 따라 만들되, 두 가지를 «우리 조건»에 맞췄다.
  ① OpenAI 키가 없으면 «로컬 Ollama» 로 돈다 (교안은 6강부터 키 필수)
  ② 교안의 「🚀 더 해보기」 중 셋을 본문에 넣었다
     · 8강① 한글 검사 + 재요청        (로컬 모델은 영어로 새기 더 쉽다)
     · 7강③ event 라벨 중복을 «코드»로 제거
     · 4강  tier1 면제에 «상한» 적용

★불러오기만 해도 안전해야 한다 — 실행은 run.py 에서만 일어난다 (11강).
"""
import json
import os
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, Dict, List, Optional, TypedDict
import operator

import feedparser
import requests
import trafilatura
import yaml
from pydantic import BaseModel, Field

from langgraph.graph import START, END, StateGraph
from langgraph.types import Send

HERE = os.path.dirname(os.path.abspath(__file__))

# ★2026-09-14 실측 — 4강 G3(접근)에서 제일 뜻밖이었던 것.
#   Phys.org 기사 본문이 «크롬인 척하면» 403 봇검사에 막혀 0/3 이었다.
#   그런데 그 403 페이지 HTML 에 이렇게 적혀 있었다:
#     「NOTICE TO BOT ADMINISTRATORS: 봇이면 <bot-name> (+contact-url) 형식의
#      descriptive User-Agent 를 쓰라」
#   시킨 대로 «나는 봇입니다»라고 밝혔더니 3/3 통과.
#   ⇒ «사람인 척»하는 쪽이 더 잘 되는 게 아니다. 밝히는 쪽이 통과한다.
#     4강이 G3 에서 robots.txt·약관을 보라고 한 것과 같은 결이다.
UA = {"User-Agent": "KDTNewsletterBot/1.0 (+https://github.com/kimjy0977/KDT_Works; study project)"}


# ══════════════════════════════════════════════════════════════
# 13강 · 설정 — 구조와 내용을 분리한다
# ══════════════════════════════════════════════════════════════
# ★프로필 — 13강 「내 분야로 옮기기」를 «파일 교체»로 만든다.
#   PROFILE=discovery  →  audience_discovery.yaml + settings_discovery.yaml
#   PROFILE 없음        →  audience.yaml + settings.yaml (AI 뉴스)
#   ⇒ 코드는 한 줄도 안 바뀐다. 13강이 말한 «구조와 내용의 분리»가 이것이다.
PROFILE = os.environ.get("PROFILE", "").strip()


def _load(base):
    name = "%s_%s.yaml" % (base, PROFILE) if PROFILE else "%s.yaml" % base
    p = os.path.join(HERE, name)
    if not os.path.exists(p):
        # ★교안의 「없으면 만든다」는 «교안용 편의»다.
        #   실제 프로젝트에서는 바로 멈추는 편이 낫다 — 기본값으로 도는 게 «조용한 실패»다(5강).
        raise SystemExit("설정 파일이 없습니다: %s\n  (PROFILE=%r)" % (p, PROFILE or "(기본)"))
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)


CFG = _load("audience")
SET = _load("settings")


def build_criteria(cfg):
    """audience.yaml → 프롬프트 문단. 함수가 불릴 때마다 «그 시점의» 설정을 읽는다."""
    t = ["[독자] %s" % cfg["독자"]["누구"],
         "이미 아는 것: %s" % cfg["독자"]["이미_아는_것"],
         "",
         "[중요도 기준] 위에 있을수록 우선한다."]
    t += ["  %d. %s" % (i, s) for i, s in enumerate(cfg["중요도_기준"], 1)]
    t += ["", "[버릴 것]"]
    t += ["  - %s" % s for s in cfg["버릴_것"]]
    t += ["", "[토픽]"]
    t += ["  - %s: %s" % (x["이름"], x["데스크지침"]) for x in cfg["토픽"]]
    return "\n".join(t)


CRITERIA = build_criteria(CFG)
TOPICS = [x["이름"] for x in CFG["토픽"]]


# ══════════════════════════════════════════════════════════════
# LLM — 키가 있으면 OpenAI, 없으면 로컬 Ollama
# ══════════════════════════════════════════════════════════════
def get_llm(temperature=0.0):
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if key:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                          temperature=temperature)
    from langchain_ollama import ChatOllama
    return ChatOllama(model=os.environ.get("OLLAMA_MODEL", "qwen2.5:3b"),
                      temperature=temperature, num_ctx=8192, num_predict=1024)


def llm_backend():
    return "OpenAI/%s" % os.environ.get("OPENAI_MODEL", "gpt-4o-mini") \
        if os.environ.get("OPENAI_API_KEY", "").strip() \
        else "Ollama/%s" % os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")


# ══════════════════════════════════════════════════════════════
# 2강 · State — «단계 사이를 건너가는 것»만 담는다
# ══════════════════════════════════════════════════════════════
class Brief(TypedDict):
    hours: int
    collected: List[dict]                      # 덮어쓰기 — 한 노드가 쓰고 다음이 읽는다
    picked: List[dict]                         # 덮어쓰기
    drafted: Annotated[List[dict], operator.add]   # ★여러 취재 워커가 «동시에» 쓴다
    verified: List[dict]                       # ★9강 — 합치는 키와 «줄이는» 키를 나눈다
    log: Annotated[List[str], operator.add]    # 모든 노드가 한 줄씩


# ══════════════════════════════════════════════════════════════
# 5강 · ① 수집
# ══════════════════════════════════════════════════════════════
def strip_tags(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "")).strip()


def published_at(e):
    t = getattr(e, "published_parsed", None) or getattr(e, "updated_parsed", None)
    return datetime(*t[:6], tzinfo=timezone.utc) if t else None


# ★2026-09-14 — 1번(자료수집) 담당 김만영 님의 발견을 «우리 것으로» 재현해 확인했다.
#   `link.split("?")[0]` 은 «추적 꼬리표»를 떼려던 것인데,
#   국내 언론사는 «기사 번호»를 쿼리에 넣는다 → 기사 전체가 한 건으로 뭉개진다.
#     AI타임스  기사 50건 → 「?」 자른 뒤 고유 «1건»  (49건 조용히 소실)
#     전자신문  30건 → 30건 (경로에 번호가 있어 무사)
#   ⇒ 꼬리표를 «통째로» 버리지 말고 «추적 파라미터만» 골라 버린다.
_TRACK = re.compile(r"^(utm_|fbclid$|gclid$|igshid$|mc_cid$|mc_eid$|ref$|source$|spm$)")


def canon(url):
    try:
        from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
        u = urlsplit(url)
        q = [(k, v) for k, v in parse_qsl(u.query, keep_blank_values=True)
             if not _TRACK.match(k)]
        return urlunsplit((u.scheme, u.netloc, u.path, urlencode(sorted(q)), ""))
    except Exception:
        return url.split("?")[0]


def collect(state: Brief) -> dict:
    hours = state.get("hours", SET["hours"])
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    items, seen, dead, per = [], set(), [], {}
    total = 0

    for s in SET["sources"]:
        try:
            r = requests.get(s["url"], headers=UA, timeout=15)
            d = feedparser.parse(r.content)
            n = 0
            for e in d.entries:
                total += 1
                at = published_at(e)
                if not at or at < cutoff:
                    continue                      # 시간 창 · 날짜 없는 항목도 여기서 버려진다
                link = getattr(e, "link", "")
                if not link:
                    continue
                key = canon(link)                 # ★«주소가 같은 것»만 걸러 낸다
                if key in seen:
                    continue
                if per.get(s["name"], 0) >= SET["per_source_cap"]:
                    continue
                seen.add(key)
                per[s["name"]] = per.get(s["name"], 0) + 1
                n += 1
                items.append({"group": s.get("group"),
                              "title": strip_tags(getattr(e, "title", ""))[:300],
                              "url": link, "source": s["name"], "tier": s["tier"],
                              "at": at.isoformat(),
                              "summary": strip_tags(getattr(e, "summary", ""))[:800]})
        except Exception:
            dead.append(s["name"])                # ★이 줄이 없으면 «조용한 실패»

    # ①칸 — Hacker News 공개 API. RSS 에 없는 «비LLM 신호»(points)를 준다
    hn = SET.get("hackernews", {})
    if hn.get("enabled"):
        try:
            j = requests.get(hn["url"], headers=UA, timeout=15).json()
            n = 0
            for h in j.get("hits", []):
                total += 1
                if (h.get("points") or 0) < hn.get("min_points", 0):
                    continue
                ts = h.get("created_at")
                at = datetime.fromisoformat(ts.replace("Z", "+00:00")) if ts else None
                if not at or at < cutoff:
                    continue
                link = h.get("url") or ("https://news.ycombinator.com/item?id=%s" % h.get("objectID"))
                key = link.split("?")[0]
                if key in seen or n >= SET["per_source_cap"]:
                    continue
                seen.add(key)
                n += 1
                items.append({"title": strip_tags(h.get("title", ""))[:300], "url": link,
                              "source": "Hacker News", "tier": 2, "at": at.isoformat(),
                              "summary": "", "points": h.get("points")})
        except Exception:
            dead.append("Hacker News")

    line = "① 수집   %dh 창 · 전체 %d → 후보 %d건 (소스 %d곳)" % (
        hours, total, len(items), len(per) + (1 if any(i["source"] == "Hacker News" for i in items) else 0))
    if dead:
        line += " · ⚠응답없음: %s" % ", ".join(dead)   # 건너뛴 «사실»을 남긴다
    return {"collected": items, "log": [line]}


# ══════════════════════════════════════════════════════════════
# 7강 · ② 선별 — 예선(병렬화 sectioning) → 본선
# ══════════════════════════════════════════════════════════════
class Pick(BaseModel):
    idx: int = Field(description="후보 번호")
    event: str = Field(description="사건 라벨. 같은 사건이면 반드시 같은 짧은 라벨")
    why: str = Field(description="고른 이유 한 줄(한국어)")


class Shortlist(BaseModel):
    picks: List[Pick]


def _fmt(cands):
    return "\n".join("%d. [%s] %s" % (i, c["source"], c["title"]) for i, c in enumerate(cands))


def ask_picks(cands, k, llm):
    sys = (CRITERIA + "\n\n"
           "너는 위 기준으로 기사를 고르는 편집자다.\n"
           "아래 후보 중 «가장 중요한» %d건을 골라라.\n"
           "같은 사건을 다룬 기사는 «하나만» 골라라.\n"
           "event 에는 사건을 식별하는 짧은 라벨을 한국어로 적어라." % k)
    try:
        out = llm.with_structured_output(Shortlist).invoke(
            [("system", sys), ("human", _fmt(cands))])
        return [p for p in out.picks if 0 <= p.idx < len(cands)][:k]
    except Exception:
        return [Pick(idx=i, event=cands[i]["title"][:20], why="(모델 실패 — 순서대로)")
                for i in range(min(k, len(cands)))]


def select(state: Brief) -> dict:
    cands = list(state["collected"])
    llm = get_llm(0.0)
    logs = []

    # tier1(당사자 발표)은 «경쟁 면제». 단 ★면제에도 상한이 있다 (4강)
    t1 = [c for c in cands if c.get("tier") == 1][:SET["tier1_cap"]]
    rest = [c for c in cands if c not in t1]

    # 예선 — 묶음으로 쪼개 «서로 모르는 채로» 처리
    #
    # ★2026-09-15 실측으로 고친 자리 — «묶음을 어떻게 나누느냐»가 결과를 바꾼다.
    #   처음엔 후보를 «들어온 순서대로» 20건씩 잘랐다. 그랬더니 —
    #     본선 2건 · 우주 8건이 주제 상한에 걸림 · 고고/고생물 0건
    #   원인: 우주가 24h 28건으로 제일 많아 «예선 묶음이 우주로만 채워졌고»,
    #        고고·고생물은 **본선에 오기 전에 이미 탈락**했다.
    #   ⇒ 주제 상한은 «본선»에서만 도는데, 앞에서 없어진 건 못 살린다.
    #   ⇒ 그래서 예선 묶음을 «주제별»로 나눈다. 각 주제가 예선 자리를 «보장»받는다.
    #   (8강 팬아웃 경계와 같은 이야기 — 어디서 나누느냐가 답을 바꾼다)
    B, K = SET["batch"], SET["batch_keep"]
    survivors = []
    buckets = {}
    for it in rest:
        buckets.setdefault(it.get("group") or "_", []).append(it)
    for gname, items in buckets.items():
        for i in range(0, len(items), B):
            grp = items[i:i + B]
            picks = ask_picks(grp, min(K, len(grp)), llm)
            for p in picks:
                item = dict(grp[p.idx])
                item["event"] = p.event
                survivors.append(item)
            logs.append("   예선 [%s] %d건 → %d건" % (gname, len(grp), len(picks)))

    pool = t1 + survivors
    if not pool:
        return {"picked": [], "log": ["② 선별   후보 0건"] + logs}

    # 본선 — 예선 통과분이면 «한 화면»에 놓을 수 있다
    finals_idx = ask_picks(pool, min(SET["target"] * 2, len(pool)), llm)
    ranked = []
    for p in finals_idx:
        it = dict(pool[p.idx])
        it["event"] = p.event or it.get("event", "")
        it["why_pick"] = p.why
        ranked.append(it)

    # ★7강 더 해보기 ③ — 프롬프트 «부탁»이 안 지켜지므로 «코드»로 센다
    kept, seen_ev, per_media, per_group, dropped = [], set(), {}, {}, []
    for it in ranked:
        ev = re.sub(r"\s+", "", it.get("event", ""))[:24]
        if ev and ev in seen_ev:
            dropped.append((it["title"][:40], "같은 사건(%s)" % ev))
            continue
        if per_media.get(it["source"], 0) >= SET["media_cap"]:
            dropped.append((it["title"][:40], "매체 상한(%s)" % it["source"]))
            continue
        # ★주제별 자리 배분 — 7강 「매체 상한」과 «같은 코드, 다른 축».
        #   안 걸면 «건수 많은 주제»가 다섯 자리를 다 가져간다.
        #   실측 근거: 우주 24h 28건 vs 고생물 10건 — 그냥 두면 우주가 전부 이긴다.
        gcaps = SET.get("group_caps") or {}
        g = it.get("group")
        if g and gcaps.get(g) is not None and per_group.get(g, 0) >= gcaps[g]:
            dropped.append((it["title"][:40], "주제 상한(%s %d)" % (g, gcaps[g])))
            continue
        seen_ev.add(ev)
        per_media[it["source"]] = per_media.get(it["source"], 0) + 1
        if g:
            per_group[g] = per_group.get(g, 0) + 1
        kept.append(it)
        if len(kept) >= SET["target"]:
            break

    logs.append("② 선별   %d건 → 예선 %d → 본선 %d건 (tier1 면제 %d)"
                % (len(cands), len(pool), len(kept), len(t1)))
    for t, why in dropped:
        logs.append("   − %s … %s" % (t, why))     # ★탈락 «이유»가 없으면 무엇을 고칠지 모른다
    return {"picked": kept, "log": logs}


# ══════════════════════════════════════════════════════════════
# 8강 · ③ 요약(취재) — Send 로 기사 수만큼 펼친다
# ══════════════════════════════════════════════════════════════
class Draft(BaseModel):
    headline: str = Field(description="한국어 헤드라인. 15~40자. 주어와 무엇을 했는지가 «둘 다» 들어가야 한다. 문장을 도중에 끊지 말 것")
    summary: str = Field(description="한국어 요약 3문장. '~합니다'체. 원문에 있는 사실만. 각 문장을 «끝까지» 맺을 것")
    why: str = Field(description="한국어 한 문장. 우리 독자에게 왜 중요한지 (해석 허용)")
    topic: str = Field(description="토픽 이름 하나")


HAS_KO = re.compile(r"[가-힣]")


def extract_body(url):
    try:
        html = requests.get(url, headers=UA, timeout=20).text
        return (trafilatura.extract(html) or "")[:6000]
    except Exception:
        return ""


def draft_sys():
    """취재 프롬프트. ★검수의 «재생성»도 같은 문장을 쓴다 — 두 곳이 갈리면 안 된다."""
    return (CRITERIA + "\n\n너는 국내 독자를 위한 뉴스레터 기자다.\n"
            "반드시 «한국어»로 쓴다. 원문이 영어여도 한국어로 쓴다.\n"
            # ★2026-09-14 실측 — 오역이 «환각처럼» 보이는 자리를 막는다.
            #   Democrats → 「디플레민트 당」 · endemic fauna → 「고유 동물 콘텐츠」
            #   aurochs(들소) → 「황소(en」 처럼, 모델이 모르는 고유명사를 «지어내» 옮긴다.
            #   ⇒ 옮기지 말고 «그대로 두라»고 하면 지어낼 자리가 사라진다.
            "★인명·지명·학명·기관명·장비명 같은 고유명사는 «원문 표기 그대로» 두고\n"
            "  한국어 조사만 붙여라. 예: 「JWST가」 「Levant에서」 「Homo sapiens는」.\n"
            "  한국에서 널리 쓰이는 표기가 «확실할 때만» 한글로 옮겨라(NASA·나사 등).\n"
            "  모르는 이름을 억지로 한글로 옮기지 마라 — 그건 지어내는 것이다.\n"
            "headline·summary 는 원문에 있는 사실만 쓴다. 지어내지 않는다.\n"
            "why 는 우리 독자 관점의 해석이다.\n"
            "topic 은 다음 중 하나: %s" % ", ".join(TOPICS))


def report(state) -> dict:
    """워커. 메인 State 가 아니라 {'item': 기사 하나} 를 받는다 — 전체 상황을 모른다."""
    it = state["item"]
    body = extract_body(it["url"])
    if len(body) < SET["body_min"]:
        # 모자란다고 «다시 긁어 오지 않는다». 그날은 적게 발행한다
        return {"drafted": [], "log": ["   ⚠본문 부족(%d자) — %s" % (len(body), it["title"][:40])]}

    sysmsg = draft_sys()
    human = "[제목] %s\n[매체] %s\n\n[본문]\n%s" % (it["title"], it["source"], body[:5000])

    # ★2026-09-15 실측 — 재시도가 «사실상 1회»였다.
    #   temperature=0 은 결정적이라 같은 입력에 «같은 출력»이 나온다.
    #   그래서 「한국어로 다시 써라」를 세 번 말해도 세 번 다 같은 영어가 돌아왔다.
    #   실측: 한국어 실패 3건 모두 「3회 재시도」로 찍혔는데 실은 한 번을 세 번 센 것이다.
    #   ⇒ 재시도는 «온도를 올려야» 재시도다. 사실을 옮기는 1차 시도만 0.0 으로 둔다.
    #   ★2026-09-15 2차 — 온도를 «너무» 올렸더니 이번엔 다국어가 섞였다.
    #     실측: 「아주古老的 woolly rhinos」 「아크티브ブラック홀」 「근처galaxy」
    #     ⇒ 한국어 실패는 줄었는데 «한자·가나»가 들어왔다. 트레이드오프다.
    #     0.9 는 3B 모델에 과했다. 살짝만 흔든다.
    RETRY_TEMPS = [0.0, 0.25, 0.45]
    d, retried = None, 0
    for attempt, temp in enumerate(RETRY_TEMPS):
        llm = get_llm(temp)
        try:
            d = llm.with_structured_output(Draft).invoke(
                [("system", sysmsg + ("\n\n★직전 출력이 한국어가 아니었다.\n"
                                      "  이번에는 «반드시» 한국어 문장으로 써라.\n"
                                      "  headline·summary·why 세 칸 «모두» 한글이 들어가야 한다.\n"
                                      "  영어 고유명사는 그대로 두되 «조사와 서술어는 한국어»로."
                                      if attempt else "")),
                 ("human", human)])
        except Exception:
            d = None
        # ★8강 더 해보기 ① — 「한글이 있는가」는 «출력만 보고» 확인할 수 있다 → 코드로 강제
        if d and HAS_KO.search(d.summary or "") and HAS_KO.search(d.headline or ""):
            break
        retried += 1
        d = None
    if not d:
        return {"drafted": [], "log": ["   ⚠한국어 실패(%d회 재시도) — %s"
                                       % (retried, it["title"][:40])]}

    out = dict(it)
    out.update({"headline": d.headline.strip()[:120], "summary": d.summary.strip(),
                "why": d.why.strip(), "topic": d.topic.strip(), "body": body,
                "retried": retried})
    note = "   · %s%s" % (d.headline.strip()[:34], " (재시도 %d)" % retried if retried else "")
    return {"drafted": [out], "log": [note]}


def fan_report(state: Brief):
    """팬아웃 «경계» — 여기부터 뒤는 「다른 항목을 안 봐도 답할 수 있다」."""
    picked = state.get("picked") or []
    if not picked:
        return "verify"
    return [Send("report", {"item": it}) for it in picked]


# ══════════════════════════════════════════════════════════════
# 9강 · ④ 검수 — LLM 대조. headline·summary 만. why 는 «대조 대상이 없다»
# ══════════════════════════════════════════════════════════════
class Verdict(BaseModel):
    ok: bool = Field(description="요약의 모든 주장이 원문에서 뒷받침되면 true")
    problems: List[str] = Field(default_factory=list, description="문제가 된 부분")


# ★규칙 검사(9강 ②칸)를 «앞»에 겹쳐 둔다.
#   9강은 ③(LLM 대조)을 골랐지만 「②를 버린다」는 뜻이 아니다.
#   ②가 구조적으로 오탐하는 것은 «번역·단위 환산»이고,
#   「문장이 끊겼는가」는 번역과 무관하게 «문자열로» 확인된다 — 그러면 코드가 맞다.
#   실측 2026-09-14: LLM 검수는 끊긴 문장을 «통과»시켰다(5케이스 중 1). 코드는 잡는다.
_ENDS_OK = re.compile(r"(다|요|음|함|됨|임)[.!?\"'’”)\]]*\s*$")


def rule_check(d):
    probs = []
    s = (d.get("summary") or "").strip()
    h = (d.get("headline") or "").strip()
    if len(h) < 8:
        probs.append("헤드라인이 %d자 — 잘렸을 가능성" % len(h))
    if len(s) < 40:
        probs.append("요약이 %d자 — 너무 짧다" % len(s))
    elif not _ENDS_OK.search(s):
        probs.append("요약 마지막 문장이 «맺어지지 않았다»: …%s" % s[-18:])
    # ★2026-09-14 — 이 한 줄을 «두 번» 잘못 썼다. 둘 다 «정상 한국어»를 불합격시켰다.
    #     1차 r"[A-Za-z]{2,}[가-힣]"        → 「오픈AI가」·「API를」  (대문자 약어 + 조사)
    #     2차 r"...|[a-z]{2,}[가-힣]"       → 「Tapper에게」·「Altman은」 (영문 고유명사 + 조사)
    #   둘 다 «한국어에서 정상인 표기»다. 실제 결함은 한 방향뿐이었다 —
    #   «한글 뒤에» 소문자 영문 조각이 붙는 것(실측: 「정acing」).
    #   ⇒ «아니다»를 판정하는 검사가 제일 위험하다 — 「맞다」를 놓치면 한 번 더 보지만
    #      「아니다」로 찍히면 아예 안 본다. 그래서 방향을 «하나»로 좁혔다.
    m = re.search(r"[가-힣][a-z]{2,}", s)
    if m:
        probs.append("한글 뒤에 «소문자 영문»이 붙었다: %s" % m.group())
    # ★2026-09-15 — 재시도 온도를 올렸더니 «한자·가나»가 섞였다.
    #   「아주古老的」 「아크티브ブラック홀」. 한국어 기사에 CJK 한자/가나는 나올 일이 없다.
    #   (고유명사를 원문 그대로 두라고 했지만 그건 «라틴 문자» 얘기다)
    m2 = re.search(r"[一-鿿぀-ヿ]", (d.get("headline") or "") + " " + s)
    if m2:
        probs.append("한자·가나가 섞였다: %s" % m2.group())
    return probs


# ★2026-09-14 — 숫자 «지목»이 새 오탐을 냈다.
#   요약 「40만년」 vs 원문 「400,000 years」 를 «원문에 없는 숫자»로 지목했고
#   그 힌트를 받은 LLM 이 멀쩡한 요약을 불합격시켰다.
#   9강이 ②(숫자 문자열 대조)를 버린 이유가 «번역·단위 환산 오탐»이었는데,
#   내가 ②를 «지목»으로 되살리면서 그 오탐도 같이 되살린 것이다.
#   ⇒ 한국어 만/억 단위를 «값»으로 펴서 비교한다. 한 숫자가 여러 값을 가질 수 있다
#     (「40만」은 400000 이기도 하고, 문자열 40 이기도 하다).
_KO_UNIT = {"만": 10 ** 4, "억": 10 ** 8, "조": 10 ** 12}
# 영어 쪽도 같이 편다 — 「6000만 달러」 vs 「$60 million」 이 같은 값임을 알아야 한다
_EN_UNIT = {"thousand": 10 ** 3, "million": 10 ** 6, "billion": 10 ** 9, "trillion": 10 ** 12}
_NUM = re.compile(r"(\d[\d,.]*)\s*([만억조]|thousand|million|billion|trillion)?", re.I)


def _nums_ko(text):
    """숫자 표기 → 가능한 «값» 집합. {표기: {값들}}"""
    out = {}
    for m in _NUM.finditer(text or ""):
        raw, unit = m.group(1), m.group(2)
        label = raw + (" " + unit if unit and unit[0].isalpha() else (unit or ""))
        try:
            base = float(raw.replace(",", "").rstrip("."))
        except ValueError:
            continue
        vals = {base}
        if unit:
            u = _KO_UNIT.get(unit) or _EN_UNIT.get(unit.lower())
            if u:
                vals.add(base * u)
        out.setdefault(label, set()).update(vals)
    return out


def body_nums_values(body_map):
    vals = set()
    for s in body_map.values():
        vals |= s
    return vals


def redraft(d, problems):
    """★검수 불합격분을 «지적을 붙여» 다시 쓰게 한다 (9강 선택지 ①).

    9강은 셋 중 ③「버리고 로그에 남긴다」를 골랐고 우리도 그것을 «최후»로 둔다.
    다만 ①을 «한 번만» 앞에 넣었다 —
      · 값을 건진다: 본문 추출까지 끝난 건을 버리는 건 아깝다
      · ①의 약점인 「재시도 이력이 노드 안에 숨는다」는 **로그에 남겨** 없앴다
      · 비용 상한: **재생성은 건당 1회**. 그래도 안 되면 스킵한다
        (상한이 없으면 「언제까지 다시 시도할 것인가」가 통제되지 않는다 — 9강)

    ★반환은 «(원고, 사유)» 둘이다. 실패할 때 원고만 None 으로 주면
      「재생성 실패」라고만 남고 **왜** 실패했는지가 사라진다 — 12강의 「조용한 실패」다.
    """
    body = d.get("body") or ""
    if len(body) < SET["body_min"]:
        return None, "본문 %d자(기준 %d)" % (len(body), SET["body_min"])
    fix = ("\n\n★이전 원고가 검수에서 불합격했다. 지적은 다음과 같다:\n"
           + "\n".join("  - " + p for p in problems[:5])
           + "\n지적된 부분을 «고쳐서» 다시 써라. 원문에 없는 내용은 절대 넣지 마라.\n"
             "확실하지 않은 고유명사는 «원문 표기 그대로» 두어라.")
    why = []
    for temp in (0.0, 0.3):
        try:
            nd = get_llm(temp).with_structured_output(Draft).invoke(
                [("system", draft_sys() + fix),
                 ("human", "[제목] %s\n[매체] %s\n\n[이전 원고]\n%s\n%s\n\n[본문]\n%s"
                  % (d["title"], d["source"], d.get("headline", ""), d.get("summary", ""),
                     body[:5000]))])
        except Exception as exc:
            why.append("t%.1f 호출오류 %s" % (temp, type(exc).__name__))
            continue
        if not nd:
            why.append("t%.1f 빈 응답" % temp)
        elif not (HAS_KO.search(nd.summary or "") and HAS_KO.search(nd.headline or "")):
            why.append("t%.1f 한국어 아님" % temp)
        else:
            out = dict(d)
            out.update({"headline": nd.headline.strip()[:120], "summary": nd.summary.strip(),
                        "why": nd.why.strip(), "topic": nd.topic.strip(), "redrafted": True})
            return out, ""
    return None, " / ".join(why)


def verify(state: Brief) -> dict:
    drafted = state.get("drafted") or []
    if not drafted:
        return {"verified": [], "log": ["④ 검수   0건"]}
    llm = get_llm(0.0)
    passed, logs = [], []
    n_redraft = n_saved = 0

    def judge(d):
        """규칙 + 숫자지목 + LLM 대조. (합격여부, 지적목록)"""
        rp = rule_check(d)
        if rp:
            return False, ["[규칙] " + p for p in rp]
        hint = ""
        nums = _nums_ko(d.get("summary") or "")
        unmatched = sorted(k for k, v in nums.items()
                           if not (v & body_nums_values(_nums_ko(d.get("body") or ""))))
        if unmatched:
            hint = ("\n\n★다음 숫자는 [원문]에서 «문자열 그대로»는 찾지 못했다: %s\n"
                    "  번역이나 단위 환산(60 million → 6000만)의 결과일 수 있으니 «값»으로 대조하라.\n"
                    "  값으로도 맞지 않으면 ok=false 다." % ", ".join(unmatched[:8]))
        try:
            v = llm.with_structured_output(Verdict).invoke([
                ("system", "너는 사실 검수자다. 아래 «요약»의 각 주장이 «원문»에서 뒷받침되는지 판정한다.\n"
                           "★판정 대상은 [요약] 블록뿐이다. 이 지시문에 적힌 낱말을 요약의 내용으로 «세지 마라».\n"
                           "영어를 한국어로 옮긴 것과 단위를 한국식으로 환산한 것은 «정상»이다. 환각이 아니다.\n"
                           "다음 중 하나라도 있으면 ok=false 로 한다.\n"
                           "  - [원문]에 없는 사실이나 숫자가 [요약]에 추가됨\n"
                           "  - [원문]에 없는 «고유명사»(인명·정당명·회사명·제품명)가 [요약]에 등장함\n"
                           "둘 다 아니면 ok=true 로 한다." + hint),
                ("human", "[요약]\n%s\n%s\n\n[원문]\n%s"
                 % (d["headline"], d["summary"], (d.get("body") or "")[:4000]))])
        except Exception:
            return True, ["(검수 호출 실패 — 통과 처리)"]
        probs = list(v.problems or [])
        # ★ok=false 인데 지적이 비어 오는 일이 실제로 있다(모델이 필드를 안 채운다).
        #   그대로 두면 로그에 «빈 괄호»만 남아 왜 떨어졌는지 알 수 없다.
        if not v.ok and not probs:
            probs = ["(모델이 사유를 적지 않음 — ok=false 만 왔다)"]
        return bool(v.ok), probs

    for d in drafted:
        ok, probs = judge(d)
        if ok:
            passed.append(d)
            continue
        # ★1차 불합격 → «재생성» 1회
        logs.append("   ✗ %s … %s" % (d["headline"][:30], "; ".join(probs)[:80]))
        nd, fail = redraft(d, probs)
        n_redraft += 1
        if not nd:
            logs.append("     ↳ 재생성 실패 → 스킵: %s" % (fail or "사유 미기재"))
            continue
        ok2, probs2 = judge(nd)
        if ok2:
            passed.append(nd)
            n_saved += 1
            logs.append("     ↳ ★재생성 후 합격: %s" % nd["headline"][:34])
        else:
            logs.append("     ↳ 재생성해도 불합격 → 스킵: %s" % "; ".join(probs2)[:60])

    head = "④ 검수   %d건 → 합격 %d · 불합격 %d" % (
        len(drafted), len(passed), len(drafted) - len(passed))
    if n_redraft:
        head += "  (재생성 %d회 · 그중 %d건 회복)" % (n_redraft, n_saved)
    logs.insert(0, head)
    return {"verified": passed, "log": logs}


# ══════════════════════════════════════════════════════════════
# 10강 · ⑤ 발행 — 되돌릴 수 없는 곳. 여기엔 언어 모델을 «넣지 않는다»
# ══════════════════════════════════════════════════════════════
COLORS = {"모델·API": 0x0B6E77, "에이전트·도구": 0x2E7D32, "정책·규제": 0xB26A00,
          "연구": 0x5E35B1, "사건·장애": 0xC62828}


def build_embeds(items, when):
    D = SET["discord"]
    # ★2026-09-15 — 머리말 제목이 「AI 브리핑」으로 «코드에 박혀» 있었다.
    #   프로필을 「발견」으로 바꿔 발행했는데 카드 머리말은 여전히 「AI 브리핑」이었다.
    #   13강이 말한 그 자리다 — «분야가 바뀌면 달라지는 값»은 설정에 있어야 한다.
    #   코드에 박힌 문구는 «프로필을 갈아 끼워도 안 따라온다».
    title = D.get("title") or "브리핑"
    head = {"title": "📰 %s · %s" % (when, title),
            "description": ("오늘은 %d건을 골랐습니다. (%s)"
                            % (len(items), ", ".join(sorted({i["source"] for i in items})))
                            if items else "오늘은 조용합니다."),
            "color": 0x0B6E77}
    out = [head]
    for n, it in enumerate(items, 1):
        desc = "%s\n\n💡 **%s**" % (it["summary"], it["why"])
        out.append({"title": ("%d. %s" % (n, it["headline"]))[:D["title_max"]],
                    "description": desc[:D["desc_max"]],
                    "url": it["url"],
                    "color": COLORS.get(it.get("topic", ""), 0x546E7A),
                    "footer": {"text": "%s · %s" % (it["source"], it.get("topic", "기타"))}})
    return out[:D["embed_max"]]


def send(embeds, dry_run=True):
    D = SET["discord"]
    total = sum(len(json.dumps(e, ensure_ascii=False)) for e in embeds)
    if dry_run:
        print("[dry-run] embed %d개 · %d자 — 보내지 않음" % (len(embeds), total))
        for e in embeds:
            print(json.dumps(e, ensure_ascii=False, indent=2)[:900])
        return 0
    if total > D["total_max"]:                    # ★넘으면 «아무것도» 발행되지 않는다
        embeds = embeds[:max(1, len(embeds) // 2)]
    url = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    if not url:
        raise SystemExit("DISCORD_WEBHOOK_URL 이 없습니다 (.env 확인)")
    r = requests.post(url, json={"username": D["username"], "embeds": embeds}, timeout=20)
    print("[send] HTTP %s%s" % (r.status_code, "  ← 204 는 «성공»이다" if r.status_code == 204 else ""))
    return r.status_code


QUIET_MARK = os.path.join(HERE, "store", "last_quiet.txt")


def quiet_already_sent(when):
    """오늘 «조용합니다»를 이미 보냈는가."""
    try:
        with open(QUIET_MARK, encoding="utf-8") as f:
            return f.read().strip() == when
    except Exception:
        return False


def publish(state: Brief) -> dict:
    items = state.get("verified") or []
    dry = os.environ.get("DRY_RUN", "1") != "0"   # ★기본은 «보내지 않음»
    when = datetime.now().strftime("%Y-%m-%d")

    # ★0건인 날에도 보내는 건 «의도»다 — 안 보내면 파이프라인이 죽은 것과 구분이 안 된다.
    #   다만 그 규칙은 **하루 한 번 도는 것**을 전제한다. 그 전제가 코드에 없었다.
    #   실사고 2026-09-15 — 카드 제목을 고치려고 --send 를 단 채 두 번 더 돌렸더니
    #   채널에 「오늘은 조용합니다」가 **두 장** 올라갔다(11:49 · 11:52, 둘 다 HTTP 204).
    #   ⇒ 0건 알림은 «하루 한 번»으로 못 박는다. 기사가 있는 날은 상한이 없다 —
    #     그건 내용이 다르지만, 조용합니다는 **몇 번을 보내도 같은 말**이기 때문이다.
    if not items and not dry and quiet_already_sent(when):
        return {"log": ["⑤ 발행   0건 · 건너뜀 — 「오늘은 조용합니다」는 이미 오늘 보냈다"]}

    embeds = build_embeds(items, when)
    code = send(embeds, dry_run=dry)

    if not items and not dry and str(code).startswith("2"):
        os.makedirs(os.path.dirname(QUIET_MARK), exist_ok=True)
        with open(QUIET_MARK, "w", encoding="utf-8") as f:
            f.write(when)

    return {"log": ["⑤ 발행   %d건 · %s (embed %d장%s)"
                    % (len(items), "dry-run" if dry else "HTTP %s" % code, len(embeds),
                       "" if items else " · 「오늘은 조용합니다」")]}


# ══════════════════════════════════════════════════════════════
# 2강 · 그래프 — 노드를 «이름»으로 찾는다
# ══════════════════════════════════════════════════════════════
def build():
    g = StateGraph(Brief)
    for n in ("collect", "select", "report", "verify", "publish"):
        g.add_node(n, globals()[n])
    g.add_edge(START, "collect")
    g.add_edge("collect", "select")
    g.add_conditional_edges("select", fan_report, ["report", "verify"])
    g.add_edge("report", "verify")
    g.add_edge("verify", "publish")
    g.add_edge("publish", END)
    return g


INIT = {"hours": SET["hours"], "collected": [], "picked": [],
        "drafted": [], "verified": [], "log": []}


# ══════════════════════════════════════════════════════════════
# 12강 · 운영 — 실행마다 한 줄
# ══════════════════════════════════════════════════════════════
def run(hours=None):
    t0 = time.time()
    init = dict(INIT)
    if hours:
        init["hours"] = int(hours)
    out = build().compile().invoke(init)

    stamp = datetime.now()
    row = {"run_id": stamp.strftime("%Y-%m-%dT%H:%M:%S"),
           "backend": llm_backend(), "profile": PROFILE or "(기본)",
           "hours": init["hours"],
           "collected": len(out.get("collected") or []),
           "picked": len(out.get("picked") or []),
           "drafted": len(out.get("drafted") or []),
           "published": len(out.get("verified") or []),
           "by_source": {}, "by_group": {},
           "elapsed_s": round(time.time() - t0, 1),
           "log": out.get("log") or []}
    for it in (out.get("verified") or []):
        row["by_source"][it["source"]] = row["by_source"].get(it["source"], 0) + 1
        g = it.get("group") or "-"
        row["by_group"][g] = row["by_group"].get(g, 0) + 1
    d = os.path.join(HERE, "store")
    os.makedirs(d, exist_ok=True)

    # ★실행 로그 «전문»을 파일로도 남긴다.
    #   metrics.jsonl 은 숫자를, 이 파일은 «그날 무슨 일이 있었는지»를 담는다.
    #   화면 출력은 창을 닫으면 사라진다 — 「오류 없이 끝까지 돌았다」의 증거가
    #   화면에만 있으면 나중에 아무것도 못 보여준다.
    #   ⚠ 로그 파일을 «먼저» 쓰고 그 이름을 row 에 넣는다 — 순서를 바꾸면
    #     jsonl 에 log_file 이 빠진다(실제로 한 번 그렇게 빠뜨렸다).
    logp = os.path.join(d, "run-%s.log" % stamp.strftime("%Y%m%d-%H%M"))
    with open(logp, "w", encoding="utf-8") as f:
        f.write("실행 %s · 프로필 %s · 백엔드 %s · 창 %dh · %.1fs\n"
                % (row["run_id"], row["profile"], row["backend"], row["hours"], row["elapsed_s"]))
        f.write("깔때기  수집 %d → 선별 %d → 취재 %d → 발행 %d\n"
                % (row["collected"], row["picked"], row["drafted"], row["published"]))
        f.write("=" * 70 + "\n")
        for line in row["log"]:
            f.write(line + "\n")
    row["log_file"] = os.path.basename(logp)

    with open(os.path.join(d, "metrics.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    out["_metrics"] = row
    return out
