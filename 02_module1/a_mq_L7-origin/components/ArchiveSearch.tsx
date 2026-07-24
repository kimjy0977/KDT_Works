"use client";

import { useState } from "react";
import type { Lang } from "@/lib/i18n";

// 아카이브 검색 — 서버 렌더된 카드/섹션을 클라이언트에서 필터.
// PRD §3 '발전: 사조별 필터·검색' 구현.
export default function ArchiveSearch({ lang }: { lang: Lang }) {
  const [q, setQ] = useState("");

  function apply(value: string) {
    setQ(value);
    const v = value.trim().toLowerCase();
    const cards = document.querySelectorAll<HTMLElement>("[data-search]");
    cards.forEach((c) => {
      const hit = !v || (c.dataset.search || "").includes(v);
      c.style.display = hit ? "" : "none";
    });
    let anyVisible = false;
    document.querySelectorAll<HTMLElement>(".movement").forEach((s) => {
      const shown = Array.from(
        s.querySelectorAll<HTMLElement>("[data-search]")
      ).some((el) => el.style.display !== "none");
      s.style.display = shown ? "" : "none";
      if (shown) anyVisible = true;
    });
    const empty = document.getElementById("archive-empty");
    if (empty) empty.style.display = anyVisible ? "none" : "";
  }

  return (
    <div className="archive-search">
      <input
        type="search"
        value={q}
        onChange={(e) => apply(e.target.value)}
        placeholder={
          lang === "en"
            ? "Search works, makers, movements…"
            : "작품·작가·사조 검색…"
        }
        aria-label={lang === "en" ? "Search the archive" : "아카이브 검색"}
      />
      {q && (
        <button type="button" className="archive-search-clear" onClick={() => apply("")}>
          {lang === "en" ? "Clear" : "지우기"}
        </button>
      )}
    </div>
  );
}
