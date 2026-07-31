# 테스트에 쓴 프롬프트 모음

## 입력 포즈
- 전신 OpenPose 스켈레톤(서있는 자세)을 프레임 위쪽에 여백 두고 배치 → `samples/pose_01.png`
- (참조 원본: `sd_controlnet/pose.png` 전신 스켈레톤)

## 프롬프트 (같은 포즈, 프롬프트만 변경)
- A(캐주얼) → `full length wide shot photo of a man standing, entire body from head to shoes, wearing sneakers, feet on the floor, casual clothes, plain studio background, highly detailed` → `output_01.png`
- B(정장) → `full length wide shot photo of a man standing, entire body from head to shoes, wearing dress shoes, feet on the floor, business suit, plain studio background, highly detailed` → `output_02.png`
- 공통 negative → `cropped, cut off at waist, cut off at knees, missing feet, no shoes, close-up, portrait, headshot, out of frame, lowres, bad anatomy, worst quality, blurry`

## 설정
- height=768, width=512, steps=20, seed=42(고정), controlnet_conditioning_scale=1.15
- scheduler=UniPCMultistepScheduler, controlnet=lllyasviel/sd-controlnet-openpose

## 관찰 메모
- 프롬프트만 바꿈: 전신 서있는 자세 유지, 옷차림(캐주얼↔정장)만 바뀜 → 포즈 반영 O
- 다리 잘림 해결: 세로 프레임 + 스켈레톤 위쪽 배치(아래 여백) + conditioning scale 1.15 + "head to shoes" 프롬프트
- 시드 고정: 재실행 시 동일 이미지 재현
