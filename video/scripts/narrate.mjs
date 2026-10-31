// Voices the narration with ElevenLabs text-to-speech, one WAV per scene in public/audio/, and records each clip's
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
import {splitTake, wordsFromAlignment} from "./take.mjs";

// Matilda, the voice the user picked from the samples.
const VOICE = "XrExE9yKIg1WjnnlVkGX";
const SAMPLE_VOICES = {matilda: VOICE, alice: "Xb7hH8MSUJpSbSDYk0k2", george: "JBFqnCBsd6RMkjVDRZzb", brian: "nPczCjzI2devNBz1zQrb"};
// The most expressive model; it takes no speed setting, so pace comes from the shortened pauses in take.mjs.
const MODEL = "eleven_v3";
const STABILITY = 0.5;
const RATE = 24000;
// Two minutes of audio, above the whole take, so a runaway reply cannot exhaust memory.
const MAX_BYTES = RATE * 2 * 120;
// The audio arrives as base64 inside JSON beside the per-character timings: a third larger, plus the timings.
const MAX_JSON = Math.ceil((MAX_BYTES * 4) / 3) + 2_000_000;
const TIMEOUT_MS = 180000;

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
  status === 401
    ? "ElevenLabs did not accept the key. Check ELEVENLABS_API_KEY in .env.local, and that it may use text to speech."
    : status === 402
      ? "The ElevenLabs account has no credit left. Add credit in the ElevenLabs console, then run again."
    : status === 422
      ? "ElevenLabs refused the text or the settings (HTTP 422). Check the voice and the settings in narrate.mjs."
    : status === 429
      ? "ElevenLabs is limiting requests or the account's credit is used up. Wait a minute or check the console, then run again."
      : status >= 500
        ? `ElevenLabs had a server error (HTTP ${status}). Run again in a minute.`
        : `ElevenLabs refused the request (HTTP ${status}). Check the voice and the settings in narrate.mjs.`;

/** The reply's body, refused as soon as it passes `limit` bytes, so a runaway reply cannot exhaust memory whether or
 *  not it announces its length. */
async function readCapped(res, limit, what) {
  const chunks = [];
  let size = 0;
  for await (const chunk of res.body) {
    size += chunk.length;
    if (size > limit) throw new Refusal(`ElevenLabs' ${what} was too long, so nothing was changed.`);
    chunks.push(chunk);
  }
  return Buffer.concat(chunks);
}

/** The voiced `text` as 16-bit PCM and its words timed from the reply's per-character timings; refused unless the
 *  audio is whole and every word lies inside it, since a bad time would cut a wrong clip silently. */
async function speak(text, voice, key) {
  let reply;
  try {
    const res = await fetch(
      `https://api.elevenlabs.io/v1/text-to-speech/${voice}/with-timestamps?output_format=pcm_${RATE}`,
      {
        method: "POST",
        headers: {"xi-api-key": key, "Content-Type": "application/json"},
        body: JSON.stringify({text, model_id: MODEL, language_code: "en", voice_settings: {stability: STABILITY}}),
        signal: AbortSignal.timeout(TIMEOUT_MS),
      },
    );
    if (!res.ok) throw new Refusal(refusal(res.status));
    reply = await readCapped(res, MAX_JSON, "reply");
  } catch (err) {
    if (err instanceof Refusal) throw err;
    throw new Refusal("ElevenLabs could not be reached or did not answer in time, so nothing was changed. Run again.");
  }
  let body;
  try {
    body = JSON.parse(reply.toString("utf8"));
  } catch {
    throw new Refusal("ElevenLabs' reply could not be read, so nothing was changed. Run again.");
  }
  const pcm = typeof body?.audio_base64 === "string" ? Buffer.from(body.audio_base64, "base64") : Buffer.alloc(0);
  if (pcm.length === 0 || pcm.length % 2 || pcm.length > MAX_BYTES) {
    throw new Refusal("ElevenLabs returned audio that is not a 16-bit PCM clip, so nothing was changed. Run again.");
  }
  let words;
  try {
    words = wordsFromAlignment(body.alignment ?? {});
  } catch {
    throw new Refusal("ElevenLabs' reply has no usable timings, so nothing was changed. Run again.");
  }
  const length = pcm.length / (RATE * 2);
  if (!words.length || words.length > 2 * text.split(/\s+/).length || words.some((w) => w.end > length + 0.5)) {
    throw new Refusal("ElevenLabs' timings do not fit its audio, so nothing was changed. Run again.");
  }
  return {pcm, words};
}

/** One clip per narration in `lines`, cut from a single take of all of them, so the voice keeps one pace. */
async function voice(lines, voiceId, key) {
  const {pcm, words} = await speak(lines.join("\n\n"), voiceId, key);
  try {
    return splitTake(pcm, lines, words);
  } catch (err) {
    throw new Refusal(`${err.message} Nothing was changed. Run again, or remake one fragment at a time.`);
  }
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
  const key = process.env.ELEVENLABS_API_KEY;
  if (!key) fail("ELEVENLABS_API_KEY is not set. Copy .env.example to .env.local at the repo root and add your key.");

  const bad = timeline.scenes.find((s) => !/^[a-z0-9-]+$/.test(s.id));
  if (bad) fail(`Scene id "${bad.id}" must use only lower-case letters, digits and hyphens, as it names a file.`);
  if (samples) {
    // The hook and the close carry the tone; the mitigations line carries the acronyms.
    const lines = ["hook", "mitigations", "end"].map((id) => timeline.scenes.find((s) => s.id === id).narration);
    const files = [];
    for (const [name, id] of Object.entries(SAMPLE_VOICES)) {
      files.push([join(root, "out", "samples", `${name}.wav`), wav(Buffer.concat(await voice(lines, id, key)))]);
    }
    commit(files);
    console.log(`Wrote ${files.length} samples of the hook, mitigations and close to video/out/samples/.`);
    console.log("Listen, then set VOICE in video/scripts/narrate.mjs to the chosen voice.");
    return;
  }

  const fragmentId = Object.keys(compositions).find((k) => compositions[k] === args[0]);
  const chosen = sceneIds.includes(args[0])
    ? [args[0]]
    : timeline.fragments.filter((f) => !args.length || f.id === fragmentId).flatMap((f) => f.scenes);
  const scenes = chosen.map((id) => timeline.scenes.find((s) => s.id === id));
  const clips = await voice(scenes.map((s) => s.narration), VOICE, key);
  const files = [];
  const seconds = {};
  for (const [i, scene] of scenes.entries()) {
    const id = scene.id;
    seconds[id] = Math.round((clips[i].length / (RATE * 2)) * 1000) / 1000;
    files.push([join(root, "public", "audio", `${id}.wav`), wav(clips[i])]);
    const pace = scene.narration.split(/\s+/).length / seconds[id];
    console.log(`${id}: ${seconds[id]} s, ${pace.toFixed(2)} words a second, planned ${scene.seconds} s`);
  }
  files.push([timelinePath, withAudioSeconds(text, seconds)]);
  commit(files);
  const count = chosen.length === 1 ? "1 clip" : `${chosen.length} clips`;
  console.log(`Wrote ${count} to video/public/audio/ and the lengths to timeline.json.`);
  console.log("Listen to each clip, set each scene's seconds to its clip plus its tail, then run npm run video:cues.");
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
