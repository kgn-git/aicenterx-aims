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
// The next button glows, and the save's toast stays fully shown, until the 0.3 s crossfade out of the scene begins.
const HAND_OFF = 1.2;
const TOAST_IN = 0.5;
const TOAST = 1.9;

// Only the risks run is shown in full; the later runs land their first card a quarter second after the click.
const STAGES = {
  risks: {
    click: 0.5, runFrom: 1, runTo: 4, firstCard: 4.15, sources: ["MIT AI Risk Repository", "AI Incident Database"],
    next: true,
  },
  mitigations: {click: 0.35, runFrom: 0.4, runTo: 0.8, firstCard: 0.6, sources: ["draft taxonomy", "EU AI Act"], next: true},
  enhancements: {click: 0.35, runFrom: 0.4, runTo: 0.8, firstCard: 0.6, sources: [], ticksFrom: "engineering", next: false},
};

/** The moments of a risks, mitigations or enhancements scene: the click, each card landing, the sources named, the
 *  ticks laid under the voice, the save and the hand-off. The ticks start as the voice names the sources, or later
 *  once the cards have landed, and earlier when the hand-off or the toast would otherwise lose its time; a scene too
 *  short for all of that stops the render rather than tick cards that are not there yet. */
export function stageMoments(scene, cues, seconds) {
  const stage = STAGES[scene.id];
  const {shown, saved} = scene.dataRefs[scene.id];
  const cards = shown.map((_, i) => stage.firstCard + i * STAGGER);
  const named = stage.sources.map((phrase) => saidAt(cues, phrase));
  const order = saved.map((id) => shown.indexOf(id));
  const landed = Math.max(...order.map((i, k) => cards[i] + LANDED - k * TICK));
  const hold = stage.next ? NEXT + HAND_OFF : TOAST_IN + TOAST;
  const latest = seconds - hold - SAVE - TICK * (saved.length - 1);
  if (latest < landed) {
    throw new Error(
      `The ${scene.id} scene needs ${(landed - latest).toFixed(2)} s more to tick, save and hand off. Lengthen its line.`,
    );
  }
  const cue = named.length ? named[0] : saidAt(cues, stage.ticksFrom);
  const first = Math.min(Math.max(landed, cue), latest);
  const ticks = saved.map((_, k) => first + k * TICK);
  const saveAt = ticks[ticks.length - 1] + SAVE;
  return {
    click: stage.click, runFrom: stage.runFrom, runTo: stage.runTo, cards, contextAt: stage.firstCard + shown.length * STAGGER,
    named, ticks, saveAt, nextAt: stage.next ? saveAt + NEXT : null,
  };
}

// How long "Simulate risks" is on screen before the cut, so the hand-off reads before the crossfade even though the
// line ends late.
const TRIGGER_SHOWN = 1.6;

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

/** The problem scene in pictures: the three costs' empty rings open it, and each fills as the voice names it
 *  (onScreen[0..2], lower-cased as spoken); the red cost holds until "govern", when the two aims replace it, meet,
 *  and light their shared target once they overlap. */
export function problemMoments(scene, cues) {
  const end = cues[cues.length - 1].end;
  const at = (phrase) => spokenAt(scene.narration, phrase, end);
  const marks = scene.onScreen.slice(0, 3).map((m) => at(m.toLowerCase()) - 0.1);
  const costsOut = at("govern") - 0.2;
  const circles = costsOut + 0.1;
  return {rings: 0, marks, costsOut, circles, dots: at("The challenge"), meet: circles, target: circles + 0.7};
}

// The tallies count up one after another, quickly enough to be read whole before the portfolio arrives.
export const TALLY_COUNT = 0.6;
const TALLY_STEP = 0.15;

// The capabilities the voice names as each lands, in the order the close lists them on screen.
export const KEYWORDS = ["models", "data lineage", "programmes", "architecture", "intelligence"];
const BRAND = "AI Center X";

/** The close: the years collapse into the hour as the voice says it and the tallies count up beside the message;
 *  the comparison stays until just before "models", then fades, and only then does the portfolio arrive; the brand
 *  card and its footer close the video. */
export function closeMoments(scene, cues) {
  const end = cues[cues.length - 1].end;
  const at = (phrase) => spokenAt(scene.narration, phrase, end);
  const beats = ["Three years", "reduced", "less than an hour", "Then scale up", ...KEYWORDS, BRAND];
  const times = beats.map(at);
  if (times.some((x, i) => i && x <= times[i - 1])) {
    throw new Error(`The close's narration must say ${beats.join(", ")} in that order.`);
  }
  const brandAt = at(BRAND);
  const keywords = KEYWORDS.map(at);
  const collapse = at("reduced") - 0.2;
  const scaleAt = keywords[0] - 0.55;
  return {
    message: at("Three years") + 0.2, collapse, tallies: [0, 1, 2].map((i) => collapse - 0.2 + i * TALLY_STEP),
    scaleAt, portfolioIn: scaleAt + 0.4, keywords, brandAt, footer: brandAt + 0.3,
  };
}
