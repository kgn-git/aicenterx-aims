// Builds the caption cues, src/captions.json, from each scene's narration and audioSeconds:
//   npm run video:cues                writes src/captions.json
//   node scripts/cues.mjs --stdout    prints it instead, for the freshness check in the captions test
// There are no word timestamps, so each cue's share of its clip follows its share of the scene's characters.
import {readFileSync, renameSync, writeFileSync} from "node:fs";
import {dirname, join} from "node:path";
import {fileURLToPath} from "node:url";
import {sceneSeconds} from "../src/timing.mjs";

const LINE = 42;
const LINES = 2;
// A break after one of these splits a phrase from its noun, which subtitle practice avoids.
const WEAK = new Set(["a", "an", "the", "its", "of", "in", "by", "on", "to", "and", "from", "for", "with"]);
const src = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const timeline = JSON.parse(readFileSync(join(src, "timeline.json"), "utf8"));
const scenes = new Map(timeline.scenes.map((s) => [s.id, s]));
const round = (x) => Math.round(x * 1000) / 1000;

const stop = (message) => {
  console.error(message);
  process.exit(1);
};

/** How badly a break between word a and word b reads: free after punctuation, costly inside a phrase or a name. */
function breakCost(a, b) {
  if (/[,:;.!?]$/.test(a)) return 0;
  if (WEAK.has(a.toLowerCase())) return 40;
  if (/^[A-Z]/.test(a) && /^[A-Z]/.test(b)) return 60;
  return 10;
}

/** Every way to cut `count` words into n runs, as the indexes where each later run starts. */
function* cuts(count, n, from = 1) {
  if (n === 1) {
    yield [];
    return;
  }
  for (let i = from; i <= count - n + 1; i++) for (const rest of cuts(count, n - 1, i + 1)) yield [i, ...rest];
}

/** The cheapest split of words into n runs of at most width characters: even lengths, breaks at phrase ends. */
function bestSplit(words, n, width) {
  let best = null;
  for (const at of cuts(words.length, n)) {
    const bounds = [0, ...at, words.length];
    const texts = bounds.slice(0, -1).map((s, i) => words.slice(s, bounds[i + 1]).join(" "));
    if (texts.some((t) => t.length > width)) continue;
    const mean = texts.reduce((sum, t) => sum + t.length, 0) / n;
    const cost =
      texts.reduce((sum, t) => sum + (t.length - mean) ** 2 / 10, 0) +
      at.reduce((sum, i) => sum + breakCost(words[i - 1], words[i]), 0);
    if (!best || cost < best.cost) best = {texts, cost};
  }
  return best?.texts ?? null;
}

/** A sentence as the fewest cues that fit, each of one or two lines, with no cue spanning two sentences. */
function blocks(narration, sceneId) {
  const out = [];
  for (const sentence of narration.match(/\S.*?(?:[.!?]+(?=\s|$)|$)/g) ?? []) {
    const words = sentence.split(/\s+/);
    let cues = null;
    for (let n = Math.ceil(sentence.length / (LINE * LINES)); n <= words.length && !cues; n++) {
      const chunks = bestSplit(words, n, LINE * LINES + 1);
      const lines = chunks?.map((c) => (c.length <= LINE ? [c] : bestSplit(c.split(" "), LINES, LINE)));
      if (lines?.every(Boolean)) cues = lines;
    }
    if (!cues) stop(`A sentence in ${sceneId} cannot fit captions of ${LINES} lines of ${LINE} characters.`);
    out.push(...cues);
  }
  return out;
}

const cues = [];
for (const fragment of timeline.fragments) {
  let at = 0;
  for (const id of fragment.scenes) {
    const scene = scenes.get(id);
    if (!scene.audioSeconds) stop(`${id} has no audioSeconds yet. Run npm run video:narrate first.`);
    const parts = blocks(scene.narration, id);
    const total = parts.reduce((n, lines) => n + lines.join(" ").length, 0);
    let start = at;
    for (const lines of parts) {
      const end = start + (scene.audioSeconds * lines.join(" ").length) / total;
      cues.push({fragment: fragment.id, scene: id, start: round(start), end: round(end), lines});
      start = end;
    }
    at += sceneSeconds(scene);
  }
}

const json = JSON.stringify({cues}, null, 2) + "\n";
if (process.argv.includes("--stdout")) {
  process.stdout.write(json);
} else {
  const out = join(src, "captions.json");
  writeFileSync(out + ".tmp", json);
  renameSync(out + ".tmp", out);
  console.log(`Wrote ${cues.length} cues to video/src/captions.json.`);
  console.log("Play the fragments in Remotion Studio to check them, then commit video/src/captions.json.");
}
