# -*- coding: utf-8 -*-
"""★한국어 질의 → 영어 지식원. 사전 하나로 잇는다.

왜 필요한가 — 실측으로 드러났다
  search_article("달 탐사")  → 0건
  search_article("폼페이")   → 0건
  search_article("화석")     → 0건
  지식원(RSS 14곳)이 «영어»이고 질문은 «한국어»라 토큰이 겹칠 수가 없다.

★노드4 에는 없던 문제다
  모두몰은 매뉴얼도 문의도 한국어였다. **「같은 언어」라는 전제**가 깔려 있었고,
  그 전제가 깨지면 **검색이 통째로 죽는다.** 점수가 낮아지는 게 아니라 0 이 된다.

왜 «사전»인가 — 다른 방법과 견줘서
  ⛔ 기사 72건을 번역   LLM 72회 호출. 느리고, 번역 오류가 지식원에 «박힌다»
  ⛔ 질의를 LLM 으로 확장  매 질문마다 호출 1회 추가. 그리고 «비결정적»이다
  ✅ 사전               0회 호출 · 결정적 · 틀리면 «어디가» 틀렸는지 보인다
  ⇒ 어제 배운 것과 같은 판단이다 — 규칙으로 되는 자리에 모델을 넣지 않는다.

한계 (정직하게)
  · 사전에 «없는» 말은 여전히 0건이다. 그래서 miss 를 «세는» 도구를 같이 둔다.
  · 고유명사는 표기가 갈린다 (튀르키예/터키, 마야/Maya)
"""

