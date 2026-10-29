// Renders one fragment to out/fragments/<id>.mp4:  npm run video:render:fragment -- f2-risks
// The id reaches a command line and an output path, so only an id listed in src/compositions.json is accepted, and
// the CLI is started with an argument vector, never through a shell.
import {spawnSync} from "node:child_process";
import {existsSync, mkdirSync, readFileSync} from "node:fs";
import {dirname, join} from "node:path";
import {fileURLToPath} from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const ids = Object.values(JSON.parse(readFileSync(join(root, "src", "compositions.json"), "utf8")));
const id = process.argv[2];
const install = "Install the video project first: npm --prefix video ci";

if (process.argv.length !== 3 || !ids.includes(id)) {
  console.error(`Name one fragment to render: ${ids.join(", ")}.`);
  console.error("For example: npm run video:render:fragment -- f2-risks");
  process.exit(1);
}

const cli = join(root, "node_modules", "@remotion", "cli", "remotion-cli.js");
if (!existsSync(cli)) {
  console.error(`Remotion is not installed, so ${id} was not rendered. ${install}`);
  process.exit(1);
}

const out = join(root, "out", "fragments", `${id}.mp4`);
mkdirSync(dirname(out), {recursive: true});
const run = spawnSync(process.execPath, [cli, "render", "src/index.ts", id, out], {cwd: root, stdio: "inherit"});
if (run.error) {
  console.error(`Remotion could not start, so ${id} was not rendered. ${install}`);
}
process.exit(run.status ?? 1);
