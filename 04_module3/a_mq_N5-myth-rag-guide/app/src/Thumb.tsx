import { useState } from "react";

/**
 * 작품 썸네일. MYTH GALLERY 원본을 그대로 가리킨다.
 *
 * 첫 방문에는 23MB WASM과 320KB 청크가 동시에 내려오므로 이미지 요청이 밀려
 * 한 번에 실패할 수 있다(로컬 확인에서 12장이 전부 그렇게 깨졌다).
 * 그래서 실패하면 캐시를 우회해 한 번 더 시도하고, 그래도 안 되면
 * 빈 칸 대신 "그림을 불러오지 못했습니다"를 남긴다 — 깨진 아이콘은
 * 방문자에게 서비스 오류처럼 보이기 때문이다.
 */
export function Thumb({ src, alt }: { src: string; alt: string }) {
  const [tries, setTries] = useState(0);

  if (tries > 1) {
    return (
      <div className="thumb-fail" role="img" aria-label={alt}>
        그림을 불러오지 못했습니다
      </div>
    );
  }

  return (
    <img
      src={tries === 0 ? src : `${src}?r=${tries}`}
      alt={alt}
      loading="lazy"
      decoding="async"
      onError={() => setTries((n) => n + 1)}
    />
  );
}
