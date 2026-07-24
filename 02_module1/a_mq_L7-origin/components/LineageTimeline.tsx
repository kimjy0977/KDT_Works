import type { Lang } from "@/lib/i18n";
import type { Movement } from "@/lib/types";

// 계보 시각화 — 사조를 시대축(간트) 위에 레인 배치. 순수 서버 렌더.
// PRD §3 '발전: 계보 연결선 시각화' 구현.
export default function LineageTimeline({
  movements,
  lang,
}: {
  movements: Movement[];
  lang: Lang;
}) {
  if (movements.length === 0) return null;

  const min = Math.min(...movements.map((m) => m.era_start));
  const max = Math.max(...movements.map((m) => m.era_end));
  const span = max - min || 1;

  // 시작연도 순으로 정렬 후, 겹치지 않는 첫 레인에 배치(간트 패킹)
  const byStart = [...movements].sort((a, b) => a.era_start - b.era_start);
  const laneEnds: number[] = [];
  const placed = byStart.map((m) => {
    let lane = laneEnds.findIndex((end) => end <= m.era_start);
    if (lane === -1) {
      lane = laneEnds.length;
      laneEnds.push(m.era_end);
    } else {
      laneEnds[lane] = m.era_end;
    }
    return { m, lane };
  });
  const lanes = laneEnds.length;

  // 20년 단위 눈금
  const firstTick = Math.ceil(min / 20) * 20;
  const ticks: number[] = [];
  for (let y = firstTick; y <= max; y += 20) ticks.push(y);

  return (
    <section className="lineage-tl" aria-label={lang === "en" ? "Lineage timeline" : "계보 타임라인"}>
      <div className="lineage-tl-head">
        <p className="eyebrow">{lang === "en" ? "Lineage" : "계보"}</p>
        <h2 className="lineage-tl-title">
          {lang === "en" ? "One century of origins" : "원류의 한 세기"}
        </h2>
        <p className="lineage-tl-sub">
          {lang === "en"
            ? `${min}–${max} · how the movements overlap and hand off`
            : `${min}–${max} · 사조들이 겹치고 이어지는 흐름`}
        </p>
      </div>

      <div className="lineage-tl-scroll">
        <div
          className="lineage-tl-plot"
          style={{ height: `${lanes * 3.1 + 1.6}rem` }}
        >
          {ticks.map((y) => {
            const left = ((y - min) / span) * 100;
            return (
              <div key={y} className="tl-tick" style={{ left: `${left}%` }}>
                <span>{y}</span>
              </div>
            );
          })}
          {placed.map(({ m, lane }) => {
            const left = ((m.era_start - min) / span) * 100;
            const width = ((m.era_end - m.era_start) / span) * 100;
            return (
              <a
                key={m.id}
                href={`#${m.slug}`}
                className="tl-bar"
                style={{
                  left: `${left}%`,
                  width: `${width}%`,
                  top: `${lane * 3.1}rem`,
                }}
                title={`${lang === "en" ? m.name_en : m.name_ko} · ${m.era_start}–${m.era_end}`}
              >
                <span className="tl-bar-name">
                  {lang === "en" ? m.name_en : m.name_ko}
                </span>
                <span className="tl-bar-era">
                  {m.era_start}–{m.era_end}
                </span>
              </a>
            );
          })}
        </div>
      </div>
    </section>
  );
}
