// Prints the trace scene's rows from src/trace.mjs, so the Python test checks the graph the scene draws.
import {readFileSync} from "node:fs";
import {traceRows} from "../src/trace.mjs";

const read = (path) => JSON.parse(readFileSync(new URL(path, import.meta.url), "utf8"));
console.log(JSON.stringify(traceRows({
  timeline: read("../src/timeline.json"),
  enhancements: read("../data/model_enhancements.json"),
  labels: read("../data/trace_labels.json"),
  risks: read("../../tools/data/risk_suggestions.json"),
  mitigations: read("../../tools/data/mitigation_suggestions.json"),
})));
