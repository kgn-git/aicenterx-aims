// Shared by the compositions, the caption builder and, through scripts/scene-seconds.mjs, the tests, so a scene
// lasts the same time on screen and in the cues. A clip that runs past its planned seconds stretches its scene
// instead of being cut off; the user reviews the combined length before any narration is shortened. Lengths are
// whole frames, so Root.tsx needs no rounding of its own and the cue offsets match the frames exactly.
export const FPS = 30;
export const TAIL = 0.3;

export const sceneSeconds = (scene) =>
  Math.ceil(Math.max(scene.seconds, (scene.audioSeconds ?? 0) + TAIL) * FPS - 1e-9) / FPS;
