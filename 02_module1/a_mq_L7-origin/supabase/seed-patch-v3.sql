-- ⚠️ 2026-07-24: 이 테이블들은 이후 접두사로 개명됨(a_mq_origin_* / c_lab_todo_* / d_hw_atlas_*).
-- 아래는 초기 세팅 SQL(옛 이름 기록). 현재 스키마 정본 = 라이브 DB(kdt_works). 재실행 시 개명 반영 필요.

-- ORIGIN v3 — 콘텐츠 보강 패치 (작품 +7 · 칼럼 +2)
-- 라이브 DB에 '추가만' 한다(기존 데이터·무드보드 보존, truncate 없음).
-- SQL Editor에 그대로 붙여 실행. 이미 실행했다면 재실행 금지(중복 id 충돌).

-- ── 보강 작품 (id 22~28) ────────────────────────────────
insert into works (id, movement_id, title, title_en, creator, year, image_url, source_url, description, description_en, lineage_note, lineage_en)
select v.id, m.id, v.title, v.title_en, v.creator, v.year, v.image_url, v.source_url, v.description, v.description_en, v.lineage_note, v.lineage_en
from (values
(22,'constructivism', $o$구축가 (자화상)$o$, $o$The Constructor (Self-Portrait)$o$, '엘 리시츠키','1924',
 'https://upload.wikimedia.org/wikipedia/commons/3/30/El_Lissitzky_The_Constructor%2C_self-portrait%2C_gelatin_silver_print%2C_107%C3%97118_mm%2C_1924_London%2C_Victoria_and_Albert_Museum%2C_Inv._PH142-1985.jpg',
 'https://en.wikipedia.org/wiki/El_Lissitzky',
 $o$컴퍼스를 쥔 손바닥에 눈이 겹쳐진 다중노출 포토몽타주 자화상. 예술가를 '엔지니어=구축가(constructor)'로 재정의했다.$o$,
 $o$A multiple-exposure photomontage self-portrait, an eye superimposed on a hand gripping a compass. It redefined the artist as engineer — as constructor.$o$,
 $o$사진·기하·타이포를 한 판에 합성하는 포토몽타주 문법은 오늘의 콜라주·광고 키비주얼·모션 그래픽의 뿌리다.$o$,
 $o$The photomontage grammar of fusing photograph, geometry, and type on one plane is the root of today's collage, ad key visuals, and motion graphics.$o$),
(23,'constructivism', $o$절대주의$o$, $o$Suprematism$o$, '카지미르 말레비치','1915',
 'https://upload.wikimedia.org/wikipedia/commons/5/53/Suprematism_by_Malevich_%281915%2C_GRM%29.jpg',
 'https://en.wikipedia.org/wiki/Suprematism',
 $o$흰 공간에 색색의 기하 도형이 무중력처럼 떠 있는 회화. 재현을 버리고 '순수한 감각의 우위'만 남겼다.$o$,
 $o$Colored geometric shapes float weightlessly in white space. Representation discarded, leaving only the "supremacy" of pure feeling.$o$,
 $o$도형을 배경에서 해방시킨 이 부유 감각은 오늘의 추상 레이아웃·플로팅 UI·기하 브랜딩의 원천이다.$o$,
 $o$Liberating shapes from the ground — this floating sense — is a source of today's abstract layouts, floating UI, and geometric branding.$o$),
(24,'de-stijl', $o$카운터-구성 VIII$o$, $o$Counter-Composition VIII$o$, '테오 판 두스뷔르흐','1924',
 'https://upload.wikimedia.org/wikipedia/commons/9/99/Theo_van_Doesburg_Counter-composition_VIII_2.jpg',
 'https://en.wikipedia.org/wiki/Theo_van_Doesburg',
 $o$몬드리안의 수직·수평을 45도로 기울여 긴장을 준 회화. 데 스틸 내부의 노선 논쟁을 낳은 급진적 변주다.$o$,
 $o$A painting that tilts Mondrian's verticals and horizontals to 45°, introducing tension — a radical variation that split De Stijl doctrine.$o$,
 $o$격자를 의도적으로 기울여 역동을 만드는 감각은 오늘의 다이내믹 레이아웃·대각선 그리드 디자인으로 이어진다.$o$,
 $o$Deliberately tilting the grid to create dynamism carries into today's dynamic layouts and diagonal-grid design.$o$),
(25,'arts-crafts', $o$공작과 용$o$, $o$Peacock and Dragon$o$, '윌리엄 모리스','1878',
 'https://upload.wikimedia.org/wikipedia/commons/7/7b/Morris_Peacock_and_Dragon_Fabric.jpg',
 'https://en.wikipedia.org/wiki/Peacock_and_Dragon',
 $o$공작과 용이 좌우 대칭으로 마주 선 대형 모직 직물. 중세 문양과 자연 관찰을 결합한 모리스 텍스타일의 정점이다.$o$,
 $o$A large woolen textile of peacocks and dragons in mirror symmetry. A peak of Morris's textiles, fusing medieval motif with observation of nature.$o$,
 $o$좌우 대칭과 반복 모티프로 벽면을 채우는 이 방식은 오늘의 서피스 패턴·배경 시스템의 조상이다.$o$,
 $o$Filling a surface with mirror-symmetry and repeated motif is the ancestor of today's surface patterns and background systems.$o$),
(26,'art-deco', $o$가디언 빌딩 로비$o$, $o$Guardian Building Lobby$o$, '워트 C. 롤런드','1929',
 'https://upload.wikimedia.org/wikipedia/commons/8/8e/Lobby%2C_Guardian_Building%2C_Griswold_Street%2C_Detroit%2C_MI.jpg',
 'https://en.wikipedia.org/wiki/Guardian_Building',
 $o$디트로이트의 '상업의 대성당'. 아즈텍 문양·타일·대리석을 기하학적으로 짜 넣은 아르데코 실내의 정점이다.$o$,
 $o$Detroit's "Cathedral of Finance." A peak of Art Deco interiors, weaving Aztec motifs, tile, and marble into geometric order.$o$,
 $o$재료·색·기하 장식을 공간 전체의 브랜드 경험으로 설계하는 방식은 오늘의 공간·리테일 브랜딩으로 이어진다.$o$,
 $o$Designing material, color, and ornament into a total spatial brand experience leads to today's spatial and retail branding.$o$),
(27,'art-deco', $o$이스턴 컬럼비아 빌딩$o$, $o$Eastern Columbia Building$o$, '클로드 빌먼','1930',
 'https://upload.wikimedia.org/wikipedia/commons/4/46/LA_Eastern_Columbia_Building.jpg',
 'https://en.wikipedia.org/wiki/Eastern_Columbia_Building',
 $o$청록색 테라코타와 금빛 디테일, 거대한 시계탑으로 유명한 LA의 아르데코 마천루. 색과 수직선으로 럭셔리를 연출했다.$o$,
 $o$A Los Angeles Art Deco tower famed for turquoise terracotta, gold detail, and a great clock tower. It staged luxury through color and vertical line.$o$,
 $o$강한 색·금속·수직 리듬으로 정체성을 만드는 감각은 오늘의 컬러 브랜딩과 아이코닉 파사드 디자인으로 이어진다.$o$,
 $o$Building identity from bold color, metal, and vertical rhythm carries into today's color branding and iconic-façade design.$o$),
(28,'swiss-style', $o$위니베르스$o$, $o$Univers$o$, '아드리안 프루티거','1957',
 'https://upload.wikimedia.org/wikipedia/commons/d/d3/Univers_Specimen.svg',
 'https://en.wikipedia.org/wiki/Univers',
 $o$21종의 굵기·너비를 좌표 번호(55, 65…)로 체계화한 산세리프 활자 가족. 서체를 하나의 '시스템'으로 설계한 첫 사례다.$o$,
 $o$A sans-serif family that systematized 21 weights and widths with coordinate numbers (55, 65…). The first typeface designed as a system.$o$,
 $o$하나의 형태를 굵기·너비의 좌표계로 확장하는 발상은 오늘의 가변폰트·디자인 토큰·타입 스케일의 직접 조상이다.$o$,
 $o$Extending one form across a coordinate system of weight and width is the direct ancestor of today's variable fonts, design tokens, and type scales.$o$)
) as v(id, mslug, title, title_en, creator, year, image_url, source_url, description, description_en, lineage_note, lineage_en)
join movements m on m.slug = v.mslug;

select setval(pg_get_serial_sequence('works','id'), (select max(id) from works));

-- ── 보강 칼럼 (구성주의 · 데 스틸) ──────────────────────
insert into essays (slug, title_ko, title_en, dek_ko, dek_en, hero_url, movement_slug, featured, sort, body_ko, body_en) values
('art-as-weapon',
 $o$예술이 무기가 되었을 때$o$, $o$When Art Became a Weapon$o$,
 $o$혁명기 러시아에서, 추상 도형은 장식이 아니라 메시지를 쏘는 무기였다.$o$,
 $o$In revolutionary Russia, abstract shapes were not ornament but weapons that fired a message.$o$,
 'https://upload.wikimedia.org/wikipedia/commons/f/fd/Klinom_Krasnym_Bej_Belych.JPG',
 'constructivism', false, 5,
 $o$1915년의 러시아. 말레비치는 흰 캔버스 위에 검은 사각형 하나를 올렸다. 재현의 영점(zero) — 그림이 더 이상 무언가를 '닮을' 필요가 없다는 선언이었다.

[[work:17]]

같은 손에서 색색의 도형이 무중력처럼 떠올랐다. 절대주의(Suprematism)는 순수한 감각의 우위를 말했다. 배경에서 해방된 도형, 이것이 곧 추상 레이아웃의 시작이다.

[[work:23]]

혁명이 터지자 이 추상은 거리로 나갔다. 리시츠키의 붉은 쐐기는 흰 원을 관통하며 정치 메시지를 도형만으로 전달했다.

[[work:16]]

그리고 리시츠키는 예술가 자신을 다시 정의했다. 컴퍼스를 쥔 손과 눈을 겹친 자화상 — 예술가는 이제 '구축가(constructor)', 새 세계를 설계하는 엔지니어였다.

[[work:22]]

구성주의는 예술을 미술관에서 끌어내 도구로 만들었다. 도형·대각선·색으로 메시지를 설계한다는 이 발상이, 오늘의 인포그래픽·브랜드 그래픽·모션의 뿌리다.$o$,
 $o$Russia, 1915. Malevich placed a single black square on a white canvas. The zero of representation — a declaration that a picture no longer needed to resemble anything.

[[work:17]]

From the same hand, colored shapes rose weightlessly. Suprematism spoke of the supremacy of pure feeling. Shapes freed from the ground — this is where abstract layout begins.

[[work:23]]

When revolution broke out, this abstraction went to the street. Lissitzky's red wedge pierced a white circle, carrying a political message through shape alone.

[[work:16]]

And Lissitzky redefined the artist himself. A self-portrait overlaying an eye and a hand holding a compass — the artist was now a constructor, an engineer designing a new world.

[[work:22]]

Constructivism pulled art out of the museum and made it a tool. Designing a message with shape, diagonal, and color — that idea is the root of today's infographics, brand graphics, and motion.$o$),
('order-is-beauty',
 $o$질서가 곧 아름다움이라는 믿음$o$, $o$The Faith That Order Is Beauty$o$,
 $o$수직·수평과 삼원색만 남기고, 데 스틸은 보편의 아름다움을 좇았다.$o$,
 $o$Keeping only verticals, horizontals, and three primaries, De Stijl chased a universal beauty.$o$,
 'https://upload.wikimedia.org/wikipedia/commons/0/09/Gerrit_thomas_rietveld%2C_red-blue_chair%2C_1946-56_ca.jpg',
 'de-stijl', false, 6,
 $o$1917년 네덜란드. 전쟁의 한복판에서 한 무리의 예술가들은 정반대의 것을 꿈꿨다 — 완벽한 질서. 그들은 세계를 수직선, 수평선, 그리고 삼원색으로 환원했다.

몬드리안의 화면이 그 선언이었다. 검은 격자와 빨강·파랑·노랑만으로 이룬 균형. 질서 그 자체가 곧 아름다움이라는 믿음.

[[work:9]]

릿펠트는 그 회화를 3차원으로 옮겼다. 각목과 판재의 교차만으로, 2차원의 원리가 앉을 수 있는 사물이 되었다.

[[work:10]]

그러나 모두가 직선에 만족한 것은 아니다. 판 두스뷔르흐는 격자를 45도로 기울여 긴장을 넣었고, 이 급진적 변주는 데 스틸을 둘로 갈랐다.

[[work:24]]

데 스틸은 오래가지 못했다. 그러나 그리드와 제한된 팔레트, 그리고 매체를 넘어 원리를 확장한다는 그들의 사고는 오늘의 디자인 시스템 그 자체다.$o$,
 $o$The Netherlands, 1917. In the middle of a war, a group of artists dreamed of the opposite — perfect order. They reduced the world to verticals, horizontals, and the three primaries.

Mondrian's canvas was that declaration. A balance made of black grid and red, blue, yellow alone. The faith that order itself is beauty.

[[work:9]]

Rietveld moved that painting into three dimensions. With nothing but crossing battens and planes, a two-dimensional principle became an object you could sit in.

[[work:10]]

But not everyone was content with the straight line. Van Doesburg tilted the grid to 45°, injecting tension — a radical variation that split De Stijl in two.

[[work:24]]

De Stijl did not last long. Yet the grid, the limited palette, and their idea of extending a principle across media are the very definition of today's design system.$o$);
