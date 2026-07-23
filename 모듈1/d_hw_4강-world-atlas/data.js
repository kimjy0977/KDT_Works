// ===== 공유 데이터·설정 (index.html · country.html 공용) =====
// ⚠️ anon/publishable(공개) 키만 프론트에. service_role(비밀) 키는 절대 금지 — 데이터는 RLS가 지킴.
const SB_URL = "https://gfpbvtcaxozcvoqfhxps.supabase.co";
const SB_KEY = "sb_publishable_rdSZJSTgLwHslFTTnnnchA_39UC1P36";   // Publishable(공개) 키 — 브라우저 안전, RLS가 데이터 보호
const sb = (window.supabase && !SB_KEY.startsWith("여기에")) ? window.supabase.createClient(SB_URL, SB_KEY) : null;

// landmark = 위키백과 문서명(ko/en) → 히어로 사진·명소 해설. fun = 재미있는 사실.
const COUNTRIES = [
  { id:1, name:"대한민국", nameEn:"South Korea", flag:"🇰🇷", heroImg:"https://upload.wikimedia.org/wikipedia/commons/2/2f/Gwanghwamun_20240413.jpg", capital:"서울", capitalEn:"Seoul", region:"아시아", population:51700000, area:100210, languages:"한국어", languagesEn:"Korean", religion:"무종교·개신교·불교·가톨릭", religionEn:"None·Protestant·Buddhist·Catholic", currency:"원 (KRW)", currencyEn:"Won (KRW)", dial:"+82", desc:"정보통신 강국이자 K-컬처의 중심. 삼면이 바다인 반도 국가.", descEn:"A tech powerhouse and the heart of K-culture — a peninsula bordered by sea on three sides.", landmark:"광화문", landmarkEn:"Gwanghwamun", heroPos:"center 42%", fun:"한글은 1443년 세종대왕이 창제해, 세계에서 유일하게 만든 사람과 반포일·원리가 기록된 문자예요.", funEn:"Hangul, created in 1443 by King Sejong, is the only writing system whose inventor, promulgation date, and design principles are all on record." },
  { id:2, name:"일본", nameEn:"Japan", flag:"🇯🇵", heroImg:"https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/View_of_Mount_Fuji_from_%C5%8Cwakudani_20211202.jpg/3840px-View_of_Mount_Fuji_from_%C5%8Cwakudani_20211202.jpg", capital:"도쿄", capitalEn:"Tokyo", region:"아시아", population:124000000, area:377975, languages:"일본어", languagesEn:"Japanese", religion:"신토·불교", religionEn:"Shinto·Buddhist", currency:"엔 (JPY)", currencyEn:"Yen (JPY)", dial:"+81", desc:"약 14,000개의 섬으로 이루어진 섬나라. 지진 대비 기술이 발달.", descEn:"An island nation of about 14,000 islands, with highly developed earthquake-preparedness technology.", landmark:"후지산", landmarkEn:"Mount Fuji", heroPos:"center 30%", fun:"환태평양 조산대에 있어 전 세계 지진의 상당수가 일본 주변에서 일어나요. 자판기 밀도도 세계 최고 수준.", funEn:"Sitting on the Pacific Ring of Fire, Japan sees a large share of the world's earthquakes — and has one of the highest vending-machine densities on Earth." },
  { id:3, name:"중국", nameEn:"China", flag:"🇨🇳", heroImg:"https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/The_Great_Wall_of_China_at_Jinshanling-edit.jpg/3840px-The_Great_Wall_of_China_at_Jinshanling-edit.jpg", capital:"베이징", capitalEn:"Beijing", region:"아시아", population:1410000000, area:9596960, languages:"중국어(표준어)", languagesEn:"Chinese (Mandarin)", religion:"무종교·불교·도교", religionEn:"None·Buddhist·Taoist", currency:"위안 (CNY)", currencyEn:"Yuan (CNY)", dial:"+86", desc:"세계에서 인구가 가장 많은 나라 중 하나이자 면적 세계 4위권.", descEn:"One of the world's most populous countries and the 4th largest by area.", landmark:"만리장성", landmarkEn:"Great Wall of China", fun:"만리장성은 이어 붙이면 2만 km가 넘지만, 흔한 오해와 달리 우주에서 맨눈으로 보이지는 않아요.", funEn:"The Great Wall stretches over 20,000 km when joined, but contrary to popular belief it can't be seen with the naked eye from space." },
  { id:4, name:"인도", nameEn:"India", flag:"🇮🇳", heroImg:"https://upload.wikimedia.org/wikipedia/commons/1/1d/Taj_Mahal_%28Edited%29.jpeg", capital:"뉴델리", capitalEn:"New Delhi", region:"아시아", population:1428000000, area:3287263, languages:"힌디어·영어 외", languagesEn:"Hindi·English & more", religion:"힌두교·이슬람교", religionEn:"Hindu·Muslim", currency:"루피 (INR)", currencyEn:"Rupee (INR)", dial:"+91", desc:"2023년 세계 인구 1위. 22개 공용어가 헌법에 등재된 다언어 국가.", descEn:"The world's most populous country as of 2023, with 22 official languages in its constitution.", landmark:"타지마할", landmarkEn:"Taj Mahal", fun:"숫자 0과 십진법 체계를 발전시킨 수학의 나라. 영화 산업(발리우드)은 연간 제작 편수 세계 최다.", funEn:"The land that developed zero and the decimal system. Its film industry (Bollywood) produces the most films per year in the world." },
  { id:5, name:"태국", nameEn:"Thailand", flag:"🇹🇭", heroImg:"https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/%E0%B9%80%E0%B8%88%E0%B8%94%E0%B8%B5%E0%B8%A2%E0%B9%8C%E0%B8%9B%E0%B8%A3%E0%B8%B0%E0%B8%98%E0%B8%B2%E0%B8%99%E0%B8%97%E0%B8%A3%E0%B8%87%E0%B8%9B%E0%B8%A3%E0%B8%B2%E0%B8%87%E0%B8%84%E0%B9%8C%E0%B8%A7%E0%B8%B1%E0%B8%94%E0%B8%AD%E0%B8%A3%E0%B8%B8%E0%B8%932.jpg/3840px-%E0%B9%80%E0%B8%88%E0%B8%94%E0%B8%B5%E0%B8%A2%E0%B9%8C%E0%B8%9B%E0%B8%A3%E0%B8%B0%E0%B8%98%E0%B8%B2%E0%B8%99%E0%B8%97%E0%B8%A3%E0%B8%87%E0%B8%9B%E0%B8%A3%E0%B8%B2%E0%B8%87%E0%B8%84%E0%B9%8C%E0%B8%A7%E0%B8%B1%E0%B8%94%E0%B8%AD%E0%B8%A3%E0%B8%B8%E0%B8%932.jpg", capital:"방콕", capitalEn:"Bangkok", region:"아시아", population:71700000, area:513120, languages:"태국어", languagesEn:"Thai", religion:"불교(상좌부)", religionEn:"Buddhist (Theravada)", currency:"바트 (THB)", currencyEn:"Baht (THB)", dial:"+66", desc:"'미소의 나라'. 동남아에서 식민 지배를 받지 않은 유일한 나라.", descEn:"The 'Land of Smiles' — the only Southeast Asian nation never colonized.", landmark:"왓 아룬", landmarkEn:"Wat Arun", fun:"수도 방콕의 정식 이름은 세계에서 가장 긴 지명이에요. '태국(Thai)'은 '자유'라는 뜻.", funEn:"Bangkok's full ceremonial name is the longest place name in the world. 'Thai' means 'free.'" },
  { id:6, name:"베트남", nameEn:"Vietnam", flag:"🇻🇳", heroImg:"https://upload.wikimedia.org/wikipedia/commons/7/79/Ha_Long_Bay_in_2019.jpg", capital:"하노이", capitalEn:"Hanoi", region:"아시아", population:98900000, area:331212, languages:"베트남어", languagesEn:"Vietnamese", religion:"무종교·불교", religionEn:"None·Buddhist", currency:"동 (VND)", currencyEn:"Dong (VND)", dial:"+84", desc:"쌀국수(퍼)와 커피로 유명. 남북으로 길게 뻗은 지형.", descEn:"Famous for pho and coffee, with a long north-south geography.", landmark:"하롱베이", landmarkEn:"Ha Long Bay", fun:"세계 2위 커피 수출국이에요. 연유를 넣은 진한 베트남 커피가 유명.", funEn:"The world's 2nd-largest coffee exporter, known for strong Vietnamese coffee served with condensed milk." },
  { id:7, name:"인도네시아", nameEn:"Indonesia", flag:"🇮🇩", heroImg:"https://upload.wikimedia.org/wikipedia/commons/thumb/2/25/Pradaksina.jpg/3840px-Pradaksina.jpg", capital:"자카르타", capitalEn:"Jakarta", region:"아시아", population:277000000, area:1904569, languages:"인도네시아어", languagesEn:"Indonesian", religion:"이슬람교", religionEn:"Muslim", currency:"루피아 (IDR)", currencyEn:"Rupiah (IDR)", dial:"+62", desc:"1만 7천여 개 섬으로 이루어진 세계 최대의 도서(섬) 국가.", descEn:"The world's largest archipelagic nation, made up of over 17,000 islands.", landmark:"보로부두르", landmarkEn:"Borobudur", fun:"1만 7천여 개 섬 중 사람이 사는 곳은 약 6천 개. 지역 언어가 700개가 넘어요.", funEn:"Of its 17,000+ islands, about 6,000 are inhabited, and it has more than 700 local languages." },
  { id:8, name:"사우디아라비아", nameEn:"Saudi Arabia", flag:"🇸🇦", heroImg:"https://upload.wikimedia.org/wikipedia/commons/thumb/8/89/The_Ka%27ba%2C_Great_Mosque_of_Mecca%2C_Saudi_Arabia_%284%29.jpg/3840px-The_Ka%27ba%2C_Great_Mosque_of_Mecca%2C_Saudi_Arabia_%284%29.jpg", capital:"리야드", capitalEn:"Riyadh", region:"아시아", population:36900000, area:2149690, languages:"아랍어", languagesEn:"Arabic", religion:"이슬람교", religionEn:"Muslim", currency:"리얄 (SAR)", currencyEn:"Riyal (SAR)", dial:"+966", desc:"이슬람 성지 메카·메디나가 있는 나라. 세계적인 산유국.", descEn:"Home to the Islamic holy cities of Mecca and Medina, and a leading oil producer.", landmark:"메카", landmarkEn:"Mecca", heroTitle:"카바", heroTitleEn:"Kaaba", fun:"국토 대부분이 사막이라 1년 내내 흐르는 강이 하나도 없는 나라예요.", funEn:"Mostly desert, it's one of the only countries with no permanent rivers at all." },
  { id:9, name:"프랑스", nameEn:"France", flag:"🇫🇷", heroImg:"https://upload.wikimedia.org/wikipedia/commons/a/a8/Tour_Eiffel_Wikimedia_Commons.jpg", capital:"파리", capitalEn:"Paris", region:"유럽", population:68000000, area:551695, languages:"프랑스어", languagesEn:"French", religion:"가톨릭·무종교", religionEn:"Catholic·None", currency:"유로 (EUR)", currencyEn:"Euro (EUR)", dial:"+33", desc:"세계에서 관광객이 가장 많이 찾는 나라. 예술과 요리의 중심.", descEn:"The world's most-visited country — a center of art and cuisine.", landmark:"에펠탑", landmarkEn:"Eiffel Tower", fun:"에펠탑은 1889년 만국박람회용 임시 구조물로, 원래 20년 뒤 철거될 예정이었어요. 관광객 세계 1위 국가.", funEn:"The Eiffel Tower was a temporary structure for the 1889 World's Fair, meant to be dismantled 20 years later. France is the #1 tourist destination." },
  { id:10, name:"독일", nameEn:"Germany", flag:"🇩🇪", heroImg:"https://upload.wikimedia.org/wikipedia/commons/a/a6/Brandenburger_Tor_abends.jpg", capital:"베를린", capitalEn:"Berlin", region:"유럽", population:84000000, area:357588, languages:"독일어", languagesEn:"German", religion:"개신교·가톨릭", religionEn:"Protestant·Catholic", currency:"유로 (EUR)", currencyEn:"Euro (EUR)", dial:"+49", desc:"유럽 최대 경제국. 자동차·기계 산업과 맥주 축제로 유명.", descEn:"Europe's largest economy, famous for its auto and machinery industries and its beer festival.", landmark:"브란덴부르크 문", landmarkEn:"Brandenburg Gate", fun:"고속도로 아우토반의 일부 구간은 공식 속도 제한이 없어요. 빵 종류가 3천 가지가 넘습니다.", funEn:"Parts of the Autobahn have no official speed limit, and Germany has over 3,000 kinds of bread." },
  { id:11, name:"영국", nameEn:"United Kingdom", flag:"🇬🇧", heroImg:"https://upload.wikimedia.org/wikipedia/commons/4/43/Elizabeth_Tower%2C_June_2022.jpg", capital:"런던", capitalEn:"London", region:"유럽", population:67000000, area:242495, languages:"영어", languagesEn:"English", religion:"개신교(성공회)·무종교", religionEn:"Protestant (Anglican)·None", currency:"파운드 (GBP)", currencyEn:"Pound (GBP)", dial:"+44", desc:"산업혁명의 발상지. 잉글랜드·스코틀랜드·웨일스·북아일랜드의 연합.", descEn:"Birthplace of the Industrial Revolution — a union of England, Scotland, Wales, and Northern Ireland.", landmark:"빅 벤", landmarkEn:"Big Ben", fun:"'빅 벤'은 사실 시계탑이 아니라 그 안에 달린 큰 종의 이름이에요. 지금도 도로 좌측통행.", funEn:"'Big Ben' is actually the name of the great bell inside the tower, not the tower itself. Traffic still drives on the left." },
  { id:12, name:"이탈리아", nameEn:"Italy", flag:"🇮🇹", heroImg:"https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/Colosseo_2020.jpg/3840px-Colosseo_2020.jpg", capital:"로마", capitalEn:"Rome", region:"유럽", population:59000000, area:301340, languages:"이탈리아어", languagesEn:"Italian", religion:"가톨릭", religionEn:"Catholic", currency:"유로 (EUR)", currencyEn:"Euro (EUR)", dial:"+39", desc:"로마 제국과 르네상스의 본고장. 파스타·피자의 나라.", descEn:"Home of the Roman Empire and the Renaissance — the land of pasta and pizza.", landmark:"콜로세움", landmarkEn:"Colosseum", fun:"유네스코 세계유산이 세계에서 가장 많은 나라 중 하나예요. 피자·파스타의 본고장.", funEn:"It has one of the highest counts of UNESCO World Heritage Sites in the world, and is the birthplace of pizza and pasta." },
  { id:13, name:"스페인", nameEn:"Spain", flag:"🇪🇸", heroImg:"https://upload.wikimedia.org/wikipedia/commons/e/ef/SF_maig_2_cropped.jpg", capital:"마드리드", capitalEn:"Madrid", region:"유럽", population:48000000, area:505990, languages:"스페인어", languagesEn:"Spanish", religion:"가톨릭", religionEn:"Catholic", currency:"유로 (EUR)", currencyEn:"Euro (EUR)", dial:"+34", desc:"플라멩코와 축구, 가우디 건축으로 유명한 이베리아 반도의 나라.", descEn:"An Iberian nation famous for flamenco, football, and Gaudí's architecture.", landmark:"사그라다 파밀리아", landmarkEn:"Sagrada Família", fun:"가우디의 사그라다 파밀리아는 1882년 착공해 140여 년째 건축 중이에요. 오후 낮잠(시에스타) 문화.", funEn:"Gaudí's Sagrada Família, begun in 1882, has been under construction for over 140 years. Spain is known for its afternoon siesta." },
  { id:14, name:"노르웨이", nameEn:"Norway", flag:"🇳🇴", heroImg:"https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Geirangerfjord_.jpg/3840px-Geirangerfjord_.jpg", capital:"오슬로", capitalEn:"Oslo", region:"유럽", population:5500000, area:385207, languages:"노르웨이어", languagesEn:"Norwegian", religion:"개신교(루터교)", religionEn:"Protestant (Lutheran)", currency:"크로네 (NOK)", currencyEn:"Krone (NOK)", dial:"+47", desc:"피오르와 백야로 유명. 삶의 질·복지 수준이 세계 최상위권.", descEn:"Famous for fjords and the midnight sun, with one of the highest qualities of life in the world.", landmark:"예이랑에르 피오르", landmarkEn:"Geirangerfjord", fun:"여름엔 해가 지지 않는 백야, 겨울엔 오로라를 볼 수 있어요. 전기차 보급률 세계 최고 수준.", funEn:"In summer the sun never sets; in winter you can see the aurora. It has one of the world's highest EV-adoption rates." },
  { id:15, name:"바티칸 시국", nameEn:"Vatican City", flag:"🇻🇦", heroImg:"https://upload.wikimedia.org/wikipedia/commons/thumb/f/f5/Basilica_di_San_Pietro_in_Vaticano_September_2015-1a.jpg/3840px-Basilica_di_San_Pietro_in_Vaticano_September_2015-1a.jpg", capital:"바티칸 시(도시국가)", capitalEn:"Vatican City (city-state)", region:"유럽", population:825, area:0.49, languages:"라틴어·이탈리아어", languagesEn:"Latin·Italian", religion:"가톨릭", religionEn:"Catholic", currency:"유로 (EUR)", currencyEn:"Euro (EUR)", dial:"+379", desc:"세계에서 가장 작은 독립국. 가톨릭 교회의 중심인 성좌.", descEn:"The world's smallest independent state and the seat of the Catholic Church.", landmark:"성 베드로 대성전", landmarkEn:"St. Peter's Basilica", fun:"세계에서 가장 작은 나라(약 0.49km²)로, 인구 대부분이 성직자예요. 자체 우체국도 있어요.", funEn:"The smallest country on Earth (about 0.49 km²), where most residents are clergy. It even has its own post office." },
  { id:16, name:"미국", nameEn:"United States", flag:"🇺🇸", heroImg:"https://upload.wikimedia.org/wikipedia/commons/8/89/Front_view_of_Statue_of_Liberty_%28cropped%29.jpg", capital:"워싱턴 D.C.", capitalEn:"Washington, D.C.", region:"북아메리카", population:335000000, area:9833517, languages:"영어(사실상)", languagesEn:"English (de facto)", religion:"개신교·가톨릭·무종교", religionEn:"Protestant·Catholic·None", currency:"달러 (USD)", currencyEn:"Dollar (USD)", dial:"+1", desc:"50개 주의 연방 국가. 세계 최대의 경제·문화 영향력.", descEn:"A federation of 50 states with the world's largest economic and cultural influence.", landmark:"자유의 여신상", landmarkEn:"Statue of Liberty", fun:"국립공원 제도를 세계 최초로 만든 나라예요(옐로스톤, 1872년). 50개 주의 연방국.", funEn:"It created the world's first national park (Yellowstone, 1872). A federation of 50 states." },
  { id:17, name:"캐나다", nameEn:"Canada", flag:"🇨🇦", heroImg:"https://upload.wikimedia.org/wikipedia/commons/a/ab/3Falls_Niagara.jpg", capital:"오타와", capitalEn:"Ottawa", region:"북아메리카", population:39000000, area:9984670, languages:"영어·프랑스어", languagesEn:"English·French", religion:"가톨릭·개신교·무종교", religionEn:"Catholic·Protestant·None", currency:"캐나다달러 (CAD)", currencyEn:"Canadian Dollar (CAD)", dial:"+1", desc:"면적 세계 2위. 광활한 자연과 다문화 사회로 유명.", descEn:"The 2nd-largest country by area, known for vast nature and a multicultural society.", landmark:"나이아가라 폭포", landmarkEn:"Niagara Falls", fun:"전 세계 호수의 절반 이상이 캐나다에 있을 만큼 호수가 많아요. 국토 면적 세계 2위.", funEn:"More than half of all the world's lakes are in Canada. It's the 2nd-largest country by land area." },
  { id:18, name:"멕시코", nameEn:"Mexico", flag:"🇲🇽", heroImg:"https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/Chichen_Itza_3.jpg/3840px-Chichen_Itza_3.jpg", capital:"멕시코시티", capitalEn:"Mexico City", region:"북아메리카", population:128000000, area:1964375, languages:"스페인어", languagesEn:"Spanish", religion:"가톨릭", religionEn:"Catholic", currency:"페소 (MXN)", currencyEn:"Peso (MXN)", dial:"+52", desc:"마야·아즈텍 문명의 후예. 타코와 활기찬 축제 문화.", descEn:"Heir to the Maya and Aztec civilizations, with tacos and vibrant festivals.", landmark:"치첸이트사", landmarkEn:"Chichen Itza", fun:"초콜릿·옥수수·토마토·고추의 원산지예요. 마야·아즈텍 문명의 후예.", funEn:"The birthplace of chocolate, corn, tomatoes, and chili peppers, and heir to the Maya and Aztec civilizations." },
  { id:19, name:"브라질", nameEn:"Brazil", flag:"🇧🇷", heroImg:"https://upload.wikimedia.org/wikipedia/commons/4/4f/Christ_the_Redeemer_-_Cristo_Redentor.jpg", capital:"브라질리아", capitalEn:"Brasília", region:"남아메리카", population:214000000, area:8515767, languages:"포르투갈어", languagesEn:"Portuguese", religion:"가톨릭·개신교", religionEn:"Catholic·Protestant", currency:"헤알 (BRL)", currencyEn:"Real (BRL)", dial:"+55", desc:"아마존 열대우림의 약 60%를 품은 남미 최대국. 축구와 삼바.", descEn:"South America's largest country, holding about 60% of the Amazon rainforest — football and samba.", landmark:"구세주 그리스도상", landmarkEn:"Christ the Redeemer (statue)", fun:"아마존 열대우림의 약 60%를 품은 나라. 축구 월드컵 최다 우승국(5회).", funEn:"It holds about 60% of the Amazon rainforest and has won the most World Cups (5)." },
  { id:20, name:"아르헨티나", nameEn:"Argentina", flag:"🇦🇷", heroImg:"https://upload.wikimedia.org/wikipedia/commons/thumb/c/c4/Iguazu_Cataratas2.jpg/3840px-Iguazu_Cataratas2.jpg", capital:"부에노스아이레스", capitalEn:"Buenos Aires", region:"남아메리카", population:46000000, area:2780400, languages:"스페인어", languagesEn:"Spanish", religion:"가톨릭", religionEn:"Catholic", currency:"페소 (ARS)", currencyEn:"Peso (ARS)", dial:"+54", desc:"탱고의 고향. 소고기와 축구, 파타고니아의 대자연.", descEn:"The home of tango — beef, football, and the vast nature of Patagonia.", landmark:"이과수 폭포", landmarkEn:"Iguazu Falls", fun:"탱고의 발상지예요. 세계에서 가장 남쪽에 있는 도시(우수아이아)가 있어요.", funEn:"The birthplace of tango, and home to the world's southernmost city (Ushuaia)." },
  { id:21, name:"페루", nameEn:"Peru", flag:"🇵🇪", heroImg:"https://upload.wikimedia.org/wikipedia/commons/thumb/b/bb/Machu_Picchu%2C_2023_%28012%29.jpg/3840px-Machu_Picchu%2C_2023_%28012%29.jpg", capital:"리마", capitalEn:"Lima", region:"남아메리카", population:34000000, area:1285216, languages:"스페인어·케추아어", languagesEn:"Spanish·Quechua", religion:"가톨릭", religionEn:"Catholic", currency:"솔 (PEN)", currencyEn:"Sol (PEN)", dial:"+51", desc:"잉카 문명의 마추픽추가 있는 나라. 안데스 산맥이 관통.", descEn:"Home to the Inca site of Machu Picchu, crossed by the Andes.", landmark:"마추픽추", landmarkEn:"Machu Picchu", fun:"잉카의 공중도시 마추픽추가 해발 2,430m에 있어요. 감자의 원산지로 품종이 수천 가지.", funEn:"The Inca sky-city Machu Picchu sits at 2,430 m. Peru is the birthplace of the potato, with thousands of varieties." },
  { id:22, name:"이집트", nameEn:"Egypt", flag:"🇪🇬", heroImg:"https://upload.wikimedia.org/wikipedia/commons/e/e7/Great_Pyramid_of_Giza_-_Pyramid_of_Khufu.jpg", capital:"카이로", capitalEn:"Cairo", region:"아프리카", population:109000000, area:1010408, languages:"아랍어", languagesEn:"Arabic", religion:"이슬람교·콥트교", religionEn:"Muslim·Coptic", currency:"파운드 (EGP)", currencyEn:"Pound (EGP)", dial:"+20", desc:"기자의 대피라미드 등 고대 문명 유산. 나일강 문명의 발상지.", descEn:"Ancient heritage like the Great Pyramids of Giza — the cradle of Nile civilization.", landmark:"기자의 대피라미드", landmarkEn:"Great Pyramid of Giza", fun:"대피라미드는 약 4,500년 전 지어져, 세계 7대 불가사의 중 유일하게 지금까지 남아 있어요.", funEn:"Built about 4,500 years ago, the Great Pyramid is the only one of the Seven Wonders of the Ancient World still standing." },
  { id:23, name:"남아프리카 공화국", nameEn:"South Africa", flag:"🇿🇦", heroImg:"https://upload.wikimedia.org/wikipedia/commons/d/dc/Table_Mountain_DanieVDM.jpg", capital:"프리토리아·케이프타운·블룸폰테인", capitalEn:"Pretoria·Cape Town·Bloemfontein", region:"아프리카", population:60000000, area:1221037, languages:"11개 공용어", languagesEn:"11 official languages", religion:"개신교·가톨릭", religionEn:"Protestant·Catholic", currency:"랜드 (ZAR)", currencyEn:"Rand (ZAR)", dial:"+27", desc:"행정·입법·사법 수도가 세 도시로 나뉜 나라. 공용어가 11개.", descEn:"A nation with three capital cities for its executive, legislative, and judicial branches, and 11 official languages.", landmark:"테이블 산", landmarkEn:"Table Mountain", fun:"행정·입법·사법 수도가 세 도시로 나뉜 유일한 나라예요. 공용어가 무려 11개.", funEn:"The only country whose executive, legislative, and judicial capitals are three different cities — with 11 official languages." },
  { id:24, name:"케냐", nameEn:"Kenya", flag:"🇰🇪", heroImg:"https://upload.wikimedia.org/wikipedia/commons/1/17/Masai_Mara_at_Sunset.jpg", capital:"나이로비", capitalEn:"Nairobi", region:"아프리카", population:55000000, area:580367, languages:"스와힐리어·영어", languagesEn:"Swahili·English", religion:"개신교·가톨릭", religionEn:"Protestant·Catholic", currency:"실링 (KES)", currencyEn:"Shilling (KES)", dial:"+254", desc:"사파리와 마사이마라 초원, 마라톤 강국으로 유명.", descEn:"Famous for safaris, the Maasai Mara plains, and marathon greatness.", landmark:"마사이마라 국립보호구", landmarkEn:"Maasai Mara", fun:"매년 수백만 마리 누 떼의 대이동이 펼쳐지는 마사이마라가 있어요. 세계적인 마라톤 강국.", funEn:"Home to the Maasai Mara, where millions of wildebeest migrate each year. A world powerhouse in marathon running." },
  { id:25, name:"호주", nameEn:"Australia", flag:"🇦🇺", heroImg:"https://upload.wikimedia.org/wikipedia/commons/a/a0/Sydney_Australia._%2821339175489%29.jpg", capital:"캔버라", capitalEn:"Canberra", region:"오세아니아", population:26000000, area:7692024, languages:"영어(사실상)", languagesEn:"English (de facto)", religion:"기독교·무종교", religionEn:"Christian·None", currency:"호주달러 (AUD)", currencyEn:"Australian Dollar (AUD)", dial:"+61", desc:"나라이자 하나의 대륙. 캥거루·코알라 등 고유종의 보고.", descEn:"A country that is also a whole continent — a haven for unique species like kangaroos and koalas.", landmark:"시드니 오페라 하우스", landmarkEn:"Sydney Opera House", fun:"나라이자 하나의 대륙이에요. 사람보다 캥거루가 더 많다고 할 정도.", funEn:"It's a country and a continent at once — said to have more kangaroos than people." },
  { id:26, name:"뉴질랜드", nameEn:"New Zealand", flag:"🇳🇿", heroImg:"https://upload.wikimedia.org/wikipedia/commons/thumb/b/b6/Milford_Sound_%28New_Zealand%29.JPG/3840px-Milford_Sound_%28New_Zealand%29.JPG", capital:"웰링턴", capitalEn:"Wellington", region:"오세아니아", population:5200000, area:268021, languages:"영어·마오리어", languagesEn:"English·Māori", religion:"기독교·무종교", religionEn:"Christian·None", currency:"뉴질랜드달러 (NZD)", currencyEn:"New Zealand Dollar (NZD)", dial:"+64", desc:"마오리 문화와 청정 자연. 『반지의 제왕』 촬영지로 유명.", descEn:"Māori culture and pristine nature — famous as the filming location for The Lord of the Rings.", landmark:"밀퍼드사운드", landmarkEn:"Milford Sound", fun:"사람보다 양이 훨씬 많은 나라예요. 『반지의 제왕』 촬영지로도 유명.", funEn:"A country with far more sheep than people, famous as the filming location for The Lord of the Rings." },
  { id:27, name:"필리핀", nameEn:"Philippines", flag:"🇵🇭", heroImg:"https://upload.wikimedia.org/wikipedia/commons/0/0f/Mount_Mayon_Cagsawa_field_view_close-up_%28Busay%2C_Daraga%2C_Albay%3B_04-21-2023%29.jpg", capital:"마닐라", capitalEn:"Manila", region:"아시아", population:117000000, area:300000, languages:"필리핀어·영어", languagesEn:"Filipino·English", religion:"가톨릭", religionEn:"Catholic", currency:"페소 (PHP)", currencyEn:"Peso (PHP)", dial:"+63", desc:"7천여 개 섬으로 이루어진 동남아 국가. 아시아 최대 가톨릭 국가.", descEn:"A Southeast Asian nation of over 7,000 islands and Asia's largest Catholic country.", landmark:"마욘 화산", landmarkEn:"Mayon Volcano", fun:"7,641개의 섬으로 이루어져 있어요. 영어를 공용어로 써 영어 사용 인구가 많습니다.", funEn:"Made up of 7,641 islands, with English as an official language and a large English-speaking population." },
  { id:28, name:"싱가포르", nameEn:"Singapore", flag:"🇸🇬", heroImg:"https://upload.wikimedia.org/wikipedia/commons/thumb/c/c7/Marina_Bay_Sands_%28I%29.jpg/3840px-Marina_Bay_Sands_%28I%29.jpg", capital:"싱가포르(도시국가)", capitalEn:"Singapore (city-state)", region:"아시아", population:5900000, area:728, languages:"영어·중국어·말레이어·타밀어", languagesEn:"English·Chinese·Malay·Tamil", religion:"불교·기독교·이슬람교", religionEn:"Buddhist·Christian·Muslim", currency:"싱가포르달러 (SGD)", currencyEn:"Singapore Dollar (SGD)", dial:"+65", desc:"도시 전체가 하나의 나라인 도시국가. 금융·물류 허브.", descEn:"A city-state where the whole city is the country — a finance and logistics hub.", landmark:"마리나 베이 샌즈", landmarkEn:"Marina Bay Sands", fun:"길거리에 껌 판매·반입이 엄격히 규제되는 것으로 유명해요. 4개 공용어를 씁니다.", funEn:"Famous for its strict rules on chewing gum. It has four official languages." },
  { id:29, name:"튀르키예", nameEn:"Türkiye", flag:"🇹🇷", heroImg:"https://upload.wikimedia.org/wikipedia/commons/4/4a/Hagia_Sophia_%28228968325%29.jpeg", capital:"앙카라", capitalEn:"Ankara", region:"아시아", population:85000000, area:783562, languages:"튀르키예어", languagesEn:"Turkish", religion:"이슬람교", religionEn:"Muslim", currency:"리라 (TRY)", currencyEn:"Lira (TRY)", dial:"+90", desc:"아시아와 유럽에 걸친 나라. 동서 문명의 교차로.", descEn:"A country straddling Asia and Europe — a crossroads of civilizations.", landmark:"아야소피아", landmarkEn:"Hagia Sophia", fun:"한 나라가 두 대륙(아시아·유럽)에 걸쳐 있어요. 이스탄불은 두 대륙에 도시가 나뉘어 있습니다.", funEn:"A single country spanning two continents — Istanbul itself sits on both Asia and Europe." },
  { id:30, name:"아랍에미리트", nameEn:"United Arab Emirates", flag:"🇦🇪", heroImg:"https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Burj_Khalifa_%28worlds_tallest_building%29_and_the_Dubai_skyline_%2825781049892%29.jpg/3840px-Burj_Khalifa_%28worlds_tallest_building%29_and_the_Dubai_skyline_%2825781049892%29.jpg", capital:"아부다비", capitalEn:"Abu Dhabi", region:"아시아", population:9400000, area:83600, languages:"아랍어", languagesEn:"Arabic", religion:"이슬람교", religionEn:"Muslim", currency:"디르함 (AED)", currencyEn:"Dirham (AED)", dial:"+971", desc:"7개 토후국의 연합. 사막 위에 세운 초현대 도시로 유명.", descEn:"A federation of seven emirates, famous for ultramodern cities built on the desert.", landmark:"부르즈 할리파", landmarkEn:"Burj Khalifa", fun:"세계에서 가장 높은 건물 부르즈 할리파(828m)가 두바이에 있어요.", funEn:"The world's tallest building, the Burj Khalifa (828 m), stands in Dubai." },
  { id:31, name:"네덜란드", nameEn:"Netherlands", flag:"🇳🇱", heroImg:"https://upload.wikimedia.org/wikipedia/commons/f/ff/KinderdijkMolens02.jpg", capital:"암스테르담", capitalEn:"Amsterdam", region:"유럽", population:17800000, area:41850, languages:"네덜란드어", languagesEn:"Dutch", religion:"무종교·가톨릭·개신교", religionEn:"None·Catholic·Protestant", currency:"유로 (EUR)", currencyEn:"Euro (EUR)", dial:"+31", desc:"국토의 상당 부분이 해수면보다 낮은 나라. 운하·풍차·자전거로 유명.", descEn:"A country where much of the land lies below sea level — famous for canals, windmills, and bikes.", landmark:"킨더다이크", landmarkEn:"Kinderdijk", fun:"국토의 약 4분의 1이 해수면보다 낮아 둑과 간척으로 땅을 지켜요. 자전거가 인구보다 많습니다.", funEn:"About a quarter of the land is below sea level, kept dry by dikes. There are more bikes than people." },
  { id:32, name:"스위스", nameEn:"Switzerland", flag:"🇨🇭", heroImg:"https://upload.wikimedia.org/wikipedia/commons/6/60/Matterhorn_from_Domh%C3%BCtte_-_2.jpg", capital:"베른", capitalEn:"Bern", region:"유럽", population:8800000, area:41285, languages:"독일어·프랑스어·이탈리아어", languagesEn:"German·French·Italian", religion:"가톨릭·개신교", religionEn:"Catholic·Protestant", currency:"스위스프랑 (CHF)", currencyEn:"Swiss Franc (CHF)", dial:"+41", desc:"알프스의 나라. 영세중립국이자 시계·금융·정밀산업으로 유명.", descEn:"The land of the Alps — a neutral state famous for watches, finance, and precision industry.", landmark:"마터호른", landmarkEn:"Matterhorn", fun:"공용어가 4개(독일어·프랑스어·이탈리아어·로만슈어)예요. 오랜 영세중립국입니다.", funEn:"It has four official languages (German·French·Italian·Romansh) and is a long-standing neutral state." },
  { id:33, name:"스웨덴", nameEn:"Sweden", flag:"🇸🇪", heroImg:"https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Gamla_stan_September_2014_01.jpg/3840px-Gamla_stan_September_2014_01.jpg", capital:"스톡홀름", capitalEn:"Stockholm", region:"유럽", population:10500000, area:450295, languages:"스웨덴어", languagesEn:"Swedish", religion:"개신교(루터교)·무종교", religionEn:"Protestant (Lutheran)·None", currency:"크로나 (SEK)", currencyEn:"Krona (SEK)", dial:"+46", desc:"복지와 디자인의 나라. 노벨상 시상식이 열리는 곳.", descEn:"A land of welfare and design — home of the Nobel Prize ceremony.", landmark:"감라스탄", landmarkEn:"Gamla stan", fun:"노벨상 시상식이 매년 스톡홀름에서 열려요(평화상만 오슬로). 이케아·볼보의 나라.", funEn:"The Nobel Prize ceremony is held in Stockholm each year (except the Peace Prize, in Oslo). Home of IKEA and Volvo." },
  { id:34, name:"그리스", nameEn:"Greece", flag:"🇬🇷", heroImg:"https://upload.wikimedia.org/wikipedia/commons/d/da/The_Parthenon_in_Athens.jpg", capital:"아테네", capitalEn:"Athens", region:"유럽", population:10400000, area:131957, languages:"그리스어", languagesEn:"Greek", religion:"정교회", religionEn:"Orthodox", currency:"유로 (EUR)", currencyEn:"Euro (EUR)", dial:"+30", desc:"서양 문명·민주주의·올림픽의 발상지. 6천여 개의 섬.", descEn:"The cradle of Western civilization, democracy, and the Olympics, with over 6,000 islands.", landmark:"파르테논 신전", landmarkEn:"Parthenon", fun:"민주주의와 올림픽이 시작된 나라예요. 6천여 개의 섬 중 사람이 사는 곳은 약 200여 곳.", funEn:"The birthplace of democracy and the Olympics. Of its 6,000+ islands, only about 200 are inhabited." },
  { id:35, name:"포르투갈", nameEn:"Portugal", flag:"🇵🇹", heroImg:"https://upload.wikimedia.org/wikipedia/commons/f/fa/Bel%C3%A9m_Tower_in_Lisbon%2C_Portugal.jpg", capital:"리스본", capitalEn:"Lisbon", region:"유럽", population:10300000, area:92212, languages:"포르투갈어", languagesEn:"Portuguese", religion:"가톨릭", religionEn:"Catholic", currency:"유로 (EUR)", currencyEn:"Euro (EUR)", dial:"+351", desc:"대항해시대를 연 나라. 이베리아 반도 서쪽 끝.", descEn:"The nation that launched the Age of Discovery, at the western edge of Iberia.", landmark:"벨렘 탑", landmarkEn:"Belém Tower", fun:"대항해시대를 이끌며 포르투갈어를 여러 대륙에 남겼어요(브라질 등). 에그타르트의 원조.", funEn:"It led the Age of Discovery and spread Portuguese across continents (e.g. Brazil). The home of the egg tart (pastel de nata)." },
  { id:36, name:"러시아", nameEn:"Russia", flag:"🇷🇺", heroImg:"https://upload.wikimedia.org/wikipedia/commons/1/18/Saint_Basil%27s_Cathedral_in_Moscow.jpg", capital:"모스크바", capitalEn:"Moscow", region:"유럽", population:144000000, area:17098242, languages:"러시아어", languagesEn:"Russian", religion:"정교회·무종교", religionEn:"Orthodox·None", currency:"루블 (RUB)", currencyEn:"Ruble (RUB)", dial:"+7", desc:"세계에서 면적이 가장 넓은 나라. 유럽과 아시아에 걸쳐 11개 시간대.", descEn:"The largest country in the world by area, spanning Europe and Asia across 11 time zones.", landmark:"성 바실리 대성당", landmarkEn:"Saint Basil's Cathedral", fun:"국토 면적 세계 1위로, 시간대가 11개나 됩니다.", funEn:"The world's largest country by area, with a remarkable 11 time zones." },
  { id:37, name:"칠레", nameEn:"Chile", flag:"🇨🇱", heroImg:"https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Easter_Island_5.jpg/3840px-Easter_Island_5.jpg", capital:"산티아고", capitalEn:"Santiago", region:"남아메리카", population:19600000, area:756102, languages:"스페인어", languagesEn:"Spanish", religion:"가톨릭", religionEn:"Catholic", currency:"페소 (CLP)", currencyEn:"Peso (CLP)", dial:"+56", desc:"남북으로 4,300km 길게 뻗은 나라. 아타카마 사막과 파타고니아.", descEn:"A country stretching 4,300 km north to south — from the Atacama Desert to Patagonia.", landmark:"모아이", landmarkEn:"Moai", fun:"남북으로 매우 길고 동서로는 좁아요. 세계에서 가장 건조한 아타카마 사막이 있습니다.", funEn:"Extremely long north-to-south and narrow east-to-west. Home to the Atacama, the world's driest desert." },
  { id:38, name:"콜롬비아", nameEn:"Colombia", flag:"🇨🇴", heroImg:"https://upload.wikimedia.org/wikipedia/commons/3/30/Museo_Naval_del_Caribe.JPG", capital:"보고타", capitalEn:"Bogotá", region:"남아메리카", population:52000000, area:1141748, languages:"스페인어", languagesEn:"Spanish", religion:"가톨릭", religionEn:"Catholic", currency:"페소 (COP)", currencyEn:"Peso (COP)", dial:"+57", desc:"커피와 에메랄드로 유명. 카리브해와 태평양을 동시에 낀 나라.", descEn:"Famous for coffee and emeralds, bordering both the Caribbean and the Pacific.", landmark:"카르타헤나", landmarkEn:"Cartagena", fun:"고급 아라비카 커피 산지로 유명해요. 세계 에메랄드의 상당량을 생산합니다.", funEn:"Renowned for high-quality Arabica coffee, and a leading producer of the world's emeralds." },
  { id:39, name:"나이지리아", nameEn:"Nigeria", flag:"🇳🇬", heroImg:"https://upload.wikimedia.org/wikipedia/commons/c/cb/Zuma_Rock.jpg", capital:"아부자", capitalEn:"Abuja", region:"아프리카", population:223000000, area:923768, languages:"영어", languagesEn:"English", religion:"이슬람교·기독교", religionEn:"Muslim·Christian", currency:"나이라 (NGN)", currencyEn:"Naira (NGN)", dial:"+234", desc:"아프리카에서 인구가 가장 많은 나라. 활발한 영화·음악 산업.", descEn:"Africa's most populous country, with a vibrant film and music industry.", landmark:"주마 록", landmarkEn:"Zuma Rock", fun:"아프리카 인구 1위 국가예요. 영화산업 '놀리우드'는 제작 편수가 세계 최상위권.", funEn:"Africa's most populous country. Its film industry, 'Nollywood,' is among the world's most prolific." },
  { id:40, name:"모로코", nameEn:"Morocco", flag:"🇲🇦", heroImg:"https://upload.wikimedia.org/wikipedia/commons/thumb/7/79/Djemaa_el_Fna.jpg/3840px-Djemaa_el_Fna.jpg", capital:"라바트", capitalEn:"Rabat", region:"아프리카", population:37000000, area:446550, languages:"아랍어·베르베르어", languagesEn:"Arabic·Berber", religion:"이슬람교", religionEn:"Muslim", currency:"디르함 (MAD)", currencyEn:"Dirham (MAD)", dial:"+212", desc:"사하라 사막과 아틀라스 산맥, 미로 같은 옛 도시(메디나)로 유명.", descEn:"Famous for the Sahara, the Atlas Mountains, and labyrinthine old towns (medinas).", landmark:"제마 엘프나", landmarkEn:"Jemaa el-Fnaa", fun:"파란 도시 셰프샤우엔, 붉은 도시 마라케시 등 색으로 유명한 도시가 많아요.", funEn:"Known for colorful cities like blue Chefchaouen and red Marrakesh." }
];
const REGIONS = ["전체","아시아","유럽","북아메리카","남아메리카","아프리카","오세아니아"];
const REGION_EN = { "전체":"All", "아시아":"Asia", "유럽":"Europe", "북아메리카":"North America", "남아메리카":"South America", "아프리카":"Africa", "오세아니아":"Oceania" };

