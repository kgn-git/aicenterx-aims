// Renders the final marketing video in one piece, so each scene crossfades into the next, to
// out/cv-screening-journey.mp4:  npm run video:assemble
// The fragments stay for review; this renders the same scenes through the CvScreeningJourney composition, then
// checks the result and fails closed on anything off.
import {spawnSync} from "node:child_process";
import {existsSync, mkdirSync, renameSync, rmSync} from "node:fs";
import {dirname, join} from "node:path";
import {fileURLToPath} from "node:url";

// The user's tolerance until the combined review; the plan targets 60 s.
const MAX_SECONDS = 75;
const WIDTH = 1920;
const HEIGHT = 1080;

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const out = process.env.VIDEO_OUT ?? join(root, "out");
const cli = join(root, "node_modules", "@remotion", "cli", "remotion-cli.js");

const fail = (message) => {
  console.error(message);
  process.exit(1);
};

if (process.argv.length > 2) fail("This takes no arguments. Run: npm run video:assemble");
if (!existsSync(cli)) fail("Remotion is not installed, so nothing was rendered. Install it first: npm --prefix video ci");

const tool = (name, args, inherit) =>
  spawnSync(process.execPath, [cli, name, ...args], {cwd: root, encoding: "utf8", stdio: inherit ? "inherit" : "pipe"});
const target = join(out, "cv-screening-journey.mp4");
const staged = `${target}.tmp.mp4`;
mkdirSync(dirname(target), {recursive: true});
const render = tool("render", ["src/index.ts", "CvScreeningJourney", staged], true);
if (render.status !== 0) {
  rmSync(staged, {force: true});
  fail("Remotion could not render the video, so nothing was written. Check the scenes in Remotion Studio.");
}

const probe = tool("ffprobe", ["-v", "error", "-show_entries", "format=duration:stream=codec_type,codec_name,width,height",
  "-of", "json", staged]);
let info;
try {
  info = JSON.parse(probe.stdout);
} catch {
  rmSync(staged, {force: true});
  fail("ffprobe could not read the rendered video, so it was not kept.");
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
  fail(`The rendered video was not kept: ${problems.join("; ")}.`);
}
renameSync(staged, target);
console.log("Rendered video/out/cv-screening-journey.mp4.");
console.log(`Check passed: ${seconds.toFixed(2)} s, ${video.width}x${video.height}, ${video.codec_name} with ${audio.codec_name}.`);
