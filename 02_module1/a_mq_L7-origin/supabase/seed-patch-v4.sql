-- ⚠️ 2026-07-24: 이 테이블들은 이후 접두사로 개명됨(a_mq_origin_* / c_lab_todo_* / d_hw_atlas_*).
-- 아래는 초기 세팅 SQL(옛 이름 기록). 현재 스키마 정본 = 라이브 DB(kdt_works). 재실행 시 개명 반영 필요.

-- ORIGIN v4 — 영향력 큰 사조 심화 (바우하우스 +4 · 미술공예 +2)
-- 라이브 DB에 '추가만' 한다(truncate 없음). SQL Editor에 붙여 실행.
-- 이미 실행했다면 재실행 금지(중복 id 충돌).

insert into works (id, movement_id, title, title_en, creator, year, image_url, source_url, description, description_en, lineage_note, lineage_en)
select v.id, m.id, v.title, v.title_en, v.creator, v.year, v.image_url, v.source_url, v.description, v.description_en, v.lineage_note, v.lineage_en
from (values
(29,'bauhaus', $o$데사우 바우하우스 교사$o$, $o$Bauhaus Dessau Building$o$, '발터 그로피우스','1925–1926',
 'https://upload.wikimedia.org/wikipedia/commons/6/6e/Bauhaus_Dessau_2018.jpg',
 'https://en.wikipedia.org/wiki/Bauhaus_Dessau',
 $o$그로피우스가 설계한 바우하우스의 상징 교사. 유리 커튼월·비대칭 배치·기능별 동(棟) 구성으로 '형태는 기능을 따른다'를 건물 그 자체로 구현했다.$o$,
 $o$The Bauhaus's emblematic school, designed by Gropius. Glass curtain walls, asymmetric planning, and function-zoned wings embodied "form follows function" in the building itself.$o$,
 $o$유리·기능·비대칭이라는 이 어휘는 20세기 모더니즘 건축과 오늘의 미니멀 오피스·인터페이스 미감의 원형이다.$o$,
 $o$This vocabulary of glass, function, and asymmetry is the archetype of modernist architecture and today's minimal office and interface aesthetics.$o$),
(30,'bauhaus', $o$구성 (헷 오버지흐트를 위한)$o$, $o$Composition (for Het Overzicht)$o$, '라슬로 모호이-너지','약 1922',
 'https://upload.wikimedia.org/wikipedia/commons/5/53/L%C3%A1szl%C3%B3_Moholy-Nagy_Composition_for_Het_Overzicht.jpg',
 'https://en.wikipedia.org/wiki/L%C3%A1szl%C3%B3_Moholy-Nagy',
 $o$사진·타이포·기하 추상을 넘나든 다재다능한 바우하우스 교수의 회화. 투명한 면과 선의 겹침으로 빛과 공간을 조형했다.$o$,
 $o$A painting by the polymath Bauhaus professor who ranged across photography, typography, and geometric abstraction. Overlapping transparent planes and lines shape light and space.$o$,
 $o$빛·투명·레이어를 조형 요소로 다루는 감각은 오늘의 모션그래픽·글래스모피즘·레이어드 UI로 이어진다.$o$,
 $o$Treating light, transparency, and layering as formal elements carries into today's motion graphics, glassmorphism, and layered UI.$o$),
(31,'bauhaus', $o$바우하우스 계단$o$, $o$Bauhaus Stairway$o$, '오스카어 슐레머','1932',
 'https://upload.wikimedia.org/wikipedia/commons/4/48/Oskar_Schlemmer_-_Bauhaustreppe_1932.jpg',
 'https://en.wikipedia.org/wiki/Oskar_Schlemmer',
 $o$데사우 교사의 계단을 오르는 학생들을 기하학적 인물로 그린 회화. 폐교 직전, 바우하우스 공동체의 낙관을 담은 상징적 이미지다.$o$,
 $o$Students climbing the Dessau building's staircase, rendered as geometric figures. Painted near the school's closure, it holds the optimism of the Bauhaus community.$o$,
 $o$인체를 기하로 단순화해 공간에 배치하는 이 감각은 오늘의 픽토그램·아이소메트릭 일러스트·모션 캐릭터로 이어진다.$o$,
 $o$Simplifying the body into geometry and placing it in space carries into today's pictograms, isometric illustration, and motion characters.$o$),
(32,'bauhaus', $o$바겐펠트 테이블 램프 (WG24)$o$, $o$Wagenfeld Table Lamp (WG24)$o$, '빌헬름 바겐펠트 · 칼 야콥 유커','1924',
 'https://upload.wikimedia.org/wikipedia/commons/1/12/Tischlampe_di_Carl_Jakob_Jucker_%28left%2C_1923-24%29_e_di_Wilhelm_Wagenfeld_%28right%2C_1924%29_%28cropped%29.JPG',
 'https://en.wikipedia.org/wiki/WG24',
 $o$유리 기둥·금속 원반·반투명 갓만으로 이룬 테이블 램프. 장식을 완전히 걷어내고 재료와 기능만 남긴 바우하우스 제품 디자인의 아이콘이다.$o$,
 $o$A table lamp of nothing but a glass stem, a metal disc, and a translucent shade. Stripped of all ornament, an icon of Bauhaus product design — material and function alone.$o$,
 $o$재료의 정직함과 기하 최소 형태라는 원칙은 오늘의 가전·조명·프로덕트 디자인이 여전히 따르는 규범이다.$o$,
 $o$The principle of honest material and minimal geometric form is a rule today's appliances, lighting, and product design still follow.$o$),
(33,'arts-crafts', $o$하이백 체어$o$, $o$High-Backed Chair$o$, '찰스 레니 매킨토시','1903',
 'https://upload.wikimedia.org/wikipedia/commons/d/d3/High-backed_chair_by_Charles_Rennie_Mackintosh%2C_V%26A_London.jpg',
 'https://en.wikipedia.org/wiki/Charles_Rennie_Mackintosh',
 $o$등받이를 극단적으로 높인 글래스고 스타일의 의자. 아르누보의 곡선을 수직 격자로 정제해, 미술공예운동과 모더니즘을 잇는 다리가 됐다.$o$,
 $o$A Glasgow Style chair with an extremely tall back. Refining Art Nouveau's curves into a vertical lattice, it bridged the Arts & Crafts movement and modernism.$o$,
 $o$기능을 넘어 공간의 분위기를 설계하는 이 태도는 오늘의 시그니처 가구·공간 브랜딩·아이코닉 프로덕트로 이어진다.$o$,
 $o$Designing atmosphere beyond mere function carries into today's signature furniture, spatial branding, and iconic products.$o$),
(34,'arts-crafts', $o$드레서 티팟$o$, $o$Dresser Teapot$o$, '크리스토퍼 드레서','1879',
 'https://upload.wikimedia.org/wikipedia/commons/f/f1/Christopher_Dresser_-_Teapot_-_1879.jpg',
 'https://en.wikipedia.org/wiki/Christopher_Dresser',
 $o$각진 기하 형태와 노출된 리벳으로 만든 은도금 티팟. 장식을 버리고 기능·기하·대량생산을 앞세운, '최초의 산업 디자이너'의 대표작이다.$o$,
 $o$An electroplated teapot of angular geometry and exposed rivets. Discarding ornament for function, geometry, and mass production — a signature work by "the first industrial designer."$o$,
 $o$바우하우스보다 40년 앞서 기능·기하·양산을 제시한 이 사물은 오늘의 산업·프로덕트 디자인의 진짜 조상이다.$o$,
 $o$Proposing function, geometry, and mass production forty years before the Bauhaus, this object is the true ancestor of today's industrial and product design.$o$)
) as v(id, mslug, title, title_en, creator, year, image_url, source_url, description, description_en, lineage_note, lineage_en)
join movements m on m.slug = v.mslug;

select setval(pg_get_serial_sequence('works','id'), (select max(id) from works));