// ===== 국기 의미 (상세페이지 '국기 이야기') — ISO 코드 기준 =====
const FLAG_MEANING = {
  kr:{ko:"가운데 태극은 음(파랑)과 양(빨강)의 조화를, 네 모서리의 건·곤·감·리 4괘는 하늘·땅·물·불을 상징해요. 흰 바탕은 밝음과 평화를 사랑하는 민족성을 나타냅니다.",en:"The central taegeuk shows the harmony of yin (blue) and yang (red), while the four trigrams at the corners stand for heaven, earth, water, and fire. The white field reflects a people who love brightness and peace."},
  jp:{ko:"흰 바탕 가운데의 붉은 원은 떠오르는 태양을 나타내며 '일장기(日章旗)'라 불려요. 태양신의 후손이라는 오랜 신화와 이어져 있습니다.",en:"The red disc on white represents the rising sun and is called Hinomaru. It connects to Japan's ancient sun-goddess mythology."},
  cn:{ko:"붉은 바탕은 혁명을, 큰 별은 공산당을, 작은 별 4개는 인민의 단결을 상징해요. 별의 노란색은 광명을 뜻합니다.",en:"The red field stands for revolution, the large star for the Communist Party, and the four small stars for the people's unity. The gold of the stars signifies brightness."},
  in:{ko:"위에서부터 사프란(용기·희생)·흰색(평화·진리)·초록(신의·번영)의 3색이에요. 가운데 파란 아소카 차크라(24살 법륜)는 끊임없는 전진을 뜻합니다.",en:"From top: saffron (courage), white (peace and truth), and green (faith and prosperity). The blue Ashoka Chakra, a 24-spoke wheel, symbolizes ceaseless progress."},
  th:{ko:"바깥의 빨강은 국민, 흰색은 종교(불교), 가운데 굵은 파랑은 왕실을 상징해요. 이 셋은 태국의 근간을 이루는 기둥으로 여겨집니다.",en:"The outer red is the nation, white is religion (Buddhism), and the broad central blue is the monarchy. Together they are seen as the pillars of Thai identity."},
  vn:{ko:"붉은 바탕은 혁명과 피의 희생을, 가운데 노란 별은 인민의 단결을 상징해요. 별의 다섯 꼭짓점은 노동자·농민·지식인·청년·군인을 뜻한다고 해요.",en:"The red field stands for revolution and sacrifice, and the gold star for the unity of the people. Its five points are said to represent workers, farmers, intellectuals, youth, and soldiers."},
  id:{ko:"위의 빨강은 용기와 피를, 아래 흰색은 순결과 정신을 뜻해요. 모나코 국기와 색·비율이 거의 같아 종종 헷갈립니다.",en:"The upper red means courage and blood, the lower white the purity of spirit. It looks almost identical to Monaco's flag."},
  sa:{ko:"초록 바탕에 이슬람 신앙고백(샤하다)이 아랍어로 쓰여 있고 아래엔 검이 있어요. 신성한 문구가 적혀 있어 조기(弔旗)로 내리지 않습니다.",en:"On a green field, the Islamic declaration of faith (shahada) is written in Arabic above a sword. Because it bears sacred script, it is never flown at half-mast."},
  fr:{ko:"파랑·흰색·빨강 삼색은 프랑스 혁명의 자유·평등·박애를 상징해요. 근대 삼색기의 원형이 되어 세계 여러 나라 국기에 영향을 주었습니다.",en:"The blue-white-red tricolour embodies the Revolution's liberty, equality, and fraternity. It became the model for tricolour flags around the world."},
  de:{ko:"검정·빨강·금색은 19세기 통일 운동에서 자유를 향한 열망을 상징했어요. 나폴레옹에 맞선 의용군의 군복 색에서 유래했다는 설이 유명합니다.",en:"Black, red, and gold symbolized the 19th-century drive for unity and freedom. They are often traced to the uniforms of volunteers who fought Napoleon."},
  gb:{ko:"잉글랜드(성 조지)·스코틀랜드(성 앤드루)·아일랜드(성 패트릭)의 십자를 겹친 '유니언잭'이에요. 여러 영연방 국가 국기 한 귀퉁이에 여전히 남아 있습니다.",en:"The 'Union Jack' overlays the crosses of England (St George), Scotland (St Andrew), and Ireland (St Patrick). It still appears in the canton of several Commonwealth flags."},
  it:{ko:"초록·흰색·빨강 삼색기로 프랑스 삼색기의 영향을 받았어요. 초록은 국토, 흰색은 알프스의 눈, 빨강은 독립운동의 피를 뜻한다고도 해요.",en:"A green-white-red tricolour inspired by France's flag. Green is often read as the land, white as Alpine snow, and red as the blood of independence."},
  es:{ko:"빨강·노랑·빨강 띠에 왕실과 옛 왕국들을 담은 국가 문장이 들어가요. '피와 금(sangre y oro)'이라는 별명으로 불립니다.",en:"Red and yellow bands carry a coat of arms representing the crown and old kingdoms. It is nicknamed 'blood and gold' (sangre y oro)."},
  no:{ko:"빨강 바탕에 파란 십자를 흰색으로 두른 스칸디나비아 십자예요. 덴마크 국기에 파랑을 더한 형태로 북유럽의 유대를 보여줍니다.",en:"A Scandinavian cross: blue outlined in white on red. It adds blue to Denmark's design, reflecting Nordic ties."},
  va:{ko:"노랑·흰색 바탕에 성 베드로의 두 열쇠(천국의 열쇠)와 교황의 삼중관이 그려져 있어요. 정사각형에 가까운 몇 안 되는 국기 중 하나입니다.",en:"On yellow and white, it bears St Peter's two keys (to heaven) and the papal tiara. It is one of the few nearly square national flags."},
  us:{ko:"별 50개는 현재의 주, 13개 줄은 독립 당시 13개 식민지를 뜻해요. '성조기(Stars and Stripes)'라 불리며 주가 늘 때마다 별이 추가돼 왔습니다.",en:"The 50 stars are today's states and the 13 stripes the founding colonies. Called the 'Stars and Stripes,' a star was added each time a state joined."},
  ca:{ko:"가운데 붉은 단풍잎은 캐나다를 상징하는 국민적 상징이에요. 지금의 단풍잎기는 1965년에야 공식 채택되었습니다.",en:"The central red maple leaf is Canada's national emblem. The current maple-leaf flag was only adopted in 1965."},
  mx:{ko:"초록(희망)·흰색(통합)·빨강(피)에 독수리가 뱀을 문 아즈텍 건국신화가 담겨 있어요. 선인장 위 독수리가 나타난 곳에 도시를 세우라는 전설에서 나왔습니다.",en:"Green (hope), white (unity), and red (blood), with an eagle devouring a serpent from Aztec legend. The myth told the people to build their city where such an eagle appeared on a cactus."},
  br:{ko:"초록은 숲, 노란 마름모는 금, 파란 천구는 브라질의 하늘을 나타내요. 곡선 띠의 '질서와 진보(Ordem e Progresso)'는 공화국의 이념입니다.",en:"Green for forests, a yellow rhombus for gold, and a blue globe for Brazil's sky. The banner reads 'Order and Progress' (Ordem e Progresso), the republic's motto."},
  ar:{ko:"하늘색과 흰색 줄무늬는 독립 당시의 하늘과 구름을 상징해요. 가운데 얼굴이 있는 '5월의 태양'은 잉카 태양신과 독립을 기립니다.",en:"The sky-blue and white stripes recall the sky and clouds of independence. The 'Sun of May' with a face honors the Inca sun god and the nation's freedom."},
  pe:{ko:"빨강·흰색·빨강 세로 삼색기로, 빨강은 독립 투쟁의 피, 흰색은 평화를 뜻해요. 잉카 제국을 계승한 나라의 정체성을 담고 있습니다.",en:"A red-white-red vertical tricolour: red for the blood of independence and white for peace. It reflects a nation heir to the Inca Empire."},
  eg:{ko:"빨강(투쟁)·흰색(평화)·검정(억압의 종식)의 3색이에요. 가운데 황금빛 '살라딘의 독수리'는 아랍 세계의 상징입니다.",en:"Red (struggle), white (peace), and black (the end of oppression). The golden 'Eagle of Saladin' at the center is a symbol of the Arab world."},
  za:{ko:"여섯 색을 Y자로 합쳐 과거의 분열이 하나로 모이는 '무지개 국가'를 표현해요. 아파르트헤이트 종식 후 1994년에 채택된 화합의 상징입니다.",en:"Six colors converge in a Y-shape, showing a divided past coming together as the 'Rainbow Nation.' Adopted in 1994 after apartheid, it stands for unity."},
  ke:{ko:"검정(국민)·빨강(독립 투쟁의 피)·초록(자연)에 흰 띠(평화)를 둘렀어요. 가운데 마사이족 방패와 창은 자유의 수호를 뜻합니다.",en:"Black (the people), red (blood of independence), and green (nature), edged with white (peace). The central Maasai shield and spears represent the defense of freedom."},
  au:{ko:"유니언잭은 영국과의 역사, 큰 7각별은 6개 주와 준주들의 연방을 뜻해요. 오른쪽 별 5개는 남반구에서 보이는 남십자성입니다.",en:"The Union Jack marks British heritage and the large seven-pointed star the federation of states and territories. The five stars at right form the Southern Cross."},
  nz:{ko:"유니언잭과 함께 붉은 남십자성 별 4개가 그려져 있어요. 별이 6개인 호주 국기와 비슷하지만 개수·색으로 구분됩니다.",en:"The Union Jack accompanies four red stars of the Southern Cross. It resembles Australia's flag but differs in the number and color of stars."},
  ph:{ko:"파랑(평화)·빨강(용기)과 흰 삼각형(평등)에 태양·별 3개가 있어요. 특이하게 전시(戰時)엔 빨강이 위로 오게 뒤집어 답니다.",en:"Blue (peace), red (courage), and a white triangle (equality) with a sun and three stars. Uniquely, it is flown upside-down—red on top—in times of war."},
  sg:{ko:"빨강(형제애)·흰색(순수)에 초승달과 별 5개(민주·평화·진보·정의·평등)가 있어요. 초승달은 떠오르는 젊은 나라를 상징합니다.",en:"Red (brotherhood) and white (purity) with a crescent and five stars (democracy, peace, progress, justice, equality). The crescent stands for a young, rising nation."},
  tr:{ko:"붉은 바탕에 흰 초승달과 별은 이슬람과 튀르키예를 상징해요. 오스만 제국 시절부터 이어져 온 오랜 상징입니다.",en:"The white crescent and star on red symbolize Islam and Türkiye. It is a long-standing emblem dating to the Ottoman era."},
  ae:{ko:"빨강·초록·흰색·검정의 범아랍 색으로 아랍의 통일을 상징해요. 각 색은 용맹·번영·평화·투쟁을 뜻합니다.",en:"The Pan-Arab colors—red, green, white, and black—symbolize Arab unity. The colors stand for valor, prosperity, peace, and struggle."},
  nl:{ko:"빨강·흰색·파랑의 가로 삼색기로, 세계 최초의 삼색기 중 하나예요. 러시아·프랑스 등 여러 나라 삼색기에 영향을 주었습니다.",en:"A red-white-blue horizontal tricolour, one of the world's first. It influenced the tricolours of Russia, France, and others."},
  ch:{ko:"붉은 바탕의 흰 십자로, 바티칸과 함께 정사각형인 드문 국기예요. 이 십자를 색만 바꾼 것이 적십자(Red Cross) 표장입니다.",en:"A white cross on red—one of only two square national flags, with the Vatican's. Inverting its colors gives the Red Cross emblem."},
  se:{ko:"파란 바탕의 노란 스칸디나비아 십자로, 스웨덴 왕가의 색에서 유래했어요. 이웃 노르딕 국가들과 십자 형태를 공유합니다.",en:"A yellow Scandinavian cross on blue, drawn from the royal coat of arms. It shares the cross form with its Nordic neighbors."},
  gr:{ko:"파랑·흰색 9개 줄무늬는 독립 구호 '자유가 아니면 죽음'의 음절 수라고 해요. 왼쪽 위 십자는 그리스 정교회 신앙을 뜻합니다.",en:"The nine blue-and-white stripes are said to match the syllables of the independence cry 'Freedom or Death.' The cross in the canton reflects the Greek Orthodox faith."},
  pt:{ko:"초록·빨강 바탕에 항해 도구인 혼천의와 방패 문장이 있어요. 대항해시대에 바다를 누빈 포르투갈의 역사를 담고 있습니다.",en:"On green and red, it bears an armillary sphere (a navigation instrument) and a shield. It recalls Portugal's seafaring Age of Discovery."},
  ru:{ko:"흰색·파랑·빨강의 가로 삼색기(범슬라브 색)예요. 표트르 대제가 네덜란드 국기를 참고해 만들었다고 전해집니다.",en:"A white-blue-red horizontal tricolour in the Pan-Slavic colors. Tradition says Peter the Great modeled it on the Dutch flag."},
  cl:{ko:"흰색·빨강과 파란 사각형의 흰 별 한 개로 이루어져요. 별은 명예와 진보의 길잡이를, 색은 안데스의 눈·하늘·독립의 피를 뜻합니다.",en:"White and red with a single white star on a blue canton. The star guides honor and progress; the colors mean Andean snow, sky, and the blood of independence."},
  co:{ko:"위쪽 절반의 넓은 노랑은 나라의 부와 금을, 파랑은 바다와 강을, 빨강은 독립의 피를 뜻해요. 에콰도르·베네수엘라와 색 배열이 비슷합니다.",en:"The broad yellow top half means the nation's wealth and gold, blue the seas and rivers, and red the blood of independence. Its colors resemble Ecuador's and Venezuela's."},
  ng:{ko:"초록·흰색·초록 세로 삼색기로, 초록은 농업과 자연, 흰색은 평화와 통합을 뜻해요. 한 대학생이 공모전에서 디자인해 채택됐습니다.",en:"A green-white-green vertical tricolour: green for agriculture and nature, white for peace and unity. It was designed by a student who won a national contest."},
  ma:{ko:"붉은 바탕 가운데 초록 오각별은 '술라이만의 별'로 불려요. 붉은색은 왕조와 용맹을, 별의 다섯 꼭짓점은 이슬람의 다섯 기둥을 상징합니다.",en:"The green pentagram on red is called the 'Seal of Solomon.' Red stands for the dynasty and valor, and the star's five points for the Five Pillars of Islam."}
};
const flagMeaning = code => { const f = FLAG_MEANING[code]; return f ? (LANG==='en' ? f.en : f.ko) : ''; };

