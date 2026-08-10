# 모듈2 노드7 과제 · 폰 영상 하나로 만든 3D 방

폰으로 걸어 다니며 찍은 영상 한 개에서 3차원 공간을 복원해 웹에 올린 것입니다.

**▶ 보기:** https://kimjy0977.github.io/KDT_Works/03_module2/d_hw_N6-room-3d/

마우스를 끌면 방이 돌고, 휠로 확대됩니다. 우측 상단 버튼으로 자동회전·위아래뒤집기·알갱이 퍼짐 조절.

## 어떻게 만들었나

```
폰 영상(1920x1080, 50초) → 사진 32장 → 3D 점 444만 개 → 가우시안 알갱이 → .sog 21MB → 이 주소
```

가운데 "점을 만드는 일"만 AI가 하고 나머지는 파일 변환입니다.

| 단계 | 내용 | 결과 |
|---|---|---|
| 복원 | `facebook/map-anything-apache` (Apache-2.0), 코랩 T4, fp16 | 점 4,436,737개, 카메라 32, 13.4초·VRAM 7.2GB |
| 검증 | 카메라 이동폭/장면 대각선 = 3.42/7.49 = **0.456** (>0.1 정상) | 걸어 찍음 확인 |
| 알갱이 | 점→가우시안 스플랫 `.ply` (17칸, 68바이트/알갱이, f_rest 없음), y·z 부호 뒤집기 | 301.7MB |
| 압축 | `@playcanvas/splat-transform` → `.sog` | 21.3MB |
| 뷰어 | three.js + Spark 2.1 (`SparkRenderer`, `pcsogszip`) | index.html |

## 들어 있는 것

| 파일 | 무엇 |
|---|---|
| `index.html` | 브라우저에서 방을 띄우는 페이지 |
| `room.sog` | 알갱이 444만 개, 21MB |
| `.nojekyll` | 깃허브가 파일 이름을 손대지 않게 하는 표시 |

## 쓴 것

MapAnything Apache-2.0 · three.js MIT · Spark MIT · splat-transform MIT.
지침 스킬 출처: https://github.com/SunCreation/room-3d-demo
