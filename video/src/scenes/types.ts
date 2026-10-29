import type {Scene} from "../scenes";

/** What every scene receives: its timeline entry, its caption cues in seconds from its own start, and its length. */
export type SceneProps = {scene: Scene; cues: {start: number; end: number}[]; seconds: number};
