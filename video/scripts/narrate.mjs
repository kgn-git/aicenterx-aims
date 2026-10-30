// Voices the narration with Deepgram text-to-speech, one WAV per scene in public/audio/, and records each clip's
// length in src/timeline.json as audioSeconds:
//   npm run video:narrate                    every scene, in one continuous take cut at the scene pauses
//   npm run video:narrate -- f2-risks        one fragment, so a bad clip can be remade alone
//   npm run video:narrate -- problem         one scene, leaving the approved clips around it untouched
//   npm run video:narrate -- --samples       the hook, mitigations and close in each candidate voice, to out/samples/
// It fails closed: a missing setting or a refused request changes nothing, every file is staged before any is
// replaced, and no message carries the key, a header or a stack trace.
import {randomBytes} from "node:crypto";
import {mkdirSync, readFileSync, renameSync, rmSync, writeFileSync} from "node:fs";
import {dirname, join} from "node:path";
import {fileURLToPath} from "node:url";
import {splitTake} from "./take.mjs";

const VOICE = "flux-sienna-en";
const SAMPLE_VOICES = ["flux-colin-en", "flux-kit-en", "flux-jack-en", "flux-sienna-en"];
// Deepgram's Flux voices take no speaking instructions and no SSML; pace and liveliness are these two settings.
const SPEED = 1;
const EXPRESSIVITY = 1;
// Read letter by letter when SPELL is set, for a voice that stumbles over acronyms; the captions keep the names.
const SPELLED = [["EU AI Act", "E-U A-I Act"], ["MIT", "M-I-T"]];
const SPELL = false;
const TRANSCRIBE_MODEL = "nova-3";
const RATE = 24000;
// Two minutes of audio, above the whole take, so a runaway reply cannot exhaust memory.
const MAX_BYTES = RATE * 2 * 120;
const TIMEOUT_MS = 120000;

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const timelinePath = join(root, "src", "timeline.json");

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
  status === 401 || status === 403
    ? "Deepgram did not accept the key. Check DEEPGRAM_API_KEY in .env.local."
    : status === 429
      ? "Deepgram is limiting requests or the account's credit is used up. Wait a minute or check the console, then run again."
      : status >= 500
        ? `Deepgram had a server error (HTTP ${status}). Run again in a minute.`
        : `Deepgram refused the request (HTTP ${status}). Check the voice name and the settings in narrate.mjs.`;

