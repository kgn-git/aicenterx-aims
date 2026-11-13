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

// A figure, card or line lands this far ahead of the word that calls for it, so it is up as the word is heard.
const LEAD = 0.1;
// The footage plays alone this long before the first figure, though the voice starts on it.
const LIGHT_ALONE = 0.3;

/** When each of `phrases` is said in `scene`, refusing a line that says them out of order. */
const inOrder = (scene, cues, phrases) => {
  const end = cues[cues.length - 1].end;
  const times = phrases.map((p) => spokenAt(scene.narration, p, end));
  if (times.some((x, i) => i && x <= times[i - 1])) {
    throw new Error(`The ${scene.id} line must say ${phrases.join(", ")} in that order.`);
  }
  return times;
};

/** The world: the sponsor's footage alone, then 56% as its number is said. */
export function worldMoments(scene, cues) {
  const [said] = inOrder(scene, cues, ["Fifty-six per cent"]);
  return {figure: Math.max(LIGHT_ALONE, said - LEAD)};
}

/** The break: 40%+ over the whiteboard, a cut to the desk, ~5% over it, then the late risks. */
export function breakMoments(scene, cues) {
  const [forty, five, late] = inOrder(scene, cues, ["forty per cent", "five per cent", "The risks show up"]);
  const figures = [forty - LEAD, five - LEAD];
  return {figures, cut: figures[1] - 0.6, late: late - LEAD};
}

// The montage's pace: cards and rows land one after another, ticks follow at a glance's pace.
const STAGGER = 0.12;
const LANDED = 0.25;
const TICK = 0.22;
// The product slides in over the team as "simulate" is said, and its button is pressed just after.
const CLICK_AFTER = 0.25;
const ROWS_AFTER = 0.2;

/** The fix: the team's footage until "simulate", then the product: "Simulate risks" pressed, the risk cards land,
 *  their AIID and MIT chips light as "documented incidents" and "industry standards" are said, the saved risks are
 *  ticked; on "select", "Generate mitigations" is pressed, the rows land and the relevant ones are ticked. A scene too
 *  short to finish its ticks stops the render rather than cut them off. */
export function fixMoments(scene, cues, seconds) {
  const [simulate, incidents, standards, select] =
    inOrder(scene, cues, ["simulate", "documented incidents", "industry standards", "select"]);
  const {risks, mitigations} = scene.dataRefs;
  const productAt = simulate - LEAD;
  const click = productAt + CLICK_AFTER;
  const cards = risks.shown.map((_, i) => click + 0.2 + i * STAGGER);
  const named = [Math.max(incidents, cards.at(-1) + LANDED), Math.max(standards, cards.at(-1) + LANDED + 0.1)];
  const ticks = risks.saved.map((id, k) => Math.max(named[1], cards[risks.shown.indexOf(id)] + LANDED) + k * TICK);
  const mitClick = Math.max(select - LEAD, ticks.at(-1) + 0.3);
  const rows = mitigations.shown.map((_, i) => mitClick + ROWS_AFTER + i * STAGGER);
  const rowTicks = mitigations.saved.map((_, k) => rows.at(-1) + LANDED + k * TICK);
  const done = seconds - 0.3 - 0.5;
  if (rowTicks.at(-1) > done) {
    throw new Error(`The fix scene needs ${(rowTicks.at(-1) - done).toFixed(2)} s more to tick its mitigations. Lengthen its line.`);
  }
  return {productAt, click, cards, named, ticks, mitClick, rows, rowTicks};
}

/** The proof: "< 10 min" on the client meeting from the first words, then the brand card as its name is said, its
 *  footer just after. */
export function proofMoments(scene, cues) {
  const [brand] = inOrder(scene, cues, ["AI Center X"]);
  const brandAt = brand - LEAD;
  return {badge: LIGHT_ALONE, brandAt, footer: brandAt + 0.3};
}
