"use client";

import { useState } from "react";
import { t, type Lang } from "@/lib/i18n";

export default function TasteSummary({
  count,
  lang,
}: {
  count: number;
  lang: Lang;
}) {
  const [state, setState] = useState<"idle" | "loading" | "done" | "error">(
    "idle"
  );
  const [paras, setParas] = useState<string[]>([]);

  async function analyze() {
    setState("loading");
    try {
      const res = await fetch("/api/taste", { method: "POST" });
      if (!res.ok) throw new Error(await res.text());
      const { text } = await res.json();
      setParas(
        String(text)
          .split(/\n\n+/)
          .map((s) => s.trim())
          .filter(Boolean)
      );
      setState("done");
    } catch {
      setState("error");
    }
  }

  return (
    <div className="docent" style={{ marginBottom: "1.5rem" }}>
      <div className="docent-head">
        <span className="t">{t(lang, "taste_title")}</span>
        {state === "idle" && (
          <button className="btn btn-solid" onClick={analyze}>
            {t(lang, "taste_run")}
          </button>
        )}
        {(state === "done" || state === "error") && (
          <button className="btn" onClick={analyze}>
            {t(lang, "taste_regen")}
          </button>
        )}
      </div>
      <div className="docent-body">
        {state === "idle" && (
          <p className="docent-hint">
            {lang === "en"
              ? `The AI reads your ${count} saved origins and summarizes the lineage you're drawn to and how to use it in your own work.`
              : `담아 둔 ${count}개의 원류를 AI가 읽고, 당신이 끌리는 계보와 그것을 오늘의 작업에 쓰는 법을 요약해 드립니다.`}
          </p>
        )}
        {state === "loading" && (
          <p className="docent-hint">
            {t(lang, "taste_loading")}{" "}
            <span className="dots">
              <span></span>
              <span></span>
              <span></span>
            </span>
          </p>
        )}
        {state === "error" && (
          <p className="docent-hint">{t(lang, "taste_error")}</p>
        )}
        {state === "done" && paras.map((p, i) => <p key={i}>{p}</p>)}
      </div>
    </div>
  );
}
