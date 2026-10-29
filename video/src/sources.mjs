// Shared by the mitigations scene and, through scripts/sources.mjs, its test, so the chip on screen is the one checked.

/** The article numbers a mitigation's EU AI Act sources cite; other EUR-Lex law, such as the GDPR, is left out. */
export const aiActArticles = (m) =>
  m.sources
    .filter((s) => s.title?.startsWith("EU AI Act"))
    .flatMap((s) => [...s.title.matchAll(/Article (\d+)/g)].map((a) => Number(a[1])));

/** "EU AI Act · Article 10" or "EU AI Act · Articles 14 and 26"; empty when nothing is cited. */
export const articleLabel = (articles) =>
  !articles.length
    ? ""
    : articles.length === 1
      ? `EU AI Act · Article ${articles[0]}`
      : `EU AI Act · Articles ${articles.slice(0, -1).join(", ")} and ${articles.at(-1)}`;
