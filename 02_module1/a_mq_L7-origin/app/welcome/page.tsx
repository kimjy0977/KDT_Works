import Link from "next/link";
import { getArchive, getMyProfile } from "@/lib/queries";
import { createClient } from "@/lib/supabase/server";
import { getLang } from "@/lib/lang";
import { t } from "@/lib/i18n";
import ProfileEditor from "@/components/ProfileEditor";

export const dynamic = "force-dynamic";

export default async function WelcomePage() {
  const lang = await getLang();
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return (
      <div className="wrap empty">
        <p style={{ fontFamily: "var(--serif)", fontSize: "1.6rem" }}>
          {t(lang, "wel_title")}
        </p>
        <p>{t(lang, "board_login_prompt")}</p>
        <p style={{ marginTop: "1.4rem" }}>
          <Link className="btn btn-solid" href="/login?next=/welcome">
            {t(lang, "login")}
          </Link>
        </p>
      </div>
    );
  }

  const [archive, profile] = await Promise.all([getArchive(), getMyProfile()]);
  const movements = archive.map((m) => ({
    slug: m.slug,
    name: lang === "en" ? m.name_en : m.name_ko,
  }));

  return (
    <div className="wrap-narrow onboard-wrap">
      <p className="eyebrow">{t(lang, "wel_eyebrow")}</p>
      <h1 className="onboard-title">{t(lang, "wel_title")}</h1>
      <p className="onboard-sub">{t(lang, "wel_sub")}</p>
      <ProfileEditor
        movements={movements}
        lang={lang}
        initialInterests={profile?.interests ?? []}
        initialRole={profile?.role ?? null}
        mode="welcome"
      />
    </div>
  );
}
