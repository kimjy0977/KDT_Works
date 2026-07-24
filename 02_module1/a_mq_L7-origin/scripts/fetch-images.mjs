// 디자인사 작품의 실제 이미지 URL을 위키백과 action API(배치)로 해석한다.
// key → { image, page, resolved } 를 JSON으로 출력.

const ITEMS = [
  ["morris-strawberry",      "Strawberry Thief"],
  ["morris-acanthus",        "Acanthus (wallpaper)"],
  ["webb-red-house",         "Red House, Bexleyheath"],
  ["lautrec-goulue",         "Moulin Rouge: La Goulue"],
  ["mucha-gismonda",         "Gismonda (poster)"],
  ["klimt-kiss",             "The Kiss (Klimt)"],
  ["tiffany-lamp",           "Tiffany lamp"],
  ["gaudi-batllo",           "Casa Batlló"],
  ["mondrian-composition",   "Composition II in Red, Blue, and Yellow"],
  ["rietveld-chair",         "Red and Blue Chair"],
  ["rietveld-house",         "Rietveld Schröder House"],
  ["kandinsky-comp8",        "Composition VIII"],
  ["breuer-wassily",         "Wassily Chair"],
  ["mies-barcelona",         "Barcelona chair"],
  ["gropius-fagus",          "Fagus Factory"],
  ["lissitzky-wedge",        "Beat the Whites with the Red Wedge"],
  ["malevich-blacksquare",   "Black Square (painting)"],
  ["lempicka-bugatti",       "Autoportrait (Tamara in a Green Bugatti)"],
  ["chrysler-building",      "Chrysler Building"],
  ["helvetica",              "Helvetica"],
];

const byTitle = new Map(ITEMS.map(([k, t]) => [t, k]));
const titles = ITEMS.map(([, t]) => t).join("|");

const api = new URL("https://en.wikipedia.org/w/api.php");
api.search = new URLSearchParams({
  action: "query",
  format: "json",
  formatversion: "2",
  redirects: "1",
  prop: "pageimages|info",
  piprop: "original|thumbnail",
  pithumbsize: "1600",
  inprop: "url",
  titles,
}).toString();

const res = await fetch(api, {
  headers: { "User-Agent": "ORIGIN-archive/1.0 (educational KDT project; contact kjuyoung77@gmail.com)" },
});
const data = await res.json();

// redirects/normalized 로 원제목 → 요청제목 역추적
const remap = new Map(); // resolvedTitle -> requestedTitle
for (const n of data.query?.normalized ?? []) remap.set(n.to, n.from);
for (const r of data.query?.redirects ?? []) remap.set(r.to, remap.get(r.from) ?? r.from);

const out = {};
const failed = [];
for (const p of data.query?.pages ?? []) {
  const requested = remap.get(p.title) ?? p.title;
  const key = byTitle.get(requested);
  if (!key) { failed.push(["?", p.title]); continue; }
  const image = p.original?.source || p.thumbnail?.source || null;
  if (!image) { failed.push([key, p.title, "no-image"]); continue; }
  out[key] = { image, page: p.canonicalurl, resolved: p.title };
}

console.log(JSON.stringify(out, null, 2));
console.error("\n=== RESOLVED:", Object.keys(out).length, "/", ITEMS.length, "===");
if (failed.length) console.error("FAILED:", JSON.stringify(failed));
