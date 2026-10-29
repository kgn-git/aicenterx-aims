// Voices the narration with OpenAI text-to-speech, one WAV per scene in public/audio/, and records each clip's
// length in src/timeline.json as audioSeconds:
//   npm run video:narrate                    every fragment
//   npm run video:narrate -- f2-risks        one fragment, so a bad clip can be remade alone
//   npm run video:narrate -- --samples       the hook in each candidate voice, to out/samples/, to choose a voice
// It fails closed: a missing setting, a refused request or a failed write leaves every clip and the timeline as
// they were, and no message carries the key, a header or a stack trace.
import {randomBytes} from "node:crypto";
import {mkdirSync, readFileSync, renameSync, rmSync, writeFileSync} from "node:fs";
import {dirname, join} from "node:path";
import {fileURLToPath} from "node:url";

const VOICE = "marin";
const SAMPLE_VOICES = ["marin", "cedar", "fable"];
const INSTRUCTIONS =
  "Speak calm, warm, standard British English at a natural, steady documentary pace: clear, not slow. " +
  "Say MIT as the letters M-I-T, CV as C-V, EU as E-U, AI as A-I, and AI Center X as A-I Centre Ex.";
const RATE = 24000;

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const timelinePath = join(root, "src", "timeline.json");
const compositions = JSON.parse(readFileSync(join(root, "src", "compositions.json"), "utf8"));

class Refusal extends Error {}

const fail = (message) => {
  console.error(message);
  process.exit(1);
};

function wav(pcm) {
  const header = Buffer.alloc(44);
  header.write("RIFF", 0);
  header.writeUInt32LE(36 + pcm.length, 4);
  header.write("WAVEfmt ", 8);
  header.writeUInt32LE(16, 16);
  header.writeUInt16LE(1, 20);
  header.writeUInt16LE(1, 22);
  header.writeUInt32LE(RATE, 24);
  header.writeUInt32LE(RATE * 2, 28);
  header.writeUInt16LE(2, 32);
  header.writeUInt16LE(16, 34);
  header.write("data", 36);
  header.writeUInt32LE(pcm.length, 40);
  return Buffer.concat([header, pcm]);
}

const refusal = (status) =>
  status === 401
    ? "OpenAI did not accept the key. Check OPENAI_API_KEY in .env.local."
    : status === 403
      ? "OpenAI says the key's project may not use this model (HTTP 403). Allow OPENAI_TTS_MODEL in the project's " +
        "model settings on platform.openai.com, or use a key from a project that has it."
      : status === 429
        ? "OpenAI is limiting requests or the account's quota is used up. Wait a minute or check billing, then run again."
        : status >= 500
          ? `OpenAI had a server error (HTTP ${status}). Run again in a minute.`
          : `OpenAI refused the request (HTTP ${status}). Check OPENAI_TTS_MODEL and the voice name.`;

async function speak(text, voice, key, model) {
  let res;
  try {
    res = await fetch("https://api.openai.com/v1/audio/speech", {
      method: "POST",
      headers: {Authorization: `Bearer ${key}`, "Content-Type": "application/json"},
      body: JSON.stringify({model, voice, input: text, instructions: INSTRUCTIONS, response_format: "pcm"}),
    });
  } catch {
    throw new Refusal("OpenAI could not be reached. Check the network connection, then run again.");
  }
  if (!res.ok) throw new Refusal(refusal(res.status));
  const pcm = Buffer.from(await res.arrayBuffer());
  if (pcm.length === 0 || pcm.length % 2) throw new Refusal("OpenAI returned audio that is not 16-bit PCM.");
  return pcm;
}

/** Writes every file under a temporary name first, then renames them all, so a failure replaces nothing. */
function commit(files) {
  const tag = randomBytes(4).toString("hex");
  const staged = [];
  try {
    for (const [path, data] of files) {
      mkdirSync(dirname(path), {recursive: true});
      writeFileSync(`${path}.${tag}.tmp`, data);
      staged.push(path);
    }
  } catch {
    staged.forEach((path) => rmSync(`${path}.${tag}.tmp`, {force: true}));
    throw new Refusal("A clip could not be written, so nothing was changed. Check the disk and run again.");
  }
  staged.forEach((path) => renameSync(`${path}.${tag}.tmp`, path));
}

