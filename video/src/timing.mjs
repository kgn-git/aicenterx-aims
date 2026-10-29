// Shared by the compositions and the caption builder, so a scene lasts the same time on screen and in the cues.
// A clip that runs past its planned seconds stretches its scene instead of being cut off; the user reviews the
// combined length before any narration is shortened.
export const TAIL = 0.3;

export const sceneSeconds = (scene) => Math.max(scene.seconds, (scene.audioSeconds ?? 0) + TAIL);
