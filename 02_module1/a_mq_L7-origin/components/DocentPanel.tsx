"use client";

import { useState } from "react";
import { t, type Lang } from "@/lib/i18n";

export default function DocentPanel({
  workId,
  lang,
}: {
  workId: number;
  lang: Lang;
}) {
  const [state, setState] = useState<"idle" | "loading" | "done" | "error">(
    "idle"
  );
  const [paras, setParas] = useState<string[]>([]);

  async function load() {
    setState("loading");
    try {
      const res = await fetch("/api/docent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ workId }),
      });
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
    <div className="docent">
      <div className="docent-head">
        <span className="t">{t(lang, "docent_title")}</span>
        {state === "idle" && (
          <button className="btn" onClick={load}>
            {t(lang, "docent_load")}
          </button>
        )}
        {(state === "done" || state === "error") && (
          <button className="btn" onClick={load}>
            {t(lang, "docent_regen")}
          </button>
        )}
      </div>
      <div className="docent-body">
        {state === "idle" && <p className="docent-hint">{t(lang, "docent_hint")}</p>}
        {state === "loading" && (
          <p className="docent-hint">
            {t(lang, "docent_loading")}{" "}
            <span className="dots">
              <span></span>
              <span></span>
              <span></span>
            </span>
          </p>
        )}
        {state === "error" && (
          <p className="docent-hint">{t(lang, "docent_error")}</p>
        )}
        {state === "done" && paras.map((p, i) => <p key={i}>{p}</p>)}
      </div>
    </div>
  );
}
