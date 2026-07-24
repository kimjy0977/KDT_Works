"use client";

import { useRouter } from "next/navigation";
import { useTransition } from "react";
import type { Lang } from "@/lib/i18n";

export default function LangToggle({ lang }: { lang: Lang }) {
  const router = useRouter();
  const [pending, start] = useTransition();

  function set(next: Lang) {
    if (next === lang) return;
    // 1년 유지 쿠키
    document.cookie = `lang=${next}; path=/; max-age=31536000; samesite=lax`;
    start(() => router.refresh());
  }

  return (
    <div className="lang-toggle" aria-busy={pending}>
      <button
        className={lang === "en" ? "on" : ""}
        onClick={() => set("en")}
        aria-pressed={lang === "en"}
      >
        EN
      </button>
      <span className="sep">/</span>
      <button
        className={lang === "ko" ? "on" : ""}
        onClick={() => set("ko")}
        aria-pressed={lang === "ko"}
      >
        KO
      </button>
    </div>
  );
}
