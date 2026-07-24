"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { t, type Lang, type DictKey } from "@/lib/i18n";

const ROLES: { value: string; key: DictKey }[] = [
  { value: "graphic", key: "role_graphic" },
  { value: "product", key: "role_product" },
  { value: "student", key: "role_student" },
  { value: "illustrator", key: "role_illustrator" },
  { value: "curious", key: "role_curious" },
];

export default function ProfileEditor({
  movements,
  lang,
  initialInterests,
  initialRole,
  mode,
}: {
  movements: { slug: string; name: string }[];
  lang: Lang;
  initialInterests: string[];
  initialRole: string | null;
  mode: "welcome" | "profile";
}) {
  const router = useRouter();
  const [interests, setInterests] = useState<string[]>(initialInterests);
  const [role, setRole] = useState<string | null>(initialRole);
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);

  function toggleInterest(slug: string) {
    setInterests((cur) =>
      cur.includes(slug) ? cur.filter((s) => s !== slug) : [...cur, slug]
    );
    setSaved(false);
  }

  async function save() {
    setBusy(true);
    try {
      const res = await fetch("/api/profile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ interests, role }),
      });
      if (res.ok) {
        if (mode === "welcome") {
          router.push("/");
          router.refresh();
        } else {
          setSaved(true);
          router.refresh();
        }
      }
    } finally {
      setBusy(false);
    }
  }

  function skip() {
    router.push("/");
    router.refresh();
  }

  return (
    <div className="onboard">
      <div className="onboard-block">
        <h2 className="onboard-q">{t(lang, "wel_q1")}</h2>
        <p className="onboard-qsub">{t(lang, "wel_q1_sub")}</p>
        <div className="chips">
          {movements.map((m) => (
            <button
              key={m.slug}
              className={`chip ${interests.includes(m.slug) ? "on" : ""}`}
              onClick={() => toggleInterest(m.slug)}
              aria-pressed={interests.includes(m.slug)}
            >
              {m.name}
            </button>
          ))}
        </div>
      </div>

      <div className="onboard-block">
        <h2 className="onboard-q">{t(lang, "wel_q2")}</h2>
        <div className="chips">
          {ROLES.map((r) => (
            <button
              key={r.value}
              className={`chip ${role === r.value ? "on" : ""}`}
              onClick={() => {
                setRole(role === r.value ? null : r.value);
                setSaved(false);
              }}
              aria-pressed={role === r.value}
            >
              {t(lang, r.key)}
            </button>
          ))}
        </div>
      </div>

      <div className="onboard-actions">
        <button className="btn btn-solid" onClick={save} disabled={busy}>
          {busy
            ? t(lang, "auth_processing")
            : mode === "welcome"
            ? t(lang, "wel_save")
            : saved
            ? t(lang, "profile_saved")
            : t(lang, "profile_save")}
        </button>
        {mode === "welcome" && (
          <button className="linkish" onClick={skip}>
            {t(lang, "wel_skip")}
          </button>
        )}
      </div>
    </div>
  );
}