// ===== 관광 기반 표시용 베이스라인 (프랑스=100 상대치) =====
// 카드/상세의 가봤어요·가고싶어요에 더해 생동감을 줌. 실제 클릭은 여기에 더해져 저장됨.
const TOUR = { fr:100, es:92, us:80, it:68, cn:66, tr:62, mx:46, de:40, th:40, gb:40, gr:36, jp:34, pt:30, sa:30, ru:28, ca:26, va:26, ae:26, nl:22, sg:22, kr:20, in:20, ch:20, vn:20, id:18, eg:15, ma:15, za:12, se:12, no:12, au:12, ph:12, br:10, cl:8, ar:8, nz:8, pe:6, co:6, ke:4, ng:2 };
const baseCount = (code, kind) => { const t = TOUR[code] || 0; return kind==='visited' ? t : Math.round(t*0.7); };

// ===== 표시용 시드 댓글 (국가별 2~8개). DB엔 저장 안 됨. 실제 댓글은 이 위에 얹힘 =====
const SEED_COMMENTS = {
  kr:[{n:"서울러",b:"광화문 야경 산책 강추! 밤에 조명 켜지면 분위기 최고예요",d:4},{n:"제이",b:"외국인 친구들 경복궁 한복체험 진짜 좋아하더라고요",d:13},{n:"뚜벅이",b:"대중교통 개편함. 티머니 하나면 어디든 감",d:27}],
  jp:[{n:"오사카러버",b:"후지산은 공기 맑은 가을 아침에 가세요. 진짜 선명함",d:5},{n:"라멘조아",b:"편의점만 돌아도 재밌음ㅋㅋ 자판기 진심 천국",d:12},{n:"토모",b:"현금 아직 많이 써요. 동전지갑 챙기세요",d:24},{n:"여기저기",b:"지진 안내가 잘 돼있어서 오히려 안심됐어요",d:40}],
  cn:[{n:"만리장성러",b:"장성 팔달령은 사람 많으니 무티엔위 구간 추천",d:8},{n:"감자",b:"알리페이/위챗페이 없으면 좀 불편해요. 준비 필수",d:19},{n:"유랑",b:"땅이 넓어서 도시 간 이동은 고속철 강추",d:33}],
  in:[{n:"배낭킴",b:"타지마할 일출 보러 새벽에 갔는데 인생샷 건짐",d:6},{n:"초코라떼",b:"향신료 향에 적응하면 커리 헤어나올 수 없음",d:21},{n:"나그네",b:"기차표는 미리미리! 인도 기차 낭만 그 자체",d:45}],
  th:[{n:"방콕댁",b:"왓 아룬은 강 건너에서 노을 질 때 보면 진짜 예뻐요",d:3},{n:"소금",b:"길거리 팟타이 40바트 실화? 물가 사랑합니다",d:10},{n:"모모",b:"마사지 받으러 갔다가 매일 감ㅋㅋ",d:22},{n:"별헤는밤",b:"미소의 나라 맞아요. 사람들 진짜 친절",d:38}],
  vn:[{n:"쌀국수귀신",b:"하롱베이 크루즈 1박 강추. 아침 안개가 몽환적",d:7},{n:"라라",b:"연유커피 한 번 맛보면 못 끊어요",d:16},{n:"유랑",b:"오토바이 물결 처음엔 무서운데 나중엔 적응됨ㅋ",d:29}],
  id:[{n:"발리홀릭",b:"보로부두르 일출 투어 새벽 4시 기상값 함",d:9},{n:"감자",b:"섬마다 분위기가 완전 달라요. 여러 곳 가보세요",d:25},{n:"뚜벅이",b:"우붓 논밭뷰 카페 진심 힐링이에요",d:41}],
  sa:[{n:"사막여행자",b:"메카는 무슬림만 입장 가능하니 참고하세요",d:11},{n:"한량",b:"리야드 근교 사막 캠프에서 별 봤는데 쏟아짐",d:28}],
  fr:[{n:"파리지앵",b:"에펠탑 야경 반짝일 때 진짜 눈물남 🥹",d:2},{n:"미니",b:"루브르는 하루로 부족해요. 목표 정하고 가세요",d:6},{n:"초코라떼",b:"빵집마다 크루아상 맛이 달라서 매일 도장깨기함",d:11},{n:"떠돌이별",b:"물가 좀 있지만 그만한 값어치. 소매치기만 조심",d:19},{n:"제이",b:"몽마르트 언덕 노을 강추. 화가들 구경도 재밌음",d:30},{n:"여행자J",b:"지방 소도시가 더 예뻐요. 콜마르 꼭 가보세요",d:48}],
  de:[{n:"맥주사랑",b:"옥토버페스트 시즌 아니어도 비어가든 최고예요",d:8},{n:"소금",b:"기차 연착 은근 있음ㅋㅋ 여유롭게 다니세요",d:17},{n:"하늘바라기",b:"빵 종류 진짜 많음. 프레첼 사랑합니다",d:35}],
  gb:[{n:"런던러",b:"빅벤 앞은 늘 사람 많아요. 아침 일찍 추천",d:5},{n:"나그네",b:"비 자주 와요. 우산보다 방수자켓이 편함",d:14},{n:"모모",b:"저녁에 동네 펍 한 잔 하는 분위기 너무 좋아요",d:31}],
  it:[{n:"파스타요정",b:"콜로세움 야간 입장 예약하면 사람 적고 조명 예뻐요",d:4},{n:"미니",b:"젤라또 하루 두 개는 국룰입니다",d:9},{n:"유랑",b:"로마는 걸어다녀야 제맛. 골목마다 유적",d:18},{n:"별헤는밤",b:"거리 분수대 물 마셔도 돼요. 텀블러 챙기세요",d:27},{n:"감자",b:"기차로 피렌체-베네치아 당일치기 가능해요",d:44}],
  es:[{n:"플라멩코",b:"사그라다 파밀리아 내부 스테인드글라스 진짜 예술",d:6},{n:"한량",b:"저녁 9시에 저녁 먹는 문화. 시에스타 적응 필요ㅋ",d:15},{n:"라라",b:"타파스 바 순례가 진심 여행의 꽃이에요",d:29}],
  no:[{n:"오로라헌터",b:"겨울에 트롬쇠에서 오로라 봤어요. 인생 목표 달성",d:12},{n:"하늘바라기",b:"물가 살벌해요… 마트 이용 필수",d:26},{n:"유랑",b:"피오르 크루즈는 날 맑은 날 강추. 비 오면 아쉬움",d:40}],
  va:[{n:"순례자",b:"성 베드로 대성전 돔 오르면 로마 전경 다 보여요",d:10},{n:"모모",b:"복장 규정 있어요. 어깨·무릎 가리세요",d:23}],
  us:[{n:"뉴욕러",b:"자유의 여신상은 스태튼 페리에서 보는 게 가성비 甲",d:7},{n:"감자",b:"주마다 완전 다른 나라 같음. 렌트카 여행 추천",d:16},{n:"떠돌이별",b:"팁 문화 익숙해지는 데 시간 좀 걸림ㅋ",d:33}],
  ca:[{n:"단풍러",b:"나이아가라는 캐나다 쪽 뷰가 훨씬 좋아요",d:9},{n:"별헤는밤",b:"밴프 국립공원 호수 물색 실화냐… 에메랄드빛",d:20},{n:"소금",b:"땅 넓어서 이동 오래 걸림. 일정 여유있게",d:38}],
  mx:[{n:"타코중독",b:"치첸이트사 춘분 뱀 그림자 이벤트 신기해요",d:11},{n:"라라",b:"길거리 타코 진짜 저렴하고 맛있어요",d:24}],
  br:[{n:"삼바러",b:"예수상은 맑은 날 필수. 흐리면 구름에 가려요",d:8},{n:"나그네",b:"치안 주의. 소지품은 최소한으로 다니세요",d:19},{n:"유랑",b:"이과수는 브라질·아르헨 양쪽 다 보는 게 좋아요",d:37}],
  ar:[{n:"탱고러버",b:"부에노스아이레스 탱고 공연 밤에 꼭 보세요",d:13},{n:"감자",b:"소고기 진짜 저렴하고 맛있음. 아사도 강추",d:30}],
  pe:[{n:"마추픽추",b:"고산증 조심. 쿠스코에서 며칠 적응하고 올라가세요",d:10},{n:"배낭킴",b:"잉카트레일 예약은 몇 달 전에 미리 하세요",d:28}],
  eg:[{n:"파라오",b:"피라미드 근처 낙타 호객 심해요. 흥정 필수",d:12},{n:"소금",b:"카이로 박물관 미라관 진짜 소름. 꼭 가세요",d:27}],
  za:[{n:"사파리킴",b:"테이블마운틴은 바람 없는 날 케이블카 타야 해요",d:14},{n:"모모",b:"물개섬·펭귄해변까지 하루코스 알차요",d:33}],
  ke:[{n:"초원러",b:"마사이마라 누 떼 대이동은 7~9월이 하이라이트",d:15},{n:"나그네",b:"새벽 게임드라이브가 동물 제일 많이 봐요",d:34}],
  au:[{n:"코알라",b:"오페라하우스는 페리 위에서 보는 야경이 최고예요",d:6},{n:"별헤는밤",b:"자외선 진짜 강해요. 선크림 필수템",d:18}],
  nz:[{n:"반지원정대",b:"밀퍼드사운드 유람선 폭포 바로 앞까지 가요",d:9},{n:"유랑",b:"양이 사람보다 많다는 말 실감남ㅋㅋ",d:25}],
  ph:[{n:"섬여행자",b:"보라카이 화이트비치 노을 강추. 물 진짜 맑아요",d:7},{n:"라라",b:"영어 잘 통해서 여행 편했어요",d:20}],
  sg:[{n:"머라이언",b:"마리나베이샌즈 인피니티풀은 투숙객만 이용 가능해요",d:5},{n:"감자",b:"가든스바이더베이 야간 조명쇼 무료인데 퀄 미쳤음",d:16},{n:"소금",b:"껌 반입 규정 진짜 있음. 벌금 조심하세요",d:31}],
  tr:[{n:"이스탄불러",b:"아야소피아·블루모스크 나란히 있어 동선 좋아요",d:8},{n:"나그네",b:"카파도키아 열기구는 새벽에 떠요. 예약 필수",d:22}],
  ae:[{n:"두바이러",b:"부르즈 할리파 전망대는 해질녘 예약이 명당",d:6},{n:"한량",b:"여름은 진짜 살인적으로 더워요. 봄·가을 추천",d:21}],
  nl:[{n:"풍차러버",b:"킨더다이크는 자전거 대여해서 도는 거 강추",d:11},{n:"모모",b:"운하 보트투어는 노을시간에 타면 예뻐요",d:26}],
  ch:[{n:"알프스",b:"마터호른은 체르마트에서 아침에 봐야 구름 안 껴요",d:9},{n:"하늘바라기",b:"물가 극악… 근데 풍경값은 확실히 함",d:24}],
  se:[{n:"북유럽러",b:"감라스탄 골목 색색 건물이 사진맛집이에요",d:13},{n:"라라",b:"피카(fika) 커피타임 문화 너무 좋아요",d:29}],
  gr:[{n:"산토리니",b:"파르테논은 아침 일찍 가야 덜 더워요",d:7},{n:"유랑",b:"섬 이동은 페리라서 시간표 꼭 확인하세요",d:19}],
  pt:[{n:"리스본러",b:"에그타르트 원조 벨렘 꼭 가보세요. 줄 서도 값함",d:10},{n:"감자",b:"트램 28번 타면 시내 명소 다 돌아요",d:23}],
  ru:[{n:"모스크바",b:"성 바실리 대성당 색감 실물이 더 예뻐요",d:14},{n:"소금",b:"겨울 진짜 추워요. 방한 단단히 하세요",d:32}],
  cl:[{n:"별헤는밤",b:"아타카마 사막 밤하늘 별 관측은 인생경험이에요",d:12},{n:"나그네",b:"남북으로 길어서 지역별 날씨가 완전 달라요",d:30}],
  co:[{n:"커피러버",b:"카르타헤나 구시가지 색색 골목 진짜 예뻐요",d:11},{n:"라라",b:"커피농장 투어 강추. 원두 향 미쳤음",d:27}],
  ng:[{n:"아프로비트",b:"라고스 음악 씬 에너지 대박. 아프로비트 성지예요",d:15},{n:"소금",b:"치안은 신경 써야 하지만 사람들 정 많아요",d:33}],
  ma:[{n:"사막여행자",b:"마라케시 제마엘프나 광장 밤엔 완전 축제 분위기",d:9},{n:"모모",b:"셰프샤우엔 파란마을은 어디서 찍어도 인생샷",d:24}]
};

