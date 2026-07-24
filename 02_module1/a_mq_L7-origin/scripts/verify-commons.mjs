// 커먼즈 File: 제목의 실제 업로드 URL을 imageinfo로 확정한다.
const CANDIDATES = {
  "mondrian-composition": [
    "Piet Mondriaan, 1930 - Mondrian Composition II in Red, Blue, and Yellow.jpg",
    "Tableau I, by Piet Mondriaan.jpg",
  ],
  "kandinsky-comp8": [
    "Vassily Kandinsky, 1923 - Composition 8, huile sur toile, 140 cm x 201 cm, Musée Guggenheim, New York.jpg",
    "Kandinsky - Composition 8.jpg",
  ],
  "mucha-gismonda": [
    "Alfons Mucha - 1894 - Gismonda.jpg",
    "Mucha-Gismonda.jpg",
  ],
  "chrysler-building": [
    "Chrysler Building Midtown Manhattan New York City 1932.jpg",
    "Chrysler Building by David Shankbone Retouched.jpg",
    "Chrysler Building spire, Manhattan, by Carol Highsmith (LOC highsm.04444).jpg",
  ],
};

async function imageinfo(fileTitle) {
  const api = new URL("https://commons.wikimedia.org/w/api.php");
  api.search = new URLSearchParams({
    action: "query", format: "json", formatversion: "2",
    prop: "imageinfo", iiprop: "url", iiurlwidth: "1600",
    titles: "File:" + fileTitle,
  }).toString();
  const res = await fetch(api, { headers: { "User-Agent": "ORIGIN-archive/1.0 (educational)" } });
  const d = await res.json();
  const p = d.query?.pages?.[0];
  if (!p || p.missing) return null;
  const ii = p.imageinfo?.[0];
  return ii ? { image: ii.thumburl || ii.url, page: ii.descriptionurl } : null;
}

const out = {};
for (const [key, list] of Object.entries(CANDIDATES)) {
  for (const f of list) {
    const r = await imageinfo(f);
    if (r) { out[key] = r; break; }
  }
  if (!out[key]) console.error("STILL MISSING:", key);
}
console.log(JSON.stringify(out, null, 2));
