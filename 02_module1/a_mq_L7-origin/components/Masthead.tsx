"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { t, type Lang } from "@/lib/i18n";
import ThemeToggle from "./ThemeToggle";
import LangToggle from "./LangToggle";

export default function Masthead({ lang }: { lang: Lang }) {
  const supabase = createClient();
  const router = useRouter();
  const [email, setEmail] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => {
      setEmail(data.user?.email ?? null);
      setReady(true);
    });
    const { data: sub } = supabase.auth.onAuthStateChange((_e, session) => {
      setEmail(session?.user?.email ?? null);
    });
    return () => sub.subscription.unsubscribe();
  }, [supabase]);

  async function signOut() {
    await supabase.auth.signOut();
    router.push("/");
    router.refresh();
  }

  return (
    <header className="masthead">
      <div className="masthead-inner">
        <Link href="/" className="brand">
          <span className="brand-mark">ORIGIN</span>
          <span className="brand-sub nav-hide">{t(lang, "brandSub")}</span>
        </Link>
        <nav className="nav">
          <Link href="/archive" className="nav-hide">
            {t(lang, "nav_archive")}
          </Link>
          <Link href="/essays" className="nav-hide">
            {t(lang, "nav_essays")}
          </Link>
          <Link href="/board">{t(lang, "nav_board")}</Link>
          <LangToggle lang={lang} />
          <ThemeToggle />
          {ready &&
            (email ? (
              <button className="nav-btn" onClick={signOut} title={email}>
                {t(lang, "logout")}
              </button>
            ) : (
              <Link href="/login" className="nav-btn">
                {t(lang, "login")}
              </Link>
            ))}
        </nav>
      </div>
    </header>
  );
}