/** The take's words with their start and end in seconds, from Deepgram's transcription of the take. */
async function hear(pcm, key) {
  let body;
  try {
    const res = await fetch(`https://api.deepgram.com/v1/listen?model=${TRANSCRIBE_MODEL}&language=en&smart_format=true`, {
      method: "POST",
      headers: {Authorization: `Token ${key}`, "Content-Type": "audio/wav"},
      body: wav(pcm),
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
    if (!res.ok) throw new Refusal(refusal(res.status));
    body = await res.json();
  } catch (err) {
    if (err instanceof Refusal) throw err;
    throw new Refusal("Deepgram's transcription could not be reached or read, so nothing was changed. Run again.");
  }
  const words = body?.results?.channels?.[0]?.alternatives?.[0]?.words;
  if (!Array.isArray(words)) throw new Refusal("Deepgram's transcription has no word timings, so nothing was changed.");
  return words.map((w) => ({word: w.punctuated_word ?? w.word, start: w.start, end: w.end}));
}

/** The text as the voice should read it: acronyms spelled out when `spelled` is set. */
const spoken = (text, spelled) =>
  spelled ? SPELLED.reduce((out, [name, letters]) => out.split(name).join(letters), text) : text;

async function speak(text, voice, key, spelled = false) {
  const query = new URLSearchParams({
    model: voice, encoding: "linear16", sample_rate: String(RATE), container: "none",
    speed: String(SPEED), expressivity: String(EXPRESSIVITY),
  });
  let pcm;
  try {
    const res = await fetch(`https://api.deepgram.com/v2/speak?${query}`, {
      method: "POST",
      headers: {Authorization: `Token ${key}`, "Content-Type": "application/json"},
      body: JSON.stringify({text: spoken(text, spelled)}),
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
    if (!res.ok) throw new Refusal(refusal(res.status));
    if (Number(res.headers.get("content-length")) > MAX_BYTES) throw new Refusal("Deepgram's reply was too long.");
    pcm = Buffer.from(await res.arrayBuffer());
  } catch (err) {
    if (err instanceof Refusal) throw err;
    throw new Refusal("Deepgram could not be reached or did not answer in time, so nothing was changed. Run again.");
  }
  if (pcm.length === 0 || pcm.length % 2 || pcm.length > MAX_BYTES) {
    throw new Refusal("Deepgram returned audio that is not a 16-bit PCM clip, so nothing was changed. Run again.");
  }
  return pcm;
}

/** Writes every file under a temporary name, then renames them with the timeline last. A failed write replaces
 *  nothing; a failed rename names what it replaced, and running the same command again makes the set consistent. */
function commit(files) {
  const tag = randomBytes(4).toString("hex");
  const staged = [];
  const drop = () => staged.forEach((path) => rmSync(`${path}.${tag}.tmp`, {force: true}));
  try {
    for (const [path, data] of files) {
      mkdirSync(dirname(path), {recursive: true});
      staged.push(path);
      writeFileSync(`${path}.${tag}.tmp`, data);
    }
  } catch {
    drop();
    throw new Refusal("A file could not be written, so nothing was changed. Check the disk and run again.");
  }
  const done = [];
  try {
    for (const path of staged) {
      renameSync(`${path}.${tag}.tmp`, path);
      done.push(path);
    }
  } catch {
    drop();
    const names = done.map((p) => p.slice(root.length + 1)).join(", ") || "nothing";
    throw new Refusal(
      `A file could not be replaced, perhaps because a player has it open. Replaced so far: ${names}. ` +
        "Close any player and run the same command again.",
    );
  }
}

/** The timeline text with each scene's audioSeconds line set, leaving the rest of the hand-laid file as it is. */
function withAudioSeconds(text, seconds) {
  const eol = text.includes("\r\n") ? "\r\n" : "\n";
  let out = text;
  for (const [id, value] of Object.entries(seconds)) {
    const scene = new RegExp(`("id": "${id}",\\s*\\r?\\n(\\s*)"seconds": [\\d.]+,)(\\s*\\r?\\n\\s*"audioSeconds": [\\d.]+,)?`);
    out = out.replace(scene, (_, head, indent) => `${head}${eol}${indent}"audioSeconds": ${value},`);
  }
  const parsed = JSON.parse(out).scenes;
  if (!Object.entries(seconds).every(([id, v]) => parsed.find((s) => s.id === id)?.audioSeconds === v)) {
    throw new Refusal(
      'timeline.json is not laid out as expected, so nothing was changed. Keep "audioSeconds" on the line after ' +
        '"seconds" in each scene, then run again.',
    );
  }
  return out;
}

async function main() {
  const compositions = JSON.parse(readFileSync(join(root, "src", "compositions.json"), "utf8"));
  const args = process.argv.slice(2);
  const ids = Object.values(compositions);
  const text = readFileSync(timelinePath, "utf8");
  const timeline = JSON.parse(text);
  const sceneIds = timeline.scenes.map((s) => s.id);
  const samples = args.length === 1 && args[0] === "--samples";
  if (args.length > 1 || (args.length === 1 && !samples && !ids.includes(args[0]) && !sceneIds.includes(args[0]))) {
    const cause = args.length > 1 ? "Give at most one fragment or scene." : `"${args[0]}" is not a fragment or scene.`;
    fail(`${cause} Name one of ${ids.join(", ")}, or a scene (${sceneIds.join(", ")}), or none for all, or --samples to compare voices.`);
  }
  const key = process.env.DEEPGRAM_API_KEY;
  if (!key) fail("DEEPGRAM_API_KEY is not set. Copy .env.example to .env.local at the repo root and add your key.");

  const bad = timeline.scenes.find((s) => !/^[a-z0-9-]+$/.test(s.id));
  if (bad) fail(`Scene id "${bad.id}" must use only lower-case letters, digits and hyphens, as it names a file.`);
  if (samples) {
    // The hook and the close carry the tone; the mitigations line carries the acronyms.
    const text = ["hook", "mitigations", "end"].map((id) => timeline.scenes.find((s) => s.id === id).narration).join("\n\n");
    const files = [];
    for (const voice of SAMPLE_VOICES) {
      files.push([join(root, "out", "samples", `${voice}.wav`), wav(await speak(text, voice, key))]);
      files.push([join(root, "out", "samples", `${voice}-spelled.wav`), wav(await speak(text, voice, key, true))]);
    }
    commit(files);
    console.log(`Wrote ${files.length} samples of the hook, mitigations and close to video/out/samples/.`);
    console.log("Listen, then set VOICE in video/scripts/narrate.mjs to the chosen name.");
    return;
  }

  const fragmentId = Object.keys(compositions).find((k) => compositions[k] === args[0]);
  const chosen = sceneIds.includes(args[0])
    ? [args[0]]
    : timeline.fragments.filter((f) => !args.length || f.id === fragmentId).flatMap((f) => f.scenes);
  const files = [];
  const seconds = {};
  const scenes = chosen.map((id) => timeline.scenes.find((s) => s.id === id));
  let takes = null;
  if (!args.length) {
    const script = scenes.map((s) => s.narration).join("\n\n");
    const take = await speak(script, VOICE, key, SPELL);
    const words = await hear(take, key);
    try {
      takes = splitTake(take, scenes.map((s) => s.narration), words);
    } catch (err) {
      throw new Refusal(`${err.message} Nothing was changed. Run again, or remake one fragment at a time.`);
    }
  }
  for (const [i, scene] of scenes.entries()) {
    const id = scene.id;
    const pcm = takes ? takes[i] : await speak(scene.narration, VOICE, key, SPELL);
    seconds[id] = Math.round((pcm.length / (RATE * 2)) * 1000) / 1000;
    files.push([join(root, "public", "audio", `${id}.wav`), wav(pcm)]);
    const pace = scene.narration.split(/\s+/).length / seconds[id];
    console.log(`${id}: ${seconds[id]} s, ${pace.toFixed(2)} words a second, planned ${scene.seconds} s`);
  }
  files.push([timelinePath, withAudioSeconds(text, seconds)]);
  commit(files);
  const clips = chosen.length === 1 ? "1 clip" : `${chosen.length} clips`;
  console.log(`Wrote ${clips} to video/public/audio/ and the lengths to timeline.json.`);
  console.log("Listen to each clip, then run npm run video:cues to rebuild the captions.");
}

// Only messages written for the producer are shown; anything else could carry request details. The exit code is
// set rather than forced, because exiting while a request's socket is still closing aborts Node on Windows.
main().catch((err) => {
  console.error(
    err instanceof Refusal
      ? err.message
      : "Narration stopped unexpectedly. Check video/public/audio and timeline.json with git status before running again.",
  );
  process.exitCode = 1;
});
