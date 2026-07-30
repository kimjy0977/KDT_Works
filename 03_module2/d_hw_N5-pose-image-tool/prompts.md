# 테스트에 쓴 프롬프트 모음

## 입력 포즈
- 참조 사진: `input_image_vermeer.png` (상반신 초상, 고개를 옆으로 기울인 자세)
- OpenPose로 추출한 스켈레톤 → `samples/pose_01.png`

## 프롬프트 (같은 포즈, 프롬프트만 변경)
- A → `a photo of an astronaut in a white spacesuit, studio lighting, highly detailed` → `output_01.png`
- B → `a medieval knight in shining steel armor, dramatic cinematic lighting, highly detailed` → `output_02.png`
- 공통 negative prompt → `lowres, bad anatomy, worst quality, blurry`

## 설정
- steps=25, scheduler=UniPCMultistepScheduler, seed=42(고정), controlnet=openpose

## 관찰 메모
- 프롬프트만 바꿈: 자세(구도·머리 방향) 유지, 인물만 바뀜 → 포즈 반영 O
- 시드 고정: 재실행 시 동일 이미지 재현
