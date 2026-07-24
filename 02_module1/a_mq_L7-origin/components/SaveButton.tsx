"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { t, type Lang } from "@/lib/i18n";

export default function SaveButton({
  workId,
  initialSaved,
  isLoggedIn,
  lang,
}: {
  workId: number;
  initialSaved: boolean;
  isLoggedIn: boolean;
  lang: Lang;
}) {
  const router = useRouter();
  const [saved, setSaved] = useState(initialSaved);
  const [busy, setBusy] = useState(false);

  async function toggle() {
    if (!isLoggedIn) {
      router.push("/login?next=/works/" + workId);
      return;
    }
    setBusy(true);
    try {
      const res = await fetch("/api/board", {
        method: saved ? "DELETE" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ workId }),
      });
      if (res.ok) setSaved(!saved);
    } finally {
      setBusy(false);
    }
  }

  if (!isLoggedIn) {
    return (
      <button className="btn" onClick={toggle}>
        {t(lang, "save_add")}{" "}
        <span style={{ opacity: 0.6 }}>{t(lang, "save_login")}</span>
      </button>
    );
  }

  return (
    <button
      className={saved ? "btn" : "btn btn-solid"}
      onClick={toggle}
      disabled={busy}
    >
      {saved ? t(lang, "save_added") : t(lang, "save_add")}
    </button>
  );
}