// ===== 언어(i18n) =====
let LANG = (localStorage.getItem('lang') === 'ko') ? 'ko' : 'en';   // 기본값 영어(EN) — 저장된 값이 'ko'일 때만 한국어
function setLang(l){ LANG = (l === 'en') ? 'en' : 'ko'; localStorage.setItem('lang', LANG); }
function t(k){ return (I18N[LANG] && I18N[LANG][k] != null) ? I18N[LANG][k] : (I18N.ko[k] != null ? I18N.ko[k] : k); }
// 나라별 현지화 접근자
const L = {
  name:      c => LANG==='en' ? c.nameEn      : c.name,
  region:    c => LANG==='en' ? (REGION_EN[c.region]||c.region) : c.region,
  capital:   c => LANG==='en' ? c.capitalEn   : c.capital,
  languages: c => LANG==='en' ? c.languagesEn : c.languages,
  religion:  c => LANG==='en' ? c.religionEn  : c.religion,
  currency:  c => LANG==='en' ? c.currencyEn  : c.currency,
  desc:      c => LANG==='en' ? c.descEn      : c.desc,
  fun:       c => LANG==='en' ? c.funEn       : c.fun,
  landmark:  c => LANG==='en' ? c.landmarkEn  : c.landmark
};
const regionLabel = r => LANG==='en' ? (REGION_EN[r]||r) : r;

