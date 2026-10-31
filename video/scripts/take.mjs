// Cuts one continuous narration take (24 kHz 16-bit mono PCM) into one clip per scene, using the voice's word
// timings. Voicing the script in one take keeps one pace and energy across scenes; the pauses between scenes are
// hardly longer than those between sentences, so only the words show where a scene ends.
const RATE = 24000;
// Long enough to keep a word's first consonant, which can start before the timings say.
const LEAD = 0.15;
const TRAIL = 0.08;
// A breath before the first word, so it lands as the crossfade into the scene finishes.
const PAD = 0.1;
const MIN_MATCH = 0.85;
// The longest pause kept inside a scene's line: the user approved the voice at this pace.
const KEEP = 0.35;
// Long enough that a cut through breath or a mouth click does not pop, short enough not to soften a word.
const FADE = 0.02;
// Silence is any 10 ms frame below 3% of the take's loudest, which catches breaths and room tone between words.
const FRAME = 240;
const QUIET = 0.03;

const token = (w) => w.toLowerCase().replace(/[^a-z0-9]/g, "");

/** For each script word, the index of the timed word it lines up with (or -1), by a word-level edit distance,
 *  so a misheard or missing word shifts nothing else; and how many script words matched exactly. */
function align(script, heard) {
  const n = script.length;
  const m = heard.length;
  const cost = Array.from({length: n + 1}, (_, i) => Array.from({length: m + 1}, (_, j) => (i === 0 ? j : j === 0 ? i : 0)));
  for (let i = 1; i <= n; i++) {
    for (let j = 1; j <= m; j++) {
      const same = script[i - 1] === heard[j - 1] ? 0 : 1;
      cost[i][j] = Math.min(cost[i - 1][j - 1] + same, cost[i - 1][j] + 1, cost[i][j - 1] + 1);
    }
  }
  const map = Array(n).fill(-1);
  let exact = 0;
  for (let i = n, j = m; i > 0 && j > 0; ) {
    const same = script[i - 1] === heard[j - 1] ? 0 : 1;
    if (cost[i][j] === cost[i - 1][j - 1] + same) {
      map[i - 1] = j - 1;
      exact += 1 - same;
      i--;
      j--;
    } else if (cost[i][j] === cost[i - 1][j] + 1) i--;
    else j--;
  }
  return {map, exact};
}

/** The voice's per-character timings as {word, start, end} in seconds, a word being a run of non-space characters.
 *  Throws unless every character has a finite start and end in order, since a bad time would cut a wrong clip. */
export function wordsFromAlignment({characters, character_start_times_seconds: starts, character_end_times_seconds: ends}) {
  const sound = Array.isArray(characters) && Array.isArray(starts) && Array.isArray(ends) &&
    characters.every((c) => typeof c === "string") && characters.length === starts.length && starts.length === ends.length &&
    starts.every((s, i) => Number.isFinite(s) && Number.isFinite(ends[i]) && 0 <= s && s <= ends[i] && (!i || starts[i - 1] <= s));
  if (!sound) throw new Error("The voice's timings do not line up with its text.");
  const words = [];
  let word = null;
  characters.forEach((c, i) => {
    if (/\s/.test(c)) word = null;
    else if (word) {
      word.word += c;
      word.end = ends[i];
    } else words.push((word = {word: c, start: starts[i], end: ends[i]}));
  });
  return words;
}

/** The samples of [from, to) seconds of `pcm`, faded in and out over FADE so the cut cannot click. */
function slice(pcm, from, to) {
  const out = Buffer.from(pcm.subarray(Math.round(from * RATE) * 2, Math.round(to * RATE) * 2));
  const n = out.length / 2;
  const fade = Math.min(Math.round(FADE * RATE), Math.floor(n / 2));
  for (let i = 0; i < fade; i++) {
    const gain = i / fade;
    out.writeInt16LE(Math.round(out.readInt16LE(i * 2) * gain), i * 2);
    out.writeInt16LE(Math.round(out.readInt16LE((n - 1 - i) * 2) * gain), (n - 1 - i) * 2);
  }
  return out;
}

/** The take's silent runs as [start, end] seconds: 10 ms frames quieter than QUIET of its loudest frame. The voice's
 *  character timings run back to back, so its pauses show only in the sound. */
function silences(pcm) {
  const rms = [];
  for (let at = 0; at + FRAME * 2 <= pcm.length; at += FRAME * 2) {
    let sum = 0;
    for (let i = 0; i < FRAME; i++) sum += pcm.readInt16LE(at + i * 2) ** 2;
    rms.push(Math.sqrt(sum / FRAME));
  }
  const floor = QUIET * Math.max(0, ...rms);
  const runs = [];
  rms.forEach((r, i) => {
    if (r > floor) return;
    const last = runs.at(-1);
    if (last && last[1] === i * FRAME / RATE) last[1] = (i + 1) * FRAME / RATE;
    else runs.push([i * FRAME / RATE, (i + 1) * FRAME / RATE]);
  });
  return runs;
}

/** [from, to) with the silence at its edges cut back to LEAD and TRAIL, split around every silence inside it that
 *  runs past KEEP, which keeps KEEP from its middle. */
function spans(from, to, quiet) {
  let [a, b] = [from, to];
  for (const [s, e] of quiet) {
    if (s <= a && e > a) a = Math.min(Math.max(a, e - LEAD), b);
    if (s < b && e >= b) b = Math.max(Math.min(b, s + TRAIL), a);
  }
  const out = [];
  let start = a;
  for (const [s, e] of quiet) {
    if (s <= start || e >= b || e - s <= KEEP) continue;
    out.push([start, s + KEEP / 2]);
    start = e - KEEP / 2;
  }
  return [...out, [start, b]];
}

/** One PCM buffer per scene narration in `scenes`, PAD seconds of silence then the take cut from just before its
 *  first spoken word to just after its last, with its long pauses shortened and every cut faded;
 *  `words` are the voice's {word, start, end} in seconds. Throws when they match the script too little, or when a
 *  scene's words are timed where the take has no sound, so a drifted take is never written as an empty clip. */
export function splitTake(pcm, scenes, words) {
  const counts = scenes.map((s) => s.split(/\s+/).length);
  const script = scenes.flatMap((s) => s.split(/\s+/)).map(token);
  const {map, exact} = align(script, words.map((w) => token(w.word)));
  if (exact / script.length < MIN_MATCH) {
    throw new Error(`Only ${exact} of the script's ${script.length} words were heard in the take.`);
  }
  const samples = pcm.length / 2;
  const quiet = silences(pcm);
  const heard = [];
  let first = 0;
  for (const count of counts) {
    const own = map.slice(first, first + count).filter((j) => j >= 0);
    if (!own.length) throw new Error(`Scene ${heard.length + 1} was not heard in the take.`);
    heard.push(own.map((j) => words[j]));
    first += count;
  }
  return heard.map((own, i) => {
    const [start, end] = [own[0].start, own.at(-1).end];
    const from = Math.max(start - LEAD, i ? (heard[i - 1].at(-1).end + start) / 2 : 0);
    const to = Math.min(end + TRAIL, i < heard.length - 1 ? (end + heard[i + 1][0].start) / 2 : samples / RATE);
    const kept = spans(from, to, quiet);
    if (kept.reduce((sum, [a, b]) => sum + b - a, 0) <= LEAD + TRAIL) {
      throw new Error(`Scene ${i + 1} has no sound where its words are timed.`);
    }
    const parts = kept.map(([a, b]) => slice(pcm, a, b));
    return Buffer.concat([Buffer.alloc(Math.round(PAD * RATE) * 2), ...parts]);
  });
}
