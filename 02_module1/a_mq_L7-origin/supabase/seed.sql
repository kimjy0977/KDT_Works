-- ⚠️ 2026-07-24: 이 테이블들은 이후 접두사로 개명됨(a_mq_origin_* / c_lab_todo_* / d_hw_atlas_*).
-- 아래는 초기 세팅 SQL(옛 이름 기록). 현재 스키마 정본 = 라이브 DB(kdt_works). 재실행 시 개명 반영 필요.

-- ORIGIN v2 — 콘텐츠 시드 (7사조 · 37작품 · 6칼럼 · 한/영)
-- schema.sql 실행 후 SQL Editor에 붙여 실행. 문자열은 dollar-quote($o$)로 안전.
-- 작품 id는 고정(칼럼 임베드 [[work:ID]]가 참조).

truncate table board_items restart identity cascade;
truncate table essays     restart identity cascade;
truncate table works      restart identity cascade;
truncate table movements  restart identity cascade;

-- ── 사조 ────────────────────────────────────────────────
insert into movements (slug, name_ko, name_en, era_start, era_end, blurb, blurb_en, sort) values
('arts-crafts','미술공예운동','Arts & Crafts',1860,1910,
 $o$산업혁명의 대량생산에 맞서 손의 노동과 정직한 재료를 되살린 운동. 예술과 공예의 경계를 허물고 '잘 만든 일상 사물'이라는 디자인의 첫 윤리를 세웠다.$o$,
 $o$A revolt against industrial mass production that revived honest materials and the labor of the hand. It dissolved the line between art and craft and set design's first ethic: the well-made everyday object.$o$, 1),
('art-nouveau','아르누보','Art Nouveau',1890,1910,
 $o$식물 덩굴과 인체의 곡선을 건축·포스터·유리·가구까지 하나의 언어로 흘려보낸 국제 양식. 순수미술과 상업미술의 벽을 처음으로 허물었다.$o$,
 $o$An international style that let the curves of plants and the human body flow through architecture, posters, glass, and furniture as one language. It was the first to break the wall between fine and commercial art.$o$, 2),
('de-stijl','데 스틸','De Stijl',1917,1931,
 $o$수직·수평선과 삼원색만으로 세계를 환원한 네덜란드 운동. 회화에서 시작해 가구·건축까지 '보편적 질서'를 향한 추상의 극단.$o$,
 $o$A Dutch movement that reduced the world to verticals, horizontals, and the three primaries. Beginning in painting and reaching furniture and architecture — abstraction pushed toward a universal order.$o$, 3),
('bauhaus','바우하우스','Bauhaus',1919,1933,
 $o$형태는 기능을 따른다를 교육으로 제도화한 독일 조형학교. 예술·공예·산업을 통합해 오늘의 디자인 교육과 모던 프로덕트의 원형을 만들었다.$o$,
 $o$A German school that turned "form follows function" into a curriculum. By fusing art, craft, and industry it created the template for modern design education and the modern product.$o$, 4),
('constructivism','구성주의 · 절대주의','Constructivism & Suprematism',1915,1930,
 $o$러시아 혁명기의 급진 추상. 대각선·기하·붉은색으로 '메시지를 전달하는 도구로서의 예술'을 선언하며 그래픽 디자인의 힘을 증명했다.$o$,
 $o$Radical abstraction of the Russian revolutionary era. With diagonals, geometry, and red it declared art as a tool for delivering a message — and proved the power of graphic design.$o$, 5),
('art-deco','아르데코','Art Deco',1920,1939,
 $o$재즈 시대의 기하학적 화려함. 지그재그·유선형·금속광택으로 근대의 속도와 럭셔리를 표현하며 건축·그래픽·산업을 관통했다.$o$,
 $o$The geometric glamour of the Jazz Age. Zigzags, streamlines, and metallic sheen expressed modern speed and luxury across architecture, graphics, and industry.$o$, 6),
('swiss-style','스위스 스타일','International Typographic Style',1950,1970,
 $o$그리드·산세리프·비대칭 여백으로 정보의 객관적 전달을 추구한 타이포그래피. 오늘의 UI·웹·브랜딩 시스템 문법을 그대로 확립했다.$o$,
 $o$Typography built on the grid, sans-serifs, and asymmetric whitespace in pursuit of objective information. It set the very grammar of today's UI, web, and branding systems.$o$, 7);

-- ── 원류 작품 (id 고정) ──────────────────────────────────
insert into works (id, movement_id, title, title_en, creator, year, image_url, source_url, description, description_en, lineage_note, lineage_en)
select v.id, m.id, v.title, v.title_en, v.creator, v.year, v.image_url, v.source_url, v.description, v.description_en, v.lineage_note, v.lineage_en
from (values
(1,'arts-crafts', $o$딸기 도둑$o$, $o$Strawberry Thief$o$, '윌리엄 모리스','1883',
 'https://upload.wikimedia.org/wikipedia/commons/1/15/Strawberrythief.jpg',
 'https://en.wikipedia.org/wiki/Strawberry_Thief',
 $o$텃밭의 지빠귀가 딸기를 훔치는 장면을 인디고 방염 날염으로 촘촘히 짠 직물 패턴. 모리스가 자연 관찰과 중세 장인 기술을 결합한 대표작이다.$o$,
 $o$A densely woven indigo-discharge textile of thrushes stealing strawberries from the garden. Morris's signature work, fusing close observation of nature with medieval craft technique.$o$,
 $o$반복 패턴(리피트)과 자연에서 온 정직한 모티프라는 감각은 오늘의 텍스타일·배경 패턴·서피스 디자인의 원형이다.$o$,
 $o$Its repeat pattern and honest motif drawn from nature are the ancestor of today's textiles, background patterns, and surface design.$o$),
(2,'arts-crafts', $o$켈름스콧 프레스 콜로폰$o$, $o$Kelmscott Press Colophon$o$, '윌리엄 모리스 · 켈름스콧 프레스','1891–1898',
 'https://upload.wikimedia.org/wikipedia/commons/0/0c/KelmscottPressColophone.jpg',
 'https://en.wikipedia.org/wiki/Kelmscott_Press',
 $o$모리스가 세운 사설 출판사. 활자·여백·장식 테두리·종이까지 책 전체를 하나의 디자인으로 설계했다.$o$,
 $o$The private press Morris founded, where type, margins, ornamental borders, and paper were all designed as one whole.$o$,
 $o$책을 통째로 디자인한다는 발상은 북디자인·타이포그래피·에디토리얼 그리드의 직접 조상이다.$o$,
 $o$Designing a book as a total object is the direct forebear of book design, typography, and the editorial grid.$o$),
(3,'arts-crafts', $o$레드 하우스$o$, $o$Red House$o$, '필립 웹 · 윌리엄 모리스','1859–1860',
 'https://upload.wikimedia.org/wikipedia/commons/8/8f/Philip_Webb%27s_Red_House_in_Upton.jpg',
 'https://en.wikipedia.org/wiki/Red_House,_Bexleyheath',
 $o$모리스의 신혼집으로 지어진 주택. 겉치레 양식 대신 재료·구조·생활 동선을 정직하게 드러내 미술공예운동의 출발점이 됐다.$o$,
 $o$Built as Morris's newlywed home; instead of applied style it honestly revealed material, structure, and the flow of living — the starting point of the Arts & Crafts movement.$o$,
 $o$형태는 삶을 따른다는 태도는 기능주의 건축과 현대 프로덕트 디자인 사고의 씨앗이다.$o$,
 $o$The stance that form follows life is the seed of functionalist architecture and modern product thinking.$o$),
(4,'art-nouveau', $o$물랭 루주: 라 굴뤼$o$, $o$Moulin Rouge: La Goulue$o$, '앙리 드 툴루즈-로트레크','1891',
 'https://upload.wikimedia.org/wikipedia/commons/c/c1/Henri_de_Toulouse-Lautrec%2C_Moulin_Rouge_-_La_Goulue%2C_1891_-_The_Metropolitan_Museum_of_Art.jpg',
 'https://en.wikipedia.org/wiki/Moulin_Rouge:_La_Goulue',
 $o$몽마르트 카바레 무용수를 그린 대형 석판 포스터. 평평한 색면·과감한 실루엣·손글씨 타이포로 거리 광고를 예술로 끌어올렸다.$o$,
 $o$A large lithographic poster of a Montmartre cabaret dancer. Flat color fields, bold silhouettes, and hand-lettering raised street advertising to art.$o$,
 $o$이미지와 타이포를 한 화면에 배치하는 포스터 문법은 오늘의 광고 키비주얼·앨범 커버의 직계 조상이다.$o$,
 $o$Placing image and type in one frame — the poster grammar — is the direct ancestor of today's ad key visuals and album covers.$o$),
(5,'art-nouveau', $o$지스몽다$o$, $o$Gismonda$o$, '알폰스 무하','1894',
 'https://upload.wikimedia.org/wikipedia/commons/2/2f/Alfons_Mucha_-_1894_-_Gismonda.jpg',
 'https://commons.wikimedia.org/wiki/File:Alfons_Mucha_-_1894_-_Gismonda.jpg',
 $o$배우 사라 베르나르를 위한 세로로 긴 극장 포스터. 우아한 곡선·모자이크 후광·파스텔 톤으로 무하 스타일을 탄생시켰다.$o$,
 $o$A tall theatrical poster for the actress Sarah Bernhardt. Graceful curves, a mosaic halo, and pastel tones gave birth to the Mucha style.$o$,
 $o$인물을 감싸는 장식 프레임과 유려한 레터링은 오늘의 일러스트·패키지·타이틀 디자인에 계속 인용된다.$o$,
 $o$The ornamental frame wrapping the figure and the flowing lettering are still quoted in today's illustration, packaging, and title design.$o$),
(6,'art-nouveau', $o$키스$o$, $o$The Kiss$o$, '구스타프 클림트','1907–1908',
 'https://upload.wikimedia.org/wikipedia/commons/4/40/The_Kiss_-_Gustav_Klimt_-_Google_Cultural_Institute.jpg',
 'https://en.wikipedia.org/wiki/The_Kiss_(Klimt)',
 $o$금박과 문양으로 뒤덮인 연인. 회화의 평면 장식화를 극단까지 밀어붙인 빈 분리파의 상징이다.$o$,
 $o$Lovers wrapped in gold leaf and pattern. The symbol of the Vienna Secession, pushing painting's flat decoration to its limit.$o$,
 $o$금색·패턴·평면화의 결합은 럭셔리 브랜딩과 장식적 그래픽 감각의 원천으로 남았다.$o$,
 $o$The union of gold, pattern, and flatness remains a source for luxury branding and decorative graphic sensibility.$o$),
(7,'art-nouveau', $o$공작 테이블 램프$o$, $o$Peacock Table Lamp$o$, '티파니 스튜디오 (클라라 드리스콜)','약 1900',
 'https://upload.wikimedia.org/wikipedia/commons/c/cb/Clara_Wolcott_Driscoll_%28American%2C_1861-1944%29%2C_Tiffany_Studios_%28American%2C_1902-1932%29_-_Peacock_Table_Lamp_-_2018.281_-_Cleveland_Museum_of_Art.jpg',
 'https://en.wikipedia.org/wiki/Tiffany_lamp',
 $o$수백 조각의 스테인드글라스를 이어 붙인 조명. 빛 자체를 디자인 재료로 다룬 공예의 정점이다.$o$,
 $o$A lamp assembled from hundreds of pieces of stained glass. The peak of a craft that treated light itself as a design material.$o$,
 $o$재료의 물성과 빛을 설계에 끌어들이는 태도는 오늘의 조명·머티리얼 디자인으로 이어진다.$o$,
 $o$Drawing a material's physicality and light into the design carries into today's lighting and material design.$o$),
(8,'art-nouveau', $o$카사 바트요$o$, $o$Casa Batlló$o$, '안토니 가우디','1904–1906',
 'https://upload.wikimedia.org/wikipedia/commons/b/bf/Casa_Batllo_Overview_Barcelona_Spain_cut.jpg',
 'https://en.wikipedia.org/wiki/Casa_Batll%C3%B3',
 $o$뼈와 해양 생물을 닮은 파사드의 바르셀로나 주택. 직선을 거부한 유기적 형태의 건축이다.$o$,
 $o$A Barcelona house whose façade resembles bone and marine life. Organic architecture that refused the straight line.$o$,
 $o$자연을 구조로 번역하는 바이오모픽 디자인은 오늘의 파라메트릭·유기적 프로덕트 형태로 이어진다.$o$,
 $o$Translating nature into structure — biomorphic design — leads to today's parametric and organic product forms.$o$),
(9,'de-stijl', $o$빨강·파랑·노랑의 구성 II$o$, $o$Composition II in Red, Blue, and Yellow$o$, '피트 몬드리안','1930',
 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/Piet_Mondriaan%2C_1930_-_Mondrian_Composition_II_in_Red%2C_Blue%2C_and_Yellow.jpg/1920px-Piet_Mondriaan%2C_1930_-_Mondrian_Composition_II_in_Red%2C_Blue%2C_and_Yellow.jpg',
 'https://commons.wikimedia.org/wiki/File:Piet_Mondriaan,_1930_-_Mondrian_Composition_II_in_Red,_Blue,_and_Yellow.jpg',
 $o$검은 격자선과 삼원색 면만으로 이룬 균형. 재현을 완전히 버리고 조형의 기본 요소만 남겼다.$o$,
 $o$A balance achieved with black grid lines and the three primaries alone. Representation entirely abandoned, leaving only the basic elements of form.$o$,
 $o$그리드와 제한된 팔레트라는 이 화면은 오늘의 그리드 시스템·미니멀 UI·모듈러 디자인의 시각적 원형이다.$o$,
 $o$This canvas of grid plus limited palette is the visual archetype of today's grid systems, minimal UI, and modular design.$o$),
(10,'de-stijl', $o$빨강·파랑 의자$o$, $o$Red and Blue Chair$o$, '헤릿 릿펠트','1918/1923',
 'https://upload.wikimedia.org/wikipedia/commons/0/09/Gerrit_thomas_rietveld%2C_red-blue_chair%2C_1946-56_ca.jpg',
 'https://en.wikipedia.org/wiki/Red_and_Blue_Chair',
 $o$몬드리안의 회화를 3차원 가구로 옮긴 의자. 각목과 판재의 교차만으로 공간의 구조를 드러낸다.$o$,
 $o$A chair that moved Mondrian's painting into three dimensions. The crossing of battens and planes alone reveals the structure of space.$o$,
 $o$2D 조형 원리를 제품으로 번역한다는 시도는 디자인 시스템을 매체 너머로 확장하는 사고의 시초다.$o$,
 $o$Translating 2D formal principles into a product is the origin of extending a design system beyond one medium.$o$),
(11,'de-stijl', $o$릿펠트 슈뢰더 하우스$o$, $o$Rietveld Schröder House$o$, '헤릿 릿펠트','1924',
 'https://upload.wikimedia.org/wikipedia/commons/a/a7/Rietveld_Schr%C3%B6derhuis_HayKranen-20.JPG',
 'https://en.wikipedia.org/wiki/Rietveld_Schr%C3%B6der_House',
 $o$데 스틸 원리로 지은 유일한 주택. 이동식 벽으로 평면을 재구성하는 유연한 공간을 실현했다.$o$,
 $o$The only house built on De Stijl principles. Sliding walls reconfigure the plan into a flexible space.$o$,
 $o$가변 레이아웃·모듈 공간 개념은 오늘의 반응형·컴포넌트 기반 설계와 통한다.$o$,
 $o$The idea of variable layout and modular space speaks to today's responsive and component-based design.$o$),
(12,'bauhaus', $o$구성 8$o$, $o$Composition VIII$o$, '바실리 칸딘스키','1923',
 'https://upload.wikimedia.org/wikipedia/commons/4/47/Vassily_Kandinsky%2C_1923_-_Composition_8%2C_huile_sur_toile%2C_140_cm_x_201_cm%2C_Mus%C3%A9e_Guggenheim%2C_New_York.jpg',
 'https://commons.wikimedia.org/wiki/File:Vassily_Kandinsky,_1923_-_Composition_8,_huile_sur_toile,_140_cm_x_201_cm,_Mus%C3%A9e_Guggenheim,_New_York.jpg',
 $o$원·선·각의 기하 요소가 화면 위에서 음악처럼 긴장하는 추상화. 바우하우스에서 가르친 조형 이론의 시각적 선언이다.$o$,
 $o$An abstract painting where circles, lines, and angles tense across the surface like music. The visual manifesto of the formal theory taught at the Bauhaus.$o$,
 $o$점·선·면을 조형 문법으로 체계화한 이 사고는 모든 시각디자인 기초 교육의 토대가 됐다.$o$,
 $o$Systematizing point, line, and plane into a formal grammar became the foundation of all visual-design basic education.$o$),
(13,'bauhaus', $o$바실리 체어 (B3)$o$, $o$Wassily Chair (B3)$o$, '마르셀 브로이어','1925–1926',
 'https://upload.wikimedia.org/wikipedia/commons/1/19/Bauhaus_Chair_Breuer.png',
 'https://en.wikipedia.org/wiki/Wassily_chair',
 $o$자전거 핸들에서 착안한 강철 파이프 의자. 산업 소재를 가구에 처음 끌어들인 모던 디자인의 아이콘이다.$o$,
 $o$A tubular steel chair inspired by bicycle handlebars. The icon of modern design, the first to bring industrial material into furniture.$o$,
 $o$산업 재료·대량생산·최소 형태라는 공식은 오늘의 프로덕트 디자인이 여전히 따르는 규범이다.$o$,
 $o$The formula of industrial material, mass production, and minimal form is a rule today's product design still follows.$o$),
(14,'bauhaus', $o$바르셀로나 체어$o$, $o$Barcelona Chair$o$, '미스 반 데어 로에','1929',
 'https://upload.wikimedia.org/wikipedia/commons/5/59/Ngv_design%2C_ludwig_mies_van_der_rohe_%26_co%2C_barcelona_chair.JPG',
 'https://en.wikipedia.org/wiki/Barcelona_chair',
 $o$1929년 바르셀로나 만국박람회 독일관을 위한 의자. Less is more를 물성으로 증명한 절제의 결정체다.$o$,
 $o$A chair for the German Pavilion at the 1929 Barcelona Exposition. The crystallization of restraint that proved "less is more" in physical form.$o$,
 $o$미니멀리즘과 프리미엄 심플리시티라는 미학은 애플부터 오늘의 브랜딩까지 관통한다.$o$,
 $o$The aesthetic of minimalism and premium simplicity runs from Apple to today's branding.$o$),
(15,'bauhaus', $o$파구스 공장$o$, $o$Fagus Factory$o$, '발터 그로피우스 · 아돌프 마이어','1911–1913',
 'https://upload.wikimedia.org/wikipedia/commons/b/b3/Fagus_Gropius_Hauptgebaeude_200705_wiki_front.jpg',
 'https://en.wikipedia.org/wiki/Fagus_Factory',
 $o$유리 커튼월로 모서리를 투명하게 연 공장 건물. 바우하우스 이전에 모던 건축의 문을 연 작업이다.$o$,
 $o$A factory whose glass curtain wall opens the corners transparently. The work that opened the door to modern architecture, before the Bauhaus.$o$,
 $o$유리·격자·기능 우선의 어휘는 오늘의 오피스 건축과 미니멀 인터페이스 미감으로 이어진다.$o$,
 $o$The vocabulary of glass, grid, and function-first carries into today's office architecture and minimal-interface sensibility.$o$),
(16,'constructivism', $o$붉은 쐐기로 백군을 쳐라$o$, $o$Beat the Whites with the Red Wedge$o$, '엘 리시츠키','1919',
 'https://upload.wikimedia.org/wikipedia/commons/f/fd/Klinom_Krasnym_Bej_Belych.JPG',
 'https://en.wikipedia.org/wiki/Beat_the_Whites_with_the_Red_Wedge',
 $o$붉은 삼각형이 흰 원을 관통하는 혁명 선전 포스터. 추상 도형만으로 정치 메시지를 전달했다.$o$,
 $o$A revolutionary propaganda poster of a red triangle piercing a white circle. Abstract shapes alone carried a political message.$o$,
 $o$도형·대각선·색으로 메시지를 설계하는 방식은 오늘의 인포그래픽·모션·브랜드 그래픽의 뿌리다.$o$,
 $o$Designing a message with shape, diagonal, and color is the root of today's infographics, motion, and brand graphics.$o$),
(17,'constructivism', $o$검은 사각형$o$, $o$Black Square$o$, '카지미르 말레비치','1915',
 'https://upload.wikimedia.org/wikipedia/commons/d/dc/Kazimir_Malevich%2C_1915%2C_Black_Suprematic_Square%2C_oil_on_linen_canvas%2C_79.5_x_79.5_cm%2C_Tretyakov_Gallery%2C_Moscow.jpg',
 'https://en.wikipedia.org/wiki/Black_Square',
 $o$흰 바탕 위 검은 사각형 하나. 재현의 영점(zero)을 선언한 절대주의의 출발이다.$o$,
 $o$A single black square on a white ground. The zero of representation declared — the start of Suprematism.$o$,
 $o$형태를 극한까지 환원하는 이 급진성은 미니멀리즘·기하 추상·로고 사고의 원점이다.$o$,
 $o$This radical reduction of form to the extreme is the origin point of minimalism, geometric abstraction, and logo thinking.$o$),
(18,'art-deco', $o$크라이슬러 빌딩$o$, $o$Chrysler Building$o$, '윌리엄 밴 앨런','1928–1930',
 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/Chrysler_Building_Midtown_Manhattan_New_York_City_1932.jpg/1920px-Chrysler_Building_Midtown_Manhattan_New_York_City_1932.jpg',
 'https://commons.wikimedia.org/wiki/File:Chrysler_Building_Midtown_Manhattan_New_York_City_1932.jpg',
 $o$스테인리스 왕관과 지그재그 첨탑의 마천루. 기계 시대의 낙관과 럭셔리를 하늘에 새겼다.$o$,
 $o$A skyscraper with a stainless crown and zigzag spire. It carved the machine age's optimism and luxury into the sky.$o$,
 $o$유선형·금속광택·기하 장식의 어휘는 오늘의 럭셔리·레트로퓨처 그래픽으로 재활용된다.$o$,
 $o$The vocabulary of streamline, metallic sheen, and geometric ornament is recycled into today's luxury and retro-futurist graphics.$o$),
(19,'art-deco', $o$엠파이어 스테이트 빌딩$o$, $o$Empire State Building$o$, '슈리브·램·하먼','1930–1931',
 'https://upload.wikimedia.org/wikipedia/commons/1/10/Empire_State_Building_%28aerial_view%29.jpg',
 'https://en.wikipedia.org/wiki/Empire_State_Building',
 $o$아르데코 시대의 상징적 초고층. 수직 상승을 강조한 셋백 실루엣과 단순화된 기하 장식을 지녔다.$o$,
 $o$The emblematic high-rise of the Art Deco era, with a setback silhouette and simplified geometric ornament that stress vertical ascent.$o$,
 $o$높이와 속도를 형태로 말한다는 감각은 스카이라인 브랜딩과 아이코닉 실루엣 디자인으로 이어진다.$o$,
 $o$Speaking height and speed through form carries into skyline branding and iconic-silhouette design.$o$),
(20,'swiss-style', $o$헬베티카$o$, $o$Helvetica$o$, '막스 미딩거 · 에두아르트 호프만','1957',
 'https://upload.wikimedia.org/wikipedia/commons/2/28/HelveticaSpecimenCH.svg',
 'https://en.wikipedia.org/wiki/Helvetica',
 $o$스위스에서 태어난 산세리프 활자. 중립성과 명료함으로 20세기 후반의 표준 글자가 됐다.$o$,
 $o$A sans-serif typeface born in Switzerland. Its neutrality and clarity made it the standard letter of the late 20th century.$o$,
 $o$오늘 우리가 보는 표지판·앱·브랜드 로고 대부분이 이 중립 산세리프 계보 위에 있다.$o$,
 $o$Most of the signage, apps, and brand logos we see today sit on the lineage of this neutral sans-serif.$o$),
(21,'swiss-style', $o$악치덴츠-그로테스크$o$, $o$Akzidenz-Grotesk$o$, '베르톨트 활자주조소','1896~',
 'https://upload.wikimedia.org/wikipedia/commons/e/e1/AkzidenzGroteskspecAIB1.svg',
 'https://en.wikipedia.org/wiki/Akzidenz-Grotesk',
 $o$헬베티카에 앞서 스위스 타이포그래퍼들이 애용한 산세리프. 그리드와 결합해 국제 타이포 양식의 뼈대가 됐다.$o$,
 $o$The sans-serif Swiss typographers favored before Helvetica. Combined with the grid, it became the backbone of the International Typographic Style.$o$,
 $o$그리드·산세리프·객관적 여백이라는 이 조합이 곧 오늘의 디자인 시스템 문법이다.$o$,
 $o$The combination of grid, sans-serif, and objective whitespace is itself the grammar of today's design systems.$o$),
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
 $o$Extending one form across a coordinate system of weight and width is the direct ancestor of today's variable fonts, design tokens, and type scales.$o$),
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
 $o$Proposing function, geometry, and mass production forty years before the Bauhaus, this object is the true ancestor of today's industrial and product design.$o$),
(35,'art-nouveau', $o$절정 (살로메 삽화)$o$, $o$The Climax (from Salome)$o$, '오브리 비어즐리','1893',
 'https://upload.wikimedia.org/wikipedia/commons/3/3c/Aubrey_Beardsley_-_The_Climax.jpg',
 'https://en.wikipedia.org/wiki/Aubrey_Beardsley',
 $o$오스카 와일드의 희곡 《살로메》를 위한 흑백 펜화. 극단적 여백과 흐르는 곡선, 흑백 대비만으로 관능과 죽음을 그린 아르누보 삽화의 정점이다.$o$,
 $o$A black-and-white pen drawing for Oscar Wilde's play Salome. With extreme negative space, flowing curves, and stark contrast alone, a peak of Art Nouveau illustration.$o$,
 $o$여백·흑백 대비·유려한 선으로 분위기를 만드는 이 감각은 오늘의 그래픽노블·타투·패션 일러스트로 이어진다.$o$,
 $o$Building mood from negative space, black-white contrast, and flowing line carries into today's graphic novels, tattoo, and fashion illustration.$o$),
(36,'bauhaus', $o$푸투라$o$, $o$Futura$o$, '파울 레너','1927',
 'https://upload.wikimedia.org/wikipedia/commons/5/50/Futura_Specimen.svg',
 'https://en.wikipedia.org/wiki/Futura_(typeface)',
 $o$원·삼각형·사각형의 순수 기하로 설계한 산세리프 활자. 바우하우스의 조형 이념을 글자에 옮겨 '기하학적 산세리프'라는 계보를 열었다.$o$,
 $o$A sans-serif built from the pure geometry of circle, triangle, and square. It carried the Bauhaus's formal ideals into letters, opening the lineage of the geometric sans.$o$,
 $o$기하로 글자를 그린다는 이 발상은 오늘의 브랜드 로고·앱 타이포(퓨쳐·Poppins 계열)로 곧장 이어진다.$o$,
 $o$Drawing letters from geometry leads straight to today's brand logos and app typography (the Futura–Poppins line).$o$),
(37,'swiss-style', $o$판면 비례 (페이지 캐논)$o$, $o$Page Canon$o$, '얀 치홀트','약 1953',
 'https://upload.wikimedia.org/wikipedia/commons/0/03/Tschichold_medieval_canon.svg',
 'https://en.wikipedia.org/wiki/Canons_of_page_construction',
 $o$중세 필사본의 판면 비례를 기하 작도로 되살린 다이어그램. '신 타이포그래피'를 이끈 치홀트가 정리한, 여백과 판면의 수학적 질서다.$o$,
 $o$A diagram reconstructing the page proportions of medieval manuscripts by geometric construction. The mathematical order of margin and text block, codified by Tschichold of the New Typography.$o$,
 $o$판면과 여백을 수학적 비례로 설계한다는 이 사고가 곧 오늘의 그리드 시스템·레이아웃 그리드·타입 스케일의 뿌리다.$o$,
 $o$Designing text block and margin by mathematical proportion is the very root of today's grid systems, layout grids, and type scales.$o$)
) as v(id, mslug, title, title_en, creator, year, image_url, source_url, description, description_en, lineage_note, lineage_en)
join movements m on m.slug = v.mslug;

select setval(pg_get_serial_sequence('works','id'), (select max(id) from works));

-- ── 칼럼(에세이) — 본문의 [[work:ID]]는 작품 카드로 렌더 ──
insert into essays (slug, title_ko, title_en, dek_ko, dek_en, hero_url, movement_slug, featured, sort, body_ko, body_en) values
('when-design-began',
 $o$디자인이라는 개념은 언제 태어났나$o$, $o$When Did Design Begin?$o$,
 $o$공장 굴뚝의 시대, 윌리엄 모리스가 던진 질문에서 디자인은 시작됐다.$o$,
 $o$In the age of the factory chimney, design began with a question William Morris asked.$o$,
 'https://upload.wikimedia.org/wikipedia/commons/1/15/Strawberrythief.jpg',
 'arts-crafts', true, 1,
 $o$우리는 흔히 디자인을 화면과 로고의 일로 여긴다. 그러나 디자인이 하나의 태도로 태어난 순간은 19세기 영국, 공장 굴뚝의 시대였다.

산업혁명은 물건을 싸고 빠르게 찍어냈지만, 동시에 조악하게 만들었다. 윌리엄 모리스는 물었다. 왜 매일 쓰는 물건은 아름다우면 안 되는가.

[[work:3]]

그의 신혼집 레드 하우스는 겉치레 양식을 걷어내고 재료와 생활을 정직하게 드러냈다. 이것이 형태는 삶을 따른다는 첫 선언이었다.

모리스의 직물과 벽지는 자연을 관찰해 손으로 짠 정직한 패턴이었다. 대량생산에 맞선 이 고집이 역설적으로 디자인이라는 직업의 윤리를 세웠다.

[[work:1]]

그는 책도 하나의 사물로 설계했다. 활자·여백·종이까지. 오늘의 북디자인과 에디토리얼 그리드가 여기서 시작된다.

[[work:2]]

디자인은 새로운 기술에서 시작된 게 아니다. 잘 만든다는 것은 무엇인가라는 질문에서 시작됐다.$o$,
 $o$We tend to think of design as a matter of screens and logos. But the moment design was born as an attitude was 19th-century Britain, the age of the factory chimney.

The Industrial Revolution stamped out goods cheaply and quickly — and crudely. William Morris asked a simple question: why should the things we use every day not be beautiful?

[[work:3]]

His newlywed home, the Red House, stripped away applied style and honestly revealed material and living. This was the first declaration that form follows life.

Morris's textiles and wallpapers were honest patterns woven by hand from close observation of nature. This stubbornness against mass production paradoxically established the ethic of the profession we call design.

[[work:1]]

He designed the book as an object too — type, margins, even paper. Today's book design and editorial grid begin here.

[[work:2]]

Design did not begin with a new technology. It began with a question: what does it mean to make something well?$o$),
('bauhaus-grammar',
 $o$바우하우스: 학교가 만든 문법$o$, $o$Bauhaus: The Grammar a School Built$o$,
 $o$예술·공예·산업을 한 지붕에 둔 학교가, 오늘의 디자인 문법을 만들었다.$o$,
 $o$A school that put art, craft, and industry under one roof built the grammar of design we use today.$o$,
 'https://upload.wikimedia.org/wikipedia/commons/4/47/Vassily_Kandinsky%2C_1923_-_Composition_8%2C_huile_sur_toile%2C_140_cm_x_201_cm%2C_Mus%C3%A9e_Guggenheim%2C_New_York.jpg',
 'bauhaus', true, 2,
 $o$1919년 독일 바이마르. 한 학교가 문을 열며 예술과 공예, 그리고 산업을 한 지붕 아래 두겠다고 선언했다. 바우하우스다.

바우하우스 이전에도 그 문법의 씨앗은 있었다. 그로피우스의 파구스 공장은 유리로 벽을 열어, 건축이 기능과 구조로 말할 수 있음을 보였다.

[[work:15]]

학교는 점·선·면을 조형의 문법으로 가르쳤다. 칸딘스키의 화면은 그 이론의 시각적 선언이었다 — 형태에도 문법이 있다는.

[[work:12]]

그리고 그 문법은 의자가 되었다. 브로이어는 자전거 핸들의 강철관을 가구로 끌어와, 산업 재료와 대량생산과 최소 형태라는 공식을 만들었다.

[[work:13]]

바우하우스는 13년 만에 나치에 의해 문을 닫았다. 그러나 그 문법은 오늘의 모든 디자인 교육과 프로덕트 속에 살아 있다.$o$,
 $o$Weimar, Germany, 1919. A school opened its doors and declared it would place art, craft, and industry under one roof. The Bauhaus.

The seeds of its grammar existed even before it. Gropius's Fagus Factory opened its walls with glass, showing that architecture could speak through function and structure.

[[work:15]]

The school taught point, line, and plane as a grammar of form. Kandinsky's canvas was the visual manifesto of that theory — that form, too, has a grammar.

[[work:12]]

And that grammar became a chair. Breuer pulled the steel tube of a bicycle handlebar into furniture, forging the formula of industrial material, mass production, and minimal form.

[[work:13]]

The Bauhaus was shut by the Nazis after just thirteen years. Yet its grammar lives on inside all of today's design education and products.$o$),
('swiss-information',
 $o$스위스가 정보를 디자인한 방법$o$, $o$How Switzerland Designed Information$o$,
 $o$화려함을 버리고 그리드와 산세리프로, 스위스는 정보 자체를 디자인했다.$o$,
 $o$Discarding ornament for the grid and sans-serif, Switzerland designed information itself.$o$,
 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/Piet_Mondriaan%2C_1930_-_Mondrian_Composition_II_in_Red%2C_Blue%2C_and_Yellow.jpg/1920px-Piet_Mondriaan%2C_1930_-_Mondrian_Composition_II_in_Red%2C_Blue%2C_and_Yellow.jpg',
 'swiss-style', true, 3,
 $o$20세기 중반, 스위스의 디자이너들은 화려함을 버렸다. 그들의 목표는 단 하나 — 정보를 오해 없이 전달하는 것.

그 씨앗은 데 스틸에 있었다. 몬드리안의 격자는 화면을 수직·수평과 삼원색으로 환원했다. 질서가 곧 미(美)라는 생각.

[[work:9]]

스위스 타이포그래퍼들은 이 질서를 그리드로 제도화했다. 그리고 감정을 뺀 산세리프 — 악치덴츠 그로테스크 — 를 그 위에 올렸다.

[[work:21]]

마침내 1957년, 헬베티카가 태어났다. 중립적이고 명료한 이 글자는 20세기 후반의 표준이 되었다.

[[work:20]]

오늘 당신이 보는 지하철 표지판, 앱의 글자, 브랜드 로고 대부분이 이 스위스의 논리 위에 서 있다. 좋은 디자인은 스스로를 드러내지 않는다.$o$,
 $o$In the mid-20th century, Swiss designers threw out ornament. Their goal was singular — to deliver information without misunderstanding.

The seed lay in De Stijl. Mondrian's grid reduced the surface to verticals, horizontals, and three primaries. The idea that order itself is beauty.

[[work:9]]

Swiss typographers institutionalized this order as the grid. And onto it they set a sans-serif drained of emotion — Akzidenz-Grotesk.

[[work:21]]

Finally, in 1957, Helvetica was born. Neutral and lucid, this letter became the standard of the late 20th century.

[[work:20]]

Most of the subway signs, app text, and brand logos you see today stand on this Swiss logic. Good design does not announce itself.$o$),
('age-of-curves',
 $o$곡선의 시대, 아르누보$o$, $o$The Age of the Curve: Art Nouveau$o$,
 $o$직선이 지루하던 시대, 곡선이 순수미술과 상업미술의 벽을 허물었다.$o$,
 $o$When the straight line was boring, the curve broke the wall between fine and commercial art.$o$,
 'https://upload.wikimedia.org/wikipedia/commons/2/2f/Alfons_Mucha_-_1894_-_Gismonda.jpg',
 'art-nouveau', false, 4,
 $o$1890년대 유럽. 직선은 지루했다. 예술가들은 식물의 덩굴과 여성의 머리카락에서 새로운 언어를 찾았다 — 곡선.

툴루즈-로트레크는 그 곡선을 거리로 가져왔다. 카바레 포스터 한 장으로, 그는 상업 광고를 예술의 지위로 끌어올렸다.

[[work:4]]

무하는 곡선을 하나의 양식으로 완성했다. 인물을 감싸는 장식 프레임, 모자이크 후광, 파스텔 — 무하 스타일은 지금도 인용된다.

[[work:5]]

그리고 가우디는 그 곡선을 건물로 세웠다. 직선을 거부한 카사 바트요는 자연을 그대로 구조로 번역했다.

[[work:8]]

아르누보는 짧게 타올랐다. 그러나 순수미술과 상업미술의 벽을 처음 허문 이 시대가 없었다면, 오늘의 그래픽 디자인도 없었다.$o$,
 $o$Europe, the 1890s. The straight line was boring. Artists found a new language in the tendrils of plants and the hair of women — the curve.

Toulouse-Lautrec brought that curve to the street. With a single cabaret poster, he raised commercial advertising to the status of art.

[[work:4]]

Mucha perfected the curve into a style. The ornamental frame wrapping the figure, the mosaic halo, the pastels — the Mucha style is quoted to this day.

[[work:5]]

And Gaudí raised that curve into a building. Casa Batlló, refusing the straight line, translated nature directly into structure.

[[work:8]]

Art Nouveau burned briefly. But without this era — the first to break the wall between fine and commercial art — there would be no graphic design today.$o$),
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
