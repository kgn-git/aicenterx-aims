// Cuts one continuous narration take (24 kHz 16-bit mono PCM) into one clip per scene, using a transcript's word
// timings. Voicing the script in one take keeps one pace and energy across scenes; the pauses between scenes are
// hardly longer than those between sentences, so only the words show where a scene ends.
const RATE = 24000;
const LEAD = 0.03;
const TRAIL = 0.08;
const MIN_MATCH = 0.85;

const token = (w) => w.toLowerCase().replace(/[^a-z0-9]/g, "");

/** For each script word, the index of the transcript word it lines up with (or -1), by a word-level edit distance,
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

/** One PCM buffer per scene narration in `scenes`, cut from just before its first spoken word to just after its last;
 *  `words` are the transcript's {word, start, end} in seconds. Throws when the transcript matches too little. */
export function splitTake(pcm, scenes, words) {
  const counts = scenes.map((s) => s.split(/\s+/).length);
  const script = scenes.flatMap((s) => s.split(/\s+/)).map(token);
  const {map, exact} = align(script, words.map((w) => token(w.word)));
  if (exact / script.length < MIN_MATCH) {
    throw new Error(`Only ${exact} of the script's ${script.length} words were heard in the take.`);
  }
  const samples = pcm.length / 2;
  const spans = [];
  let first = 0;
  for (const count of counts) {
    const own = map.slice(first, first + count).filter((j) => j >= 0);
    if (!own.length) throw new Error(`Scene ${spans.length + 1} was not heard in the take.`);
    spans.push([words[own[0]].start, words[own.at(-1)].end]);
    first += count;
  }
  return spans.map(([start, end], i) => {
    const from = Math.max(start - LEAD, i ? (spans[i - 1][1] + start) / 2 : 0);
    const to = Math.min(end + TRAIL, i < spans.length - 1 ? (end + spans[i + 1][0]) / 2 : samples / RATE);
    return pcm.subarray(Math.round(from * RATE) * 2, Math.round(to * RATE) * 2);
  });
}
