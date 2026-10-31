import type {Scene} from "../scene";

export {cueWith, saidAt} from "../moments.mjs";

export type Cue = {start: number; end: number; text: string};

/** What every scene receives: its timeline entry, its caption cues in seconds from its own start, and its length. */
export type SceneProps = {scene: Scene; cues: Cue[]; seconds: number};
