// Downloads the pitch's Pexels stock clips listed in src/footage.json into public/footage/, checking each against its
// recorded sha256:  npm run video:footage
// The clips are not ours to redistribute and the repo is public, so they stay out of git; their source and hash are
// committed instead. It fails closed: a clip off Pexels, a malformed hash or a download that does not match changes
// nothing, and no message carries a stack trace. FOOTAGE_PLAN and FOOTAGE_DIR point it elsewhere, for the tests.
import {createHash} from "node:crypto";
import {existsSync, mkdirSync, readFileSync, renameSync, writeFileSync} from "node:fs";
import {dirname, join} from "node:path";
import {fileURLToPath} from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const plan = process.env.FOOTAGE_PLAN ?? join(root, "src", "footage.json");
const folder = process.env.FOOTAGE_DIR ?? join(root, "public", "footage");
// Far above any 1080p stock clip, so a runaway reply cannot exhaust memory.
const MAX_BYTES = 200 * 1024 * 1024;
const TIMEOUT_MS = 180000;

class Refusal extends Error {}

const sha256 = (bytes) => createHash("sha256").update(bytes).digest("hex");

/** Every clip as [id, entry], refusing the whole plan when any entry could fetch from elsewhere or not be checked. */
function clipsOf(text) {
  const clips = Object.entries(JSON.parse(text).clips ?? {});
  for (const [id, c] of clips) {
    if (!/^[a-z][a-z0-9-]*$/.test(id)) throw new Refusal(`Clip id "${id}" must be lower-case letters, digits and hyphens.`);
    if (!new RegExp(`^https://videos\\.pexels\\.com/video-files/${c.pexels}/[\\w.-]+\\.mp4$`).test(c.url ?? "")) {
      throw new Refusal(`Clip "${id}" must come from videos.pexels.com under its Pexels id; nothing was downloaded.`);
    }
    if (!/^[0-9a-f]{64}$/.test(c.sha256 ?? "")) throw new Refusal(`Clip "${id}" needs a 64-character sha256; nothing was downloaded.`);
  }
  return clips;
}

async function download(id, url) {
  const reply = await fetch(url, {signal: AbortSignal.timeout(TIMEOUT_MS)});
  if (!reply.ok) throw new Refusal(`Pexels answered ${reply.status} for clip "${id}". Try again later.`);
  const bytes = Buffer.from(await reply.arrayBuffer());
  if (bytes.length > MAX_BYTES) throw new Refusal(`Clip "${id}" is larger than ${MAX_BYTES / 1024 / 1024} MB.`);
  return bytes;
}

async function main() {
  const clips = clipsOf(readFileSync(plan, "utf8"));
  const fetched = [];
  for (const [id, c] of clips) {
    const target = join(folder, `${id}.mp4`);
    if (existsSync(target) && sha256(readFileSync(target)) === c.sha256) continue;
    const bytes = await download(id, c.url);
    if (sha256(bytes) !== c.sha256) {
      throw new Refusal(`Clip "${id}" from Pexels no longer matches its recorded sha256, so it was not saved. ` +
        "Check the clip on pexels.com, then record its new hash in video/src/footage.json.");
    }
    fetched.push([target, bytes]);
  }
  mkdirSync(folder, {recursive: true});
  for (const [target, bytes] of fetched) {
    const staged = `${target}.part`;
    writeFileSync(staged, bytes);
    renameSync(staged, target);
  }
  console.log(`${fetched.length} clip(s) downloaded, ${clips.length - fetched.length} already in place, in ${folder}.`);
}

// Only messages written for the producer are shown; the exit code is set rather than forced, because exiting while a
// socket is still closing aborts Node on Windows.
main().catch((err) => {
  console.error(err instanceof Refusal ? err.message : "The footage download stopped unexpectedly; nothing was changed.");
  process.exitCode = 1;
});
