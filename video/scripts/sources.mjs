// Prints {mitigation id: law chip text} for the mitigations shown, so the Python test checks the chips the scene draws.
import {readFileSync} from "node:fs";
import {aiActArticles, articleLabel} from "../src/sources.mjs";

const read = (path) => JSON.parse(readFileSync(new URL(path, import.meta.url), "utf8"));
const timeline = read("../src/timeline.json");
const all = Object.values(read("../../tools/data/mitigation_suggestions.json").risks).flat();
const shown = timeline.scenes.find((s) => s.id === "mitigations").dataRefs.mitigations.shown;
console.log(JSON.stringify(Object.fromEntries(shown.map((id) => [id, articleLabel(aiActArticles(all.find((m) => m.id === id)))]))));