const I18N = {
  ko: {
    docTitle:"세계 국가 도감", brand:"World Atlas · 세계 국가 도감",
    mastTitle:"세계를,<br><em>한 장에 펼치다.</em>",
    mastSub:"40개국의 국기·수도·인구·면적·언어·종교·통화를 한 장에 담았습니다. 나라를 누르면 국기에 담긴 의미부터 대표 명소·여행 정보까지 이어지고, 가봤어요·가고싶어요 버튼과 댓글로 여행의 기억을 나눌 수 있어요. 오른쪽 지구본을 잡고 돌려보세요 — 세계가 손끝에서 움직입니다.",
    searchPh:"나라 이름으로 검색 (예: 프랑스, 브라질)", searchAria:"국가 검색",
    fav:"⭐ 즐겨찾기", popular:"🔥 인기순",
    countCountries:"개 나라", countFav:"⭐ 즐겨찾기", countSearch:"검색",
    empty:"🔎 조건에 맞는 나라가 없습니다.<br>검색어·지역을 바꾸거나 즐겨찾기를 추가해 보세요.",
    visited:"가봤어요", wish:"가고싶어요", viewsShort:"조회",
    visitTotal:"누적 방문", visitToday:"오늘", topViewed:"가장 많이 본 나라",
    beChecking:"백엔드 연결 확인 중…",
    beOffMast:"⚠️ 백엔드 미연결 — 목업 데이터로 둘러보기만 가능",
    beOn:"🟢 백엔드 연결됨 · 익명 사용자로 접속",
    beFail:"⚠️ 로그인 실패 — Supabase '익명 로그인(Anonymous)' 켰는지 확인: ",
    footer:"KDT Node · World Atlas — Frontend + Supabase (visits · views · comments · reactions · favorites, RLS)",
    back:"← 세계 국가 도감", crumbAtlas:"도감",
    ovOverview:"개요", ovMark:"나의 기록", ovLandmark:"대표 명소", ovKnow:"알아두면", ovComments:"댓글", ovMoreIn:"같은 지역",
    kCapital:"수도", kPop:"인구", kArea:"면적", kLang:"언어", kRel:"종교", kCur:"통화", kDial:"국제전화", kRegion:"지역", kViews:"조회수",
    markFavOn:"★ 즐겨찾기 됨", markFavOff:"☆ 즐겨찾기",
    wikiMore:"위키백과에서 더 보기 →", photoCredit:"사진: Wikimedia Commons", loadingWiki:"불러오는 중…",
    cmtLoading:"불러오는 중…", cmtOffList:"댓글은 백엔드 연결 후 표시돼요.",
    cmtEmpty:"아직 댓글이 없어요. 첫 댓글을 남겨보세요!", cmtFail:"댓글을 불러오지 못했어요: ",
    cmtNick:"닉네임", cmtBody:"이 나라에 대한 한마디… (여행 팁, 감상 등)", cmtPost:"댓글 등록", cmtDel:"삭제",
    cmtOff:"댓글·반응·즐겨찾기는 <b>Supabase 연결 후</b> 사용할 수 있어요. (data.js에 키를 넣고 익명 로그인을 켜면 활성화)",
    cmtNeedBoth:"닉네임과 내용을 모두 입력해 주세요.", cmtDelConfirm:"이 댓글을 삭제할까요?",
    beNeed:"백엔드 연결 후 사용할 수 있어요.",
    beOffCountry:"⚠️ 백엔드 미연결 — 정보 열람만 가능 (data.js에 키 + 익명 로그인 켜면 반응·댓글 활성화)",
    nfTitle:"나라를 찾을 수 없어요", nfDesc:"주소가 올바르지 않거나 목록에 없는 나라입니다.", nfBack:"← 세계 국가 도감으로 돌아가기",
    backToAll:"← 전체 도감으로 돌아가기",
    secAtaGlance:"한눈에", secGeo:"지리·자연", secHist:"역사", secCult:"문화", secPeople:"사람·사회", secEcon:"경제", secPlaces:"명소",
    kSubregion:"소지역", kNeighbors:"인접국", kDemonym:"국민 호칭", kLandlocked:"해안 여부", kCoords:"좌표", kGDP:"명목 GDP", kGDPpc:"1인당 GDP", kLifeExp:"기대수명", kUrban:"도시화율", kNaviBorders:"국경을 맞댄 나라",
    vLandlockedY:"내륙국", vLandlockedN:"바다에 접함", noNeighbors:"육지 국경 없음 (섬·해양국)", yearsUnit:"세",
    srcWiki:"출처: 위키백과", srcWB:"출처: World Bank·mledoze/countries", openMap:"지도에서 열기 →", jumpTo:"바로가기", noData:"자료 준비 중"
  },
  en: {
    docTitle:"World Atlas", brand:"World Atlas",
    mastTitle:"The World,<br><em>Unfolded.</em>",
    mastSub:"Flags, capitals, population, area, languages, religion, and currency for 40 countries — gathered on a single page. Tap a country to dive into its story, from the meaning woven into its flag to landmarks and travel notes, and leave your mark with been-there, want-to-go, and comments. And go ahead — grab the globe and spin it. The world moves at your fingertips.",
    searchPh:"Search by country name (e.g. France, Brazil)", searchAria:"Search countries",
    fav:"⭐ Favorites", popular:"🔥 Popular",
    countCountries:" countries", countFav:"⭐ Favorites", countSearch:"search",
    empty:"🔎 No countries match your filters.<br>Try a different search or region, or add a favorite.",
    visited:"Been there", wish:"Want to go", viewsShort:"views",
    visitTotal:"Total visits", visitToday:"Today", topViewed:"Most viewed",
    beChecking:"Checking backend…",
    beOffMast:"⚠️ Backend not connected — browsing mock data only",
    beOn:"🟢 Backend connected · signed in anonymously",
    beFail:"⚠️ Sign-in failed — check that Anonymous sign-ins are enabled in Supabase: ",
    footer:"KDT Node · World Atlas — Frontend + Supabase (visits · views · comments · reactions · favorites, RLS)",
    back:"← World Atlas", crumbAtlas:"Atlas",
    ovOverview:"Overview", ovMark:"Your mark", ovLandmark:"Landmark", ovKnow:"Did you know", ovComments:"Comments", ovMoreIn:"More in",
    kCapital:"Capital", kPop:"Population", kArea:"Area", kLang:"Languages", kRel:"Religion", kCur:"Currency", kDial:"Dialing code", kRegion:"Region", kViews:"Views",
    markFavOn:"★ Favorited", markFavOff:"☆ Favorite",
    wikiMore:"Read more on Wikipedia →", photoCredit:"Photo: Wikimedia Commons", loadingWiki:"Loading…",
    cmtLoading:"Loading…", cmtOffList:"Comments appear once the backend is connected.",
    cmtEmpty:"No comments yet. Be the first!", cmtFail:"Couldn't load comments: ",
    cmtNick:"Nickname", cmtBody:"A word about this country… (tips, impressions)", cmtPost:"Post comment", cmtDel:"Delete",
    cmtOff:"Comments, reactions, and favorites work <b>once Supabase is connected</b>. (Add the key in data.js and enable anonymous sign-in.)",
    cmtNeedBoth:"Please enter both a nickname and a message.", cmtDelConfirm:"Delete this comment?",
    beNeed:"Available after the backend is connected.",
    beOffCountry:"⚠️ Backend not connected — viewing only (add the key in data.js + enable anonymous sign-in for reactions·comments)",
    nfTitle:"Country not found", nfDesc:"The address is invalid or this country isn't in the list.", nfBack:"← Back to World Atlas",
    backToAll:"← Back to the full atlas",
    secAtaGlance:"At a glance", secGeo:"Geography & Nature", secHist:"History", secCult:"Culture", secPeople:"People & Society", secEcon:"Economy", secPlaces:"Places",
    kSubregion:"Subregion", kNeighbors:"Neighbors", kDemonym:"Demonym", kLandlocked:"Coastline", kCoords:"Coordinates", kGDP:"GDP (nominal)", kGDPpc:"GDP per capita", kLifeExp:"Life expectancy", kUrban:"Urban population", kNaviBorders:"Countries sharing a border",
    vLandlockedY:"Landlocked", vLandlockedN:"Has coastline", noNeighbors:"No land borders (island / maritime)", yearsUnit:"yrs",
    srcWiki:"Source: Wikipedia", srcWB:"Source: World Bank · mledoze/countries", openMap:"Open in map →", jumpTo:"Jump to", noData:"Data coming soon"
  }
};

