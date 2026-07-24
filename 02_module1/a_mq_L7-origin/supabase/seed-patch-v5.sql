-- ⚠️ 2026-07-24: 이 테이블들은 이후 접두사로 개명됨(a_mq_origin_* / c_lab_todo_* / d_hw_atlas_*).
-- 아래는 초기 세팅 SQL(옛 이름 기록). 현재 스키마 정본 = 라이브 DB(kdt_works). 재실행 시 개명 반영 필요.

-- ORIGIN v5 — 아르누보·기하 타이포 심화 (비어즐리 · 푸투라 · 치홀트)
-- 라이브 DB에 '추가만'. SQL Editor에 붙여 실행. 재실행 금지(중복 id).
-- 후보 중 바이어 유니버설/알버스/뮐러-브로크만은 저작권 미해제 → 제외.

insert into works (id, movement_id, title, title_en, creator, year, image_url, source_url, description, description_en, lineage_note, lineage_en)
select v.id, m.id, v.title, v.title_en, v.creator, v.year, v.image_url, v.source_url, v.description, v.description_en, v.lineage_note, v.lineage_en
from (values
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
