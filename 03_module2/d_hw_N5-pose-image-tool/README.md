# 원하는 포즈로 이미지 만드는 도구

참조 사진의 자세(포즈)를 그대로 따라 하는 새 이미지를 만드는 Colab 튜토리얼.

## 도구 설명
참조 사람 사진에서 **OpenPose**로 관절(스켈레톤)을 뽑고, 그 포즈를 **ControlNet 조건**으로 넣어
**Stable Diffusion 1.5**가 **같은 자세의 다른 인물/장면**을 생성한다.

## 사용법
1. `pose_tool.ipynb`를 Colab에서 연다.
2. 런타임을 **T4 GPU** 로 바꾼다 (런타임 > 런타임 유형 변경).
3. 셀을 **위에서 아래로 순서대로** 실행한다.
4. 결과 이미지는 `samples/` 폴더에 저장된다 (`pose_01.png`, `output_01.png`, `output_02.png`).
5. 내 사진을 쓰려면 3번 셀의 `load_image(...)` URL을 업로드한 파일명으로 바꾼다.

## 테스트 결과
| 입력 포즈 | 프롬프트 | 결과 | 포즈 반영 |
|---|---|---|---|
| pose_01 (상반신·고개 기울임) | a photo of an astronaut... | output_01.png | ✅ 같은 구도·머리 방향 |
| pose_01 (동일) | a medieval knight... | output_02.png | ✅ 같은 자세, 인물만 기사로 |

- **같은 포즈 + 프롬프트만 변경:** 두 결과 모두 상반신 초상·고개 옆으로 돌린 **같은 자세** 유지, 인물/의상만 우주비행사↔기사로 바뀜 → 입력 포즈가 그대로 반영됨.
- **재현성:** `seed=42` 고정 → 같은 입력이면 동일 이미지 재현.

## 한계
- 참조가 상반신 초상이라 하반신 포즈는 제어되지 않음(전신 포즈는 전신 사진 입력 필요).
- 손가락 등 미세 부위는 OpenPose 정밀도 한계로 덜 정확.

## 사용 모델
- 포즈 추출: `lllyasviel/Annotators` (OpenPose)
- 생성: `stable-diffusion-v1-5/stable-diffusion-v1-5` + ControlNet `lllyasviel/sd-controlnet-openpose`