// ===== 공유 헬퍼 =====
const flagCode = flag => String.fromCharCode(...[...flag].map(c => c.codePointAt(0) - 0x1F1E6 + 97));
function fmtPop(n){
  if(LANG === 'en'){
    if(n >= 1e9){ return (n/1e9).toFixed(2).replace(/\.?0+$/,'') + "B"; }
    if(n >= 1e6){ const m = n/1e6; return (m < 100 ? m.toFixed(1).replace(/\.0$/,'') : Math.round(m)) + "M"; }
    if(n >= 1e3){ return Math.round(n/1e3) + "K"; }
    return n.toLocaleString();
  }
  if(n >= 1e8){ const eok = Math.floor(n/1e8), man = Math.round((n%1e8)/1e4); return man>0 ? `${eok}억 ${man.toLocaleString()}만 명` : `${eok}억 명`; }
  if(n >= 1e4){ return `${Math.round(n/1e4).toLocaleString()}만 명`; }
  return `${n.toLocaleString()}명`;
}
const fmtArea = n => (n < 1 ? n : Math.round(n).toLocaleString()) + " km²";
const fmtUSD = n => { if(n==null) return null; if(n>=1e12) return "$"+(n/1e12).toFixed(2).replace(/\.?0+$/,"")+"T"; if(n>=1e9) return "$"+(n/1e9).toFixed(1).replace(/\.0$/,"")+"B"; if(n>=1e6) return "$"+(n/1e6).toFixed(1).replace(/\.0$/,"")+"M"; return "$"+Math.round(n).toLocaleString(); };
const atlasMeta = code => (typeof ATLAS_META !== "undefined" && ATLAS_META[code]) ? ATLAS_META[code] : null;
const esc = s => (s||"").replace(/[&<>"]/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));
const countryByCode = code => COUNTRIES.find(c => flagCode(c.flag) === code);

// ===== 위키백과 랜드마크 이미지·해설 (히어로용) =====
// ko/en.wikipedia REST API는 CORS 허용 → 로컬/정적 배포 모두 fetch 가능. 실패 시 폴백.
async function fetchWiki(title, lang){
  lang = (lang === 'en') ? 'en' : 'ko';
  try{
    const r = await fetch(`https://${lang}.wikipedia.org/api/rest_v1/page/summary/` + encodeURIComponent(title), { headers:{ accept:"application/json" } });
    if(!r.ok) return null;
    const d = await r.json();
    const oi = d.originalimage || d.thumbnail || {};
    const img = oi.source || null;
    return { title: d.title || title, img, w: oi.width||0, h: oi.height||0, extract: d.extract || "", url: (d.content_urls && d.content_urls.desktop && d.content_urls.desktop.page) || "" };
  }catch(e){ return null; }
}

// ===== 방문자·조회수 백엔드 (page_views 로그 + 집계 RPC) =====
// 세션당 1회만 기록(새로고침 스팸 방지). 집계는 RPC 함수(SECURITY DEFINER)로만 읽음.
async function logView(code, uid){
  if(!sb || !uid) return;
  const key = 'pv_' + (code || 'home');
  if(sessionStorage.getItem(key)) return;
  sessionStorage.setItem(key, '1');
  try{ await sb.from('page_views').insert({ code: code || null, user_id: uid }); }catch(e){}
}
async function getVisitStats(){
  if(!sb) return null;
  try{ const { data } = await sb.rpc('get_visit_stats'); return (data && data[0]) || null; }catch(e){ return null; }
}
async function getViewCounts(){
  if(!sb) return {};
  try{ const { data } = await sb.rpc('get_view_counts'); const m = {}; (data||[]).forEach(r => m[r.code] = Number(r.views)); return m; }catch(e){ return {}; }
}
