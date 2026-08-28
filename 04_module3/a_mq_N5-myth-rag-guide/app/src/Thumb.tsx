import { useState } from "react";

/**
 * 작품 썸네일. MYTH GALLERY 원본을 그대로 가리킨다.
 *
 * loading="lazy"를 쓰지 않는다. 배포 주소에서 확인해 보니 12장이 화면 안에
 * 들어와 있는데도 요청 자체가 나가지 않아 빈 칸으로 남았다(에러가 아니라
 * 미발화라 onError도 걸리지 않았다). 썸네일 열두 장을 합쳐야 421KB로,
 * 같은 페이지가 받는 23MB WASM에 비하면 지연 로딩으로 아낄 것이 없다.
 *
 * 그래도 요청이 실패할 수는 있으므로 한 번 더 시도하고, 그래도 안 되면
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
      decoding="async"
      onError={() => setTries((n) => n + 1)}
    />
  );
}
