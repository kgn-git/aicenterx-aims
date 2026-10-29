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

/** Greedy line filling: as many whole words per line as fit, at most LINES lines per cue, a sentence never shared. */
function blocks(narration) {
  const out = [];
  for (const sentence of narration.match(/[^.!?]+[.!?]+/g) ?? [narration]) {
    let lines = [];
    let line = "";
    for (const word of sentence.trim().split(/\s+/)) {
      if (line && (line + " " + word).length > LINE) {
        lines.push(line);
        line = word;
        if (lines.length === LINES) {
          out.push(lines);
          lines = [];
        }
      } else {
        line = line ? line + " " + word : word;
      }
    }
    lines.push(line);
    out.push(lines);
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
