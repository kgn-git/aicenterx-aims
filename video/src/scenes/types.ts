import type {Scene} from "../scene";

export type Cue = {start: number; end: number; text: string};

/** What every scene receives: its timeline entry, its caption cues in seconds from its own start, and its length. */
export type SceneProps = {scene: Scene; cues: Cue[]; seconds: number};

/** The first cue that says `phrase`. A scene waits for words rather than a cue's position, since rewording a line
 *  re-splits the captions; a missing phrase stops the render instead of silently moving the moment. */
export const cueWith = (cues: Cue[], phrase: string): Cue => {
  const cue = cues.find((c) => c.text.includes(phrase));
  if (!cue) throw new Error(`No caption cue says "${phrase}". Update the scene to the new narration.`);
  return cue;
};

/** When `phrase` starts within the cue that says it, by its share of the cue's characters, as the captions are timed. */
export const saidAt = (cues: Cue[], phrase: string): number => {
  const cue = cueWith(cues, phrase);
  return cue.start + ((cue.end - cue.start) * cue.text.indexOf(phrase)) / cue.text.length;
};
