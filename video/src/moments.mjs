// When each scene's moments happen, in seconds from the scene's start: plain functions of the timeline and the
// caption cues, shared by the scenes and, through node, by test/marketing_video_scenes_test.py, so the tests check
// the timings the video plays rather than a copy of them.
import {sceneSeconds} from "./timing.mjs";

// A press of a button or the cursor, down and back up, short and shallow so the click reads without a bounce.
export const PRESS = 0.12;
export const PRESS_SCALE = 0.96;
/** @type {[number, number, number, number]} */
export const CURSOR_EASE = [0.22, 1, 0.36, 1];

/** 1 at a press in `times`, falling to 0 half a PRESS either side. */
export const pressed = (t, times) => Math.max(0, ...times.map((c) => 1 - Math.abs(t - c) / (PRESS / 2)));

/** @typedef {{start: number; end: number; text: string}} Cue */

/** The first cue that says `phrase`. A scene waits for words rather than a cue's position, since rewording a line
 *  re-splits the captions; a missing phrase stops the render instead of silently moving the moment.
 *  @param {Cue[]} cues @param {string} phrase @returns {Cue} */
export const cueWith = (cues, phrase) => {
  const cue = cues.find((c) => c.text.includes(phrase));
  if (!cue) throw new Error(`No caption cue says "${phrase}". Update the scene to the new narration.`);
  return cue;
};

/** When `phrase` starts within the cue that says it, by its share of the cue's characters, as the captions are timed.
 *  @param {Cue[]} cues @param {string} phrase */
export const saidAt = (cues, phrase) => {
  const cue = cueWith(cues, phrase);
  return cue.start + ((cue.end - cue.start) * cue.text.indexOf(phrase)) / cue.text.length;
};

/** When the voice reaches `phrase`, in seconds: the cues share a clip by characters, so a phrase's place in the text
 *  is its place in time, to within a pause. @param {string} narration @param {string} phrase @param {number} end */
export const spokenAt = (narration, phrase, end) => {
  const at = narration.indexOf(phrase);
  if (at < 0) throw new Error(`The narration no longer says "${phrase}", so the scene cannot time its beats.`);
  return (end * at) / narration.length;
};

/** A scene's caption cues with times from the scene's own start, since cue times count from its fragment's start. */
export function sceneCues(captions, timeline, sceneId) {
  const fragment = timeline.fragments.find((f) => f.scenes.includes(sceneId));
  const before = fragment.scenes.slice(0, fragment.scenes.indexOf(sceneId));
  const start = before.reduce((sum, id) => sum + sceneSeconds(timeline.scenes.find((s) => s.id === id)), 0);
  return captions.cues
    .filter((c) => c.fragment === fragment.id && c.scene === sceneId)
    .map((c) => ({start: c.start - start, end: c.end - start, text: c.lines.join(" ")}));
}

const STAGGER = 0.1;
// A card is ticked only once it has landed; ticks, the save and the hand-off follow at a reading pace.
const LANDED = 0.3;
const TICK = 0.35;
const SAVE = 0.6;
const NEXT = 0.6;
const HAND_OFF = 1.0;
// The save's toast fades in over half a second and stays up for TOAST before the cut.
const TOAST_IN = 0.5;
const TOAST = 1.6;

// Only the risks run is shown in full; the later runs land their first card a quarter second after the click.
const STAGES = {
  risks: {click: 0.5, runFrom: 1, runTo: 4, sources: ["MIT AI Risk Repository", "AI Incident Database"], next: true},
  mitigations: {click: 0.35, runFrom: 0.4, runTo: 0.8, sources: ["draft taxonomy", "EU AI Act"], next: true},
  enhancements: {click: 0.35, runFrom: 0.4, runTo: 0.8, sources: [], ticksFrom: "engineering", next: false},
};

/** The moments of a risks, mitigations or enhancements scene: the click, each card landing, the sources named, the
 *  ticks laid under the voice, the save and the hand-off. The ticks start as the voice names the sources, or later
 *  once the cards have landed, and earlier when the hand-off or the toast would otherwise lose its time. */
export function stageMoments(scene, cues, seconds) {
  const stage = STAGES[scene.id];
  const {shown, saved} = scene.dataRefs[scene.id];
  const firstCard = scene.id === "risks" ? stage.runTo + 0.15 : stage.click + 0.25;
  const cards = shown.map((_, i) => firstCard + i * STAGGER);
  const named = stage.sources.map((phrase) => saidAt(cues, phrase));
  const order = saved.map((id) => shown.indexOf(id));
  const landed = Math.max(...order.map((i, k) => cards[i] + LANDED - k * TICK));
  const hold = stage.next ? NEXT + HAND_OFF : TOAST_IN + TOAST;
  const latest = seconds - hold - SAVE - TICK * (saved.length - 1);
  const cue = named.length ? named[0] : saidAt(cues, stage.ticksFrom);
  const first = Math.min(Math.max(landed, cue), latest);
  const ticks = saved.map((_, k) => first + k * TICK);
  const saveAt = ticks[ticks.length - 1] + SAVE;
  return {
    click: stage.click, runFrom: stage.runFrom, runTo: stage.runTo, cards, named, ticks, saveAt,
    nextAt: stage.next ? saveAt + NEXT : null,
  };
}

// How long "Simulate risks" is on screen before the cut, so the hand-off reads even though the line ends late.
const TRIGGER_SHOWN = 1.4;

/** The canvas scene: the blocks are lit as the voice names them, and "Simulate risks" appears once they are, or
 *  earlier when the line runs close to the cut; the cursor drifts in, then reaches it as it glows. */
export function canvasMoments(cues, seconds) {
  const naming = cueWith(cues, "its data");
  const appear = Math.min(naming.end, seconds - TRIGGER_SHOWN);
  return {
    naming: {start: naming.start, end: naming.end}, appear, approach: appear + 0.4, arrive: seconds - 0.4,
    glow: seconds - 1.2,
  };
}

/** The problem scene: the two aims on screen from the start, meeting on "The challenge", lit on "create real value";
 *  the statement gives way to the challenge at its share of the clip. */
export function problemMoments(scene, cues) {
  const [statement, challenge] = scene.onScreen;
  const end = cues[cues.length - 1].end;
  const at = (phrase) => spokenAt(scene.narration, phrase, end);
  return {
    end, split: (end * statement.length) / (statement.length + challenge.length), circles: 0,
    dots: at("The challenge"), meet: at("The challenge") + 0.2, target: at("create real value") + 0.2,
  };
}

// The capabilities the voice names as each lands, in the order the close lists them on screen.
export const KEYWORDS = ["models", "data lineage", "programmes", "architecture", "intelligence"];
const BRAND = "AI Center X";

/** The close: the years collapse into the hour as the voice says it, the message stays up while the payoff is
 *  heard, the portfolio follows "Then scale up", and the brand card and its footer close the video. */
export function closeMoments(scene, cues) {
  const end = cues[cues.length - 1].end;
  const at = (phrase) => spokenAt(scene.narration, phrase, end);
  const beats = ["Three years", "reduced", "less than an hour", "Then scale up", ...KEYWORDS, BRAND];
  const times = beats.map(at);
  if (times.some((x, i) => i && x <= times[i - 1])) {
    throw new Error(`The close's narration must say ${beats.join(", ")} in that order.`);
  }
  const brandAt = at(BRAND);
  return {
    message: at("Three years") + 0.2, collapse: at("reduced"), tallies: at("less than an hour"),
    scaleAt: at("Then scale up") - 0.1, keywords: KEYWORDS.map(at), brandAt, footer: brandAt + 0.3,
  };
}
