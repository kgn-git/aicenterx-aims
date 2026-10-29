// Prints {scene id: seconds on screen} from src/timing.mjs, so the Python tests read the rule instead of copying it.
import {readFileSync} from "node:fs";
import {sceneSeconds} from "../src/timing.mjs";

const timeline = JSON.parse(readFileSync(new URL("../src/timeline.json", import.meta.url), "utf8"));
console.log(JSON.stringify(Object.fromEntries(timeline.scenes.map((s) => [s.id, sceneSeconds(s)]))));
