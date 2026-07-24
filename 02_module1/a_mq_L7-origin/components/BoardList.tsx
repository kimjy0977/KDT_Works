"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import type { BoardEntry } from "@/lib/types";
import { t, pick, type Lang } from "@/lib/i18n";

function Row({
  item,
  lang,
  onRemoved,
}: {
  item: BoardEntry;
  lang: Lang;
  onRemoved: (id: number) => void;
}) {
  const [note, setNote] = useState(item.note ?? "");
  const [saved, setSaved] = useState(item.note ?? "");
  const [busy, setBusy] = useState(false);
  const title = pick(lang, item.work.title, item.work.title_en);
  const mvName =
    lang === "en" ? item.work.movement.name_en : item.work.movement.name_ko;

  async function saveNote() {
    if (note === saved) return;
    setBusy(true);
    try {
      const res = await fetch("/api/board", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ workId: item.work_id, note }),
      });
      if (res.ok) setSaved(note);
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    setBusy(true);
    const res = await fetch("/api/board", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ workId: item.work_id }),
    });
    if (res.ok) onRemoved(item.id);
    else setBusy(false);
  }

  return (
    <div className="board-row">
      <Link href={`/works/${item.work_id}`} className="thumb">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={item.work.image_url} alt={title} loading="lazy" />
      </Link>
      <div>
        <h3>
          <Link href={`/works/${item.work_id}`}>{title}</Link>
        </h3>
        <div className="bm">
          {item.work.creator} · {item.work.year} · {mvName}
        </div>
        <textarea
          className="note-area"
          placeholder={t(lang, "note_placeholder")}
          value={note}
          onChange={(e) => setNote(e.target.value)}
          onBlur={saveNote}
        />
      </div>
      <div className="row-tools">
        {note !== saved && (
          <button className="linkish" onClick={saveNote} disabled={busy}>
            {t(lang, "note_save")}
          </button>
        )}
        {note === saved && saved && <span className="bm">{t(lang, "note_saved")}</span>}
        <button className="linkish" onClick={remove} disabled={busy}>
          {t(lang, "remove")}
        </button>
      </div>
    </div>
  );
}

export default function BoardList({
  items,
  lang,
}: {
  items: BoardEntry[];
  lang: Lang;
}) {
  const router = useRouter();
  const [list, setList] = useState(items);

  function onRemoved(id: number) {
    setList((l) => l.filter((x) => x.id !== id));
    router.refresh();
  }

  return (
    <div>
      {list.map((item) => (
        <Row key={item.id} item={item} lang={lang} onRemoved={onRemoved} />
      ))}
    </div>
  );
}
