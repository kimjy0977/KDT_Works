"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { t, type Lang } from "@/lib/i18n";

export default function LoginForm({ next, lang }: { next: string; lang: Lang }) {
  const supabase = createClient();
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [pw, setPw] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ t: string; kind: "err" | "ok" } | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMsg(null);
    try {
      if (mode === "signup") {
        const { data, error } = await supabase.auth.signUp({ email, password: pw });
        if (error) throw error;
        if (data.session) {
          router.push(next);
          router.refresh();
        } else {
          setMsg({
            t:
              lang === "en"
                ? "Account created. If email confirmation is on, check your inbox."
                : "가입 완료. 메일 확인이 켜져 있다면 받은 편지함을 확인해 주세요.",
            kind: "ok",
          });
          setMode("login");
        }
      } else {
        const { error } = await supabase.auth.signInWithPassword({ email, password: pw });
        if (error) throw error;
        router.push(next);
        router.refresh();
      }
    } catch (err) {
      const m = err instanceof Error ? err.message : "Error";
      setMsg({ t: m, kind: "err" });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-wrap">
      <div className="auth-card">
        <h1>{mode === "login" ? t(lang, "auth_login") : t(lang, "auth_signup")}</h1>
        <p className="sub">{t(lang, "auth_sub")}</p>
        <form onSubmit={submit}>
          <div className="field">
            <label htmlFor="email">{t(lang, "auth_email")}</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              placeholder="you@example.com"
            />
          </div>
          <div className="field">
            <label htmlFor="pw">{t(lang, "auth_pw")}</label>
            <input
              id="pw"
              type="password"
              value={pw}
              onChange={(e) => setPw(e.target.value)}
              required
              minLength={6}
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              placeholder={t(lang, "auth_pw_hint")}
            />
          </div>
          {msg && <p className={`auth-msg ${msg.kind}`}>{msg.t}</p>}
          {!msg && <p className="auth-msg">&nbsp;</p>}
          <button className="btn btn-solid" style={{ width: "100%" }} disabled={busy}>
            {busy
              ? t(lang, "auth_processing")
              : mode === "login"
              ? t(lang, "auth_go_login")
              : t(lang, "auth_go_signup")}
          </button>
        </form>
        <p className="auth-toggle">
          {mode === "login" ? t(lang, "auth_no_account") : t(lang, "auth_has_account")}
          <button
            onClick={() => {
              setMode(mode === "login" ? "signup" : "login");
              setMsg(null);
            }}
          >
            {mode === "login" ? t(lang, "auth_signup") : t(lang, "auth_login")}
          </button>
        </p>
      </div>
    </div>
  );
}
