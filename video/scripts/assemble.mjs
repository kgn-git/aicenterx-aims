// Joins the five rendered fragments, in order, into out/cv-screening-journey.mp4:  npm run video:assemble
// The fragments share one encoding, so ffmpeg's concat demuxer copies them without re-encoding, and a remade
// fragment needs only this step again. The result is then checked, and the script fails closed on anything off.
import {spawnSync} from "node:child_process";
import {existsSync, readFileSync, renameSync, rmSync, writeFileSync} from "node:fs";
import {dirname, join} from "node:path";
import {fileURLToPath} from "node:url";

// The user's tolerance until the combined review; the plan targets 60 s.
const MAX_SECONDS = 72;
const WIDTH = 1920;
const HEIGHT = 1080;

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const out = process.env.VIDEO_OUT ?? join(root, "out");
const ids = Object.values(JSON.parse(readFileSync(join(root, "src", "compositions.json"), "utf8")));
const cli = join(root, "node_modules", "@remotion", "cli", "remotion-cli.js");

const fail = (message) => {
  console.error(message);
  process.exit(1);
};

const missing = ids.filter((id) => !existsSync(join(out, "fragments", `${id}.mp4`)));
if (missing.length) {
  fail(`Fragment ${missing.join(", ")} is not rendered, so nothing was joined. ` +
    `Render it first: npm run video:render:fragment -- ${missing[0]}`);
}
if (!existsSync(cli)) fail("Remotion is not installed, so nothing was joined. Install it first: npm --prefix video ci");

const tool = (name, args) => spawnSync(process.execPath, [cli, name, ...args], {cwd: root, encoding: "utf8"});
const list = join(out, "fragments.txt");
const target = join(out, "cv-screening-journey.mp4");
const staged = `${target}.tmp.mp4`;
// Paths in a concat list are read relative to the list, so it sits beside the fragments' folder.
writeFileSync(list, ids.map((id) => `file 'fragments/${id}.mp4'`).join("\n") + "\n");
const joined = tool("ffmpeg", ["-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", list,
  "-c", "copy", "-movflags", "+faststart", staged]);
rmSync(list, {force: true});
if (joined.status !== 0) {
  rmSync(staged, {force: true});
  fail("ffmpeg could not join the fragments, so nothing was written. Render them again with the same settings.");
}

const probe = tool("ffprobe", ["-v", "error", "-show_entries", "format=duration:stream=codec_type,codec_name,width,height",
  "-of", "json", staged]);
let info;
try {
  info = JSON.parse(probe.stdout);
} catch {
  rmSync(staged, {force: true});
  fail("ffprobe could not read the joined video, so it was not kept.");
}
const video = info.streams.find((s) => s.codec_type === "video");
const audio = info.streams.find((s) => s.codec_type === "audio");
const seconds = Number(info.format.duration);
const problems = [
  !(seconds > 0 && seconds <= MAX_SECONDS) && `it runs ${seconds.toFixed(2)} s, more than ${MAX_SECONDS} s`,
  !(video?.width === WIDTH && video?.height === HEIGHT) && `it is ${video?.width}x${video?.height}, not ${WIDTH}x${HEIGHT}`,
  video?.codec_name !== "h264" && `its video is ${video?.codec_name}, not h264`,
  audio?.codec_name !== "aac" && `its audio is ${audio?.codec_name ?? "missing"}, not aac`,
].filter(Boolean);
if (problems.length) {
  rmSync(staged, {force: true});
  fail(`The joined video was not kept: ${problems.join("; ")}.`);
}
renameSync(staged, target);
console.log(`Joined ${ids.length} fragments into video/out/cv-screening-journey.mp4.`);
console.log(`Check passed: ${seconds.toFixed(2)} s, ${video.width}x${video.height}, ${video.codec_name} with ${audio.codec_name}.`);
