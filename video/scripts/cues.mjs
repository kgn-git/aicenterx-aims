// Builds the caption cues, src/captions.json, from each scene's narration and audioSeconds:
//   npm run video:cues            writes src/captions.json
//   node scripts/cues.mjs --stdout  prints it instead, for the freshness check in the captions test
// There are no word timestamps, so each cue's share of its clip follows its share of the scene's characters.
import {readFileSync, renameSync, writeFileSync} from "node:fs";
import {dirname, join} from "node:path";
import {fileURLToPath} from "node:url";
import {sceneSeconds} from "../src/timing.mjs";

const LINE = 42;
const LINES = 2;
const src = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const timeline = JSON.parse(readFileSync(join(src, "timeline.json"), "utf8"));
const scenes = new Map(timeline.scenes.map((s) => [s.id, s]));
const round = (x) => Math.round(x * 1000) / 1000;

/** The two lines of one cue, split where the longer line is shortest, or null when the words cannot fit. */
function twoLines(words) {
  const one = words.join(" ");
  if (one.length <= LINE) return [one];
  let best = null;
  for (let i = 1; i < words.length; i++) {
    const pair = [words.slice(0, i).join(" "), words.slice(i).join(" ")];
    const longest = Math.max(...pair.map((l) => l.length));
    if (longest <= LINE && (!best || longest < best.longest)) best = {pair, longest};
  }
  return best?.pair ?? null;
}

/** Each sentence split into the fewest cues that fit, with the words shared as evenly as possible by length, so no
 *  cue holds a stray word or two and no cue spans two sentences. */
function blocks(narration) {
  const out = [];
  for (const sentence of narration.match(/[^.!?]+[.!?]+/g) ?? [narration]) {
    const words = sentence.trim().split(/\s+/);
    for (let n = Math.ceil(sentence.trim().length / (LINE * LINES)); n <= words.length; n++) {
      const target = sentence.trim().length / n;
      const chunks = [];
      let chunk = [];
      for (const word of words) {
        chunk.push(word);
        if (chunks.length < n - 1 && chunk.join(" ").length >= target) {
          chunks.push(chunk);
          chunk = [];
        }
      }
      if (chunk.length) chunks.push(chunk);
      const split = chunks.map(twoLines);
      if (split.every(Boolean)) {
        out.push(...split);
        break;
      }
    }
  }
  return out;
}

const cues = [];
for (const fragment of timeline.fragments) {
  let at = 0;
  for (const id of fragment.scenes) {
    const scene = scenes.get(id);
    const parts = blocks(scene.narration);
    const total = parts.reduce((n, lines) => n + lines.join(" ").length, 0);
    let start = at;
    for (const lines of parts) {
      const end = start + ((scene.audioSeconds ?? 0) * lines.join(" ").length) / total;
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
}
