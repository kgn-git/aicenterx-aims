// Shared by the scenes and, through scripts/trace.mjs, the trace test, so the graph on screen is the one checked.

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

/** One row per saved enhancement: the enhancement, the saved mitigation it puts into effect with that mitigation's
 *  EU AI Act articles, and the saved risk that mitigation answers. Rows are grouped by risk, in the order each risk's
 *  first enhancement is saved, so the scene draws each risk once beside all its rows. */
export function traceRows({timeline, enhancements, risks, mitigations, labels}) {
  const saved = (kind) => timeline.scenes.find((s) => s.id === kind).dataRefs[kind].saved;
  const savedRisks = risks.initiatives.hiring.suggestions.filter((s) => saved("risks").includes(s.id));
  const rows = saved("enhancements").map((id) => {
    const e = enhancements.enhancements.find((x) => x.id === id);
    const m = Object.values(mitigations.risks).flat().find((x) => x.id === e.mitigationId);
    // A suggestion that matches a register risk keeps its mitigations under that risk, as test/video_keys.py says.
    const answering = savedRisks.filter((s) => (mitigations.risks[s.matchesRisk || s.id] ?? []).some((x) => x.id === m.id));
    if (answering.length !== 1) throw new Error(`${id}: ${answering.length} saved risks answer its mitigation, want 1.`);
    const risk = answering[0];
    return {
      risk: {id: risk.id, label: labels[risk.id]},
      mitigation: {id: m.id, label: labels[m.id], articles: aiActArticles(m)},
      enhancement: {id, label: e.name, kind: e.kind},
    };
  });
  const order = [...new Set(rows.map((r) => r.risk.id))];
  return rows.sort((a, b) => order.indexOf(a.risk.id) - order.indexOf(b.risk.id));
}
