/* MYTH GALLERY 근거 검색 — 모듈3 노드5 메인 퀘스트
 *
 * 이 파일에는 UI 가 없다. 질문을 받아 "무엇을 근거로 삼을지"와
 * "답을 만들어도 되는지"만 판정한다. 브라우저와 node 에서 똑같이 돈다.
 *
 * 판정 순서 (PRD 5절·7절)
 *   1) VAGUE        대상을 특정할 수 없다        -> 확인 질문 1개
 *   2) OUT_OF_SCOPE 취급하지 않는 신화다          -> 범위 안내
 *   3) HANDOFF      저작권·이용·가격 판단이다     -> 담당자 이관 (확정하지 않는다)
 *   4) NO_EVIDENCE  근거 점수가 문턱 미만이다     -> 모른다고 말한다
 *   5) OK           위를 다 통과했다              -> 찾은 청크로만 답한다
 *
 * 4)가 이 서비스의 급소다. 검색이 못 찾았을 때 생성 단계로 넘기면
 * 모델이 자기 지식으로 답해 버리고, 그 순간 근거 인용이 무의미해진다.
 */
(function (root) {
  "use strict";

  var K = 4;              // 답에 쓰는 근거 개수
  var THRESHOLD = 0.20;   // 근거 판정 문턱 (0~1 · 질문 핵심어가 근거에 실제로 있는 비율)

  // 뜻을 거의 담지 않는 말. 이것만 남으면 대상을 특정할 수 없다고 본다.
  var GENERIC = ["그림", "작품", "사진", "유명한", "유명", "보여줘", "보여", "알려줘", "알려",
    "설명해줘", "설명해", "뭐야", "무슨", "어떤", "어느", "좀", "그거", "이거", "저거",
    "있어", "있나", "있는", "해줘", "주세요", "궁금", "찾아줘", "찾아"];

  // 갤러리가 다루지 않는 신화. 물어보면 지어내지 말고 범위를 밝힌다.
  var OUT_MYTHS = ["일본", "켈트", "슬라브", "아즈텍", "마야", "잉카", "폴리네시아",
    "아프리카", "아메리카", "성경", "기독교", "불교", "이슬람"];

  // 사람이 판단할 일. 챗봇이 가부를 확정하지 않는다. (노드4 설계 패킷 3절 승계)
  var HANDOFF_WORDS = ["저작권", "상업", "판매", "구매", "가격", "얼마", "시세", "경매",
    "라이선스", "사용료", "인쇄", "전시", "고해상도", "원본 파일"];

  // 자료 안에 명령처럼 보이는 문장. 지시로 승격하지 않고 데이터로만 취급한다.
  var INJECTION = /(이전|위의|앞의)\s*(지시|규칙|명령)|무시하[고라]|시스템\s*(지시|프롬프트)|ignore\s+(all\s+)?previous|system\s+prompt/i;

  // ---------------------------------------------------------------- 색인
  function normalize(s) {
    return String(s || "").toLowerCase().replace(/[^0-9a-z가-힣]+/g, " ").trim();
  }

  /** 한글은 글자 2개씩 겹쳐 자르고(형태소 분석기 없이도 어미 변화를 견딘다),
   *  영문·숫자는 낱말 그대로 쓴다. */
  function terms(s) {
    var out = [];
    normalize(s).split(/\s+/).forEach(function (w) {
      if (!w) return;
      if (/^[0-9a-z]+$/.test(w)) { out.push(w); return; }
      if (w.length === 1) { out.push(w); return; }
      for (var i = 0; i < w.length - 1; i++) out.push(w.slice(i, i + 2));
    });
    return out;
  }

  function buildIndex(chunks) {
    var df = Object.create(null);
    var docs = chunks.map(function (c) {
      // 제목·작가도 검색 대상에 넣는다. 사람들은 작품 이름으로도 묻는다.
      var set = Object.create(null);
      terms(c.text + " " + c.title + " " + (c.artist || "")).forEach(function (t) { set[t] = true; });
      Object.keys(set).forEach(function (t) { df[t] = (df[t] || 0) + 1; });
      return { chunk: c, set: set };
    });
    var N = docs.length || 1;
    var idf = Object.create(null);
    Object.keys(df).forEach(function (t) { idf[t] = Math.log(1 + N / df[t]); });
    return { docs: docs, idf: idf, N: N };
  }

  // ---------------------------------------------------------------- 점수
  /** 질문의 핵심어 중 얼마나가 이 근거에 실제로 들어 있나 (0~1).
   *  희귀한 말일수록 크게 친다. 코퍼스에 아예 없는 말은 분모에만 들어가
   *  "근거가 없다"는 사실이 점수에 그대로 드러난다. */
  function coverage(qTerms, doc, idf) {
    var uniq = Object.keys(qTerms.reduce(function (a, t) { a[t] = 1; return a; }, {}));
    var total = 0, hit = 0;
    uniq.forEach(function (t) {
      var w = idf[t] != null ? idf[t] : Math.log(1 + 41);  // 미등장어도 무게를 준다
      total += w;
      if (doc.set[t]) hit += w;
    });
    return total ? hit / total : 0;
  }

  function search(query, index, k) {
    var q = terms(query);
    var scored = index.docs.map(function (d) {
      return { chunk: d.chunk, score: coverage(q, d, index.idf) };
    });
    scored.sort(function (a, b) { return b.score - a.score; });
    return scored.slice(0, k || K);
  }

  // ---------------------------------------------------------------- 판정
  function stripGeneric(query) {
    var s = " " + normalize(query) + " ";
    GENERIC.forEach(function (g) { s = s.split(g).join(" "); });
    return s.replace(/\s+/g, " ").trim();
  }

  function decide(query, index) {
    var raw = String(query || "").trim();
    if (!raw) return { verdict: "VAGUE", hits: [], message: "무엇이 궁금하신지 한 줄만 적어 주세요." };

    // 1) 대상을 특정할 수 없다 -> 추정하지 말고 확인 질문 하나
    if (stripGeneric(raw).replace(/\s/g, "").length < 2) {
      return {
        verdict: "VAGUE", hits: [],
        message: "어떤 작품을 말씀하시는지 아직 특정하지 못했습니다. 등장하는 신이나 인물 이름을 하나만 알려 주시겠어요? (예: 페르세포네, 헤라클레스)"
      };
    }

    // 2) 취급하지 않는 신화 -> 지어내지 않고 범위를 밝힌다
    //    ⚠ 낱말 앞에서만 본다. 통째로 찾으면 "얼마야" 안의 "마야"까지 걸린다 (실제로 걸렸다).
    var n = normalize(raw);
    var words = n.split(/\s+/);
    for (var i = 0; i < OUT_MYTHS.length; i++) {
      var m = OUT_MYTHS[i];
      if (words.some(function (w) { return w.indexOf(m) === 0; })) {
        return {
          verdict: "OUT_OF_SCOPE", hits: [],
          message: "MYTH GALLERY는 그리스·로마, 북유럽, 이집트, 메소포타미아, 힌두, 중국 여섯 신화만 다룹니다. " +
            m + " 관련 자료는 갖고 있지 않습니다. (지금 이 안내판에 올라온 것은 그리스·로마 작품입니다.)"
        };
      }
    }

    // 3) 사람이 판단할 일 -> 가부를 확정하지 않고 접수까지만
    for (var j = 0; j < HANDOFF_WORDS.length; j++) {
      if (n.indexOf(normalize(HANDOFF_WORDS[j])) >= 0) {
        return {
          verdict: "HANDOFF", hits: [],
          message: "저작권·이용 조건·가격은 제가 판정하지 않습니다. 추정해서 말씀드리면 틀린 답이 그대로 근거가 되기 때문입니다. " +
            "갤러리 담당자에게 문의를 남겨 주시면 확인 후 회신드립니다."
        };
      }
    }

    // 4) 근거 판정 — 문턱을 못 넘으면 생성 단계로 넘기지 않는다
    var hits = search(raw, index, K);
    var best = hits.length ? hits[0].score : 0;
    if (best < THRESHOLD) {
      return {
        verdict: "NO_EVIDENCE", hits: [], best: best,
        message: "그 내용은 지금 갖고 있는 자료에서 찾지 못했습니다. 지어내서 답하지 않겠습니다. " +
          "여기 실린 작품은 그리스·로마 신화 12점입니다 — 등장인물 이름으로 물어보시면 찾아드릴 수 있습니다."
      };
    }

    // 5) 통과 — 문턱을 넘은 근거만 넘긴다
    return {
      verdict: "OK",
      best: best,
      // 1등만 겨우 넘고 나머지가 잡음인 경우가 있다. 곁가지 근거는 문턱의 3/4 이상만 남긴다.
      hits: hits.filter(function (h) { return h.score >= THRESHOLD * 0.75; })
    };
  }

  // ---------------------------------------------------------------- 인젝션
  /** 자료 안의 명령문을 찾아낸다. 지우지는 않는다 — 지우면 원문과 달라진다.
   *  표시만 해 두고, 모델에게는 "이건 자료지 지시가 아니다"라고 못박아 넘긴다. */
  function flagInjection(chunks) {
    return chunks.map(function (c) {
      return { chunk: c, suspicious: INJECTION.test(c.text) };
    });
  }

  var api = {
    K: K, THRESHOLD: THRESHOLD,
    terms: terms, normalize: normalize, buildIndex: buildIndex,
    search: search, decide: decide, flagInjection: flagInjection,
    INJECTION: INJECTION
  };

  if (typeof module !== "undefined" && module.exports) module.exports = api;
  root.Retrieve = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