# 한국어 → 영어 «여러 개». 하나라도 걸리면 된다.
KO_EN = {
    # ── 우주 ──────────────────────────────────────────
    "달": ["moon", "lunar"],
    "태양": ["sun", "solar"],
    "지구": ["earth", "terrestrial"],
    "화성": ["mars", "martian"],
    "금성": ["venus"],
    "수성": ["mercury"],
    "목성": ["jupiter"],
    "토성": ["saturn"],
    "천왕성": ["uranus"],
    "해왕성": ["neptune"],
    "명왕성": ["pluto"],
    "행성": ["planet", "exoplanet"],
    "외계행성": ["exoplanet"],
    "항성": ["star", "stellar"],
    "별": ["star", "stellar"],
    "은하": ["galaxy", "galactic"],
    "은하수": ["milky way"],
    "성운": ["nebula"],
    "블랙홀": ["black hole"],
    "초신성": ["supernova"],
    "소행성": ["asteroid"],
    "혜성": ["comet"],
    "운석": ["meteorite", "meteor"],
    "유성": ["meteor"],
    "망원경": ["telescope"],
    "제임스웹": ["webb", "jwst"],
    "허블": ["hubble"],
    "탐사선": ["spacecraft", "probe", "orbiter", "rover", "mission"],
    "탐사": ["mission", "exploration", "probe"],
    "로버": ["rover"],
    "위성": ["satellite", "moon"],
    "궤도": ["orbit"],
    "발사": ["launch"],
    "우주": ["space", "cosmic", "universe"],
    "우주선": ["spacecraft"],
    "우주인": ["astronaut"],
    "관측": ["observation", "observe", "detect"],
    "적색편이": ["redshift"],
    "중력파": ["gravitational wave"],
    "암흑물질": ["dark matter"],
    "성간": ["interstellar"],
    "크레이터": ["crater"],
    "분화구": ["crater"],
    "일식": ["eclipse"],
    "오로라": ["aurora"],
    "태양풍": ["solar wind", "space weather"],

    # ── 고고학 ────────────────────────────────────────
    "고고학": ["archaeology", "archaeological"],
    "유적": ["site", "ruin", "settlement"],
    "유물": ["artifact", "artefact", "relic"],
    "발굴": ["excavation", "excavate", "dig", "unearth"],
    "무덤": ["tomb", "burial", "grave"],
    "고분": ["tomb", "burial mound"],
    "미라": ["mummy", "mummified"],
    "문자": ["script", "inscription", "writing"],
    "점토판": ["tablet", "cuneiform"],
    "해독": ["decipher", "decode"],
    "비문": ["inscription"],
    "토기": ["pottery", "ceramic"],
    "도자기": ["pottery", "porcelain"],
    "석기": ["stone tool", "lithic"],
    "청동기": ["bronze age"],
    "철기": ["iron age"],
    "신석기": ["neolithic"],
    "구석기": ["paleolithic", "palaeolithic"],
    "피라미드": ["pyramid"],
    "이집트": ["egypt", "egyptian"],
    "로마": ["roman", "rome"],
    "그리스": ["greek", "greece"],
    "폼페이": ["pompeii"],
    "마야": ["maya", "mayan"],
    "잉카": ["inca"],
    "메소포타미아": ["mesopotamia"],
    "동굴": ["cave"],
    "벽화": ["rock art", "cave art", "mural"],
    "난파선": ["shipwreck", "wreck"],
    "고대": ["ancient"],
    "문명": ["civilization", "civilisation"],
    "의례": ["ritual"],
    "제단": ["altar"],
    "성벽": ["wall", "fortification"],
    "라이다": ["lidar"],
    "스톤헨지": ["stonehenge"],

    # ── 고생물 ────────────────────────────────────────
    "화석": ["fossil", "fossilized"],
    "공룡": ["dinosaur"],
    "티라노사우루스": ["tyrannosaurus", "t. rex", "trex"],
    "멸종": ["extinction", "extinct"],
    "진화": ["evolution", "evolutionary"],
    "계통": ["lineage", "phylogen"],
    "조상": ["ancestor", "ancestral"],
    "종": ["species"],
    "뼈": ["bone", "skeleton"],
    "두개골": ["skull", "cranium"],
    "이빨": ["tooth", "teeth"],
    "발자국": ["track", "footprint", "trackway"],
    "깃털": ["feather", "plumage"],
    "비늘": ["scale"],
    "암모나이트": ["ammonite"],
    "삼엽충": ["trilobite"],
    "매머드": ["mammoth"],
    "네안데르탈인": ["neanderthal"],
    "호모": ["homo", "hominin"],
    "인류": ["human", "hominin"],
    "포유류": ["mammal"],
    "파충류": ["reptile"],
    "어류": ["fish"],
    "곤충": ["insect"],
    "호박": ["amber"],
    "백악기": ["cretaceous"],
    "쥐라기": ["jurassic"],
    "트라이아스기": ["triassic"],
    "캄브리아": ["cambrian"],
    "고생대": ["paleozoic", "palaeozoic"],
    "중생대": ["mesozoic"],
    "신생대": ["cenozoic"],
    "빙하기": ["ice age", "glacial"],
    "표본": ["specimen"],
    "고DNA": ["ancient dna"],
    "유전자": ["gene", "genetic", "genome"],

    # ── 방법·개념 ─────────────────────────────────────
    "연대": ["dating", "age", "chronology"],
    "연대측정": ["dating"],
    "탄소연대": ["radiocarbon", "carbon-14", "c-14"],
    "방사성": ["radioactive", "radiometric"],
    "동위원소": ["isotope"],
    "반감기": ["half-life"],
    "지층": ["stratum", "strata", "layer"],
    "층서": ["stratigraph"],
    "퇴적": ["sediment"],
    "논문": ["paper", "study", "research"],
    "연구": ["study", "research"],
    "발표": ["announce", "report", "publish"],
    "증거": ["evidence"],
    "가설": ["hypothesis"],
    "이론": ["theory"],
    "실험": ["experiment"],
    "분석": ["analysis", "analyze", "analyse"],
    "복원": ["reconstruct", "restoration"],
    "보존": ["conservation", "preserve", "preservation"],
    "기원": ["origin"],

    # ★1차 실측에서 «못 찾은» 기사가 근거다 — 기억으로 넣지 않고 «세서» 넣었다
    #   A0094 Diplodocus in Spain   ← 「스페인」이 없었다
    #   A0064 ancient scrolls       ← 「두루마리」가 없었다
    #   A0082 woolly rhinos         ← 「코뿔소」가 없었다
    "두루마리": ["scroll", "papyrus", "manuscript"],
    "코뿔소": ["rhino", "rhinoceros"],
    "아미노산": ["amino acid"],
    "생물": ["life", "organism", "biolog", "creature"],
    "외계인": ["alien", "extraterrestrial"],
    "대기": ["atmosphere", "atmospheric"],
    "시료": ["sample"],
    "고리": ["ring"],
    "뒷면": ["far side"],
    "사진": ["image", "photo", "picture"],
    "거리": ["distance"],
    "단위": ["unit"],
    "해파리": ["jellyfish"],
    "악어": ["crocodile", "croc"],
    "고래": ["whale"],
    "침팬지": ["chimpanzee", "chimp"],
    "포도": ["wine", "grape", "vine"],
    "역병": ["plague", "epidemic"],
    "수도교": ["aqueduct"],
    "도로": ["road", "route"],
    "빙하": ["glacier", "glacial"],
    "화산": ["volcano", "volcanic", "eruption"],

    # 지명 — 기사 제목에 자주 나온다
    "프록시마": ["proxima"],
    "센타우리": ["centauri"],
    "스페인": ["spain", "spanish", "iberian"],
    "이탈리아": ["italy", "italian"],
    "중국": ["china", "chinese"],
    "일본": ["japan", "japanese"],
    "호주": ["australia", "australian"],
    "탄자니아": ["tanzania"],
    "레바논": ["lebanon", "lebanese"],
    "터키": ["turkey", "turkish", "anatolia"],
    "페루": ["peru", "peruvian"],
    "멕시코": ["mexico", "mexican"],
    "영국": ["britain", "british", "england", "uk"],
    "프랑스": ["france", "french"],
    "독일": ["germany", "german"],
}


def expand_query(query):
    """★«원문 질의»에서 사전 키를 찾아 영어 대응어를 낸다.

    토큰이 아니라 원문을 보는 이유:
      · "달" 같은 1글자가 토큰화에서 버려진다
      · "black hole" 같은 다중 단어 대응어는 토큰 비교로는 영영 안 맞는다
    ⇒ 한국어는 «토큰»으로, 영어 대응어는 «문자열»로 찾는다.
    """
    q = query or ""
    ens = []
    hit_keys = []
    for ko, vals in KO_EN.items():
        if ko in q:
            ens.extend(vals)
            hit_keys.append(ko)
    # 긴 키가 짧은 키를 품는 경우(고생대/고DNA 등)는 그대로 둔다 — 둘 다 단서다
    return sorted(set(ens)), hit_keys


def unmapped(tokens, hit_keys=()):
    """★사전에 «없는» 한국어 토큰을 낸다 — 사전의 구멍을 «세려고».

    범위를 기억으로 정하지 않는다(§F-8-D). 셀 일이 생기면 «센다».
    """
    miss = []
    for t in tokens:
        if any(c.isascii() for c in t):
            continue
        if any(k in t or t in k for k in hit_keys):
            continue
        miss.append(t)
    return miss