/** The timeline text with each scene's audioSeconds line set, leaving the rest of the hand-laid file as it is. */
function withAudioSeconds(text, seconds) {
  let out = text;
  for (const [id, value] of Object.entries(seconds)) {
    const scene = new RegExp(`("id": "${id}",\\s*\\n(\\s*)"seconds": [\\d.]+,)(\\s*\\n\\s*"audioSeconds": [\\d.]+,)?`);
    out = out.replace(scene, (_, head, indent) => `${head}\n${indent}"audioSeconds": ${value},`);
  }
  const parsed = JSON.parse(out).scenes;
  if (!Object.entries(seconds).every(([id, v]) => parsed.find((s) => s.id === id)?.audioSeconds === v)) {
    throw new Refusal("timeline.json is not laid out as expected, so nothing was changed.");
  }
  return out;
}

async function main() {
  const args = process.argv.slice(2);
  const ids = Object.values(compositions);
  const samples = args.length === 1 && args[0] === "--samples";
  if (args.length > 1 || (args.length === 1 && !samples && !ids.includes(args[0]))) {
    fail(`Name one fragment to narrate, or none for all: ${ids.join(", ")}. Or run with --samples to compare voices.`);
  }
  const key = process.env.OPENAI_API_KEY;
  const model = process.env.OPENAI_TTS_MODEL;
  if (!key) fail("OPENAI_API_KEY is not set. Copy .env.example to .env.local at the repo root and add your key.");
  if (!model) fail("OPENAI_TTS_MODEL is not set. Copy it from .env.example into .env.local.");

  const text = readFileSync(timelinePath, "utf8");
  const timeline = JSON.parse(text);
  if (samples) {
    const hook = timeline.scenes[0];
    const files = [];
    for (const voice of SAMPLE_VOICES) {
      files.push([join(root, "out", "samples", `${voice}.wav`), wav(await speak(hook.narration, voice, key, model))]);
    }
    commit(files);
    console.log(`Wrote ${SAMPLE_VOICES.length} samples of the ${hook.id} scene to video/out/samples/.`);
    console.log("Listen, then set VOICE in video/scripts/narrate.mjs to the chosen name.");
    return;
  }
  if (!VOICE) fail("No voice is chosen yet. Run npm run video:narrate -- --samples, then set VOICE in narrate.mjs.");

  const fragmentIds = args.length ? [Object.keys(compositions).find((k) => compositions[k] === args[0])] : null;
  const chosen = timeline.fragments.filter((f) => !fragmentIds || fragmentIds.includes(f.id)).flatMap((f) => f.scenes);
  const files = [];
  const seconds = {};
  for (const id of chosen) {
    const scene = timeline.scenes.find((s) => s.id === id);
    const pcm = await speak(scene.narration, VOICE, key, model);
    seconds[id] = Math.round((pcm.length / (RATE * 2)) * 1000) / 1000;
    files.push([join(root, "public", "audio", `${id}.wav`), wav(pcm)]);
    const pace = scene.narration.split(/\s+/).length / seconds[id];
    console.log(`${id}: ${seconds[id]} s, ${pace.toFixed(2)} words a second, planned ${scene.seconds} s`);
  }
  files.push([timelinePath, withAudioSeconds(text, seconds)]);
  commit(files);
  console.log(`Wrote ${chosen.length} clips to video/public/audio/ and their lengths to timeline.json.`);
  console.log("Listen to each clip, then run npm run video:cues to rebuild the captions.");
}

// Only messages written for the producer are shown; anything else could carry request details. The exit code is
// set rather than forced, because exiting while a request's socket is still closing aborts Node on Windows.
main().catch((err) => {
  console.error(err instanceof Refusal ? err.message : "Narration stopped unexpectedly. Check video/public/audio and timeline.json with git status before running again.");
  process.exitCode = 1;
});
