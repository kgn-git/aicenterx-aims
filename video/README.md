# Marketing video

This folder holds the narrated marketing video of the CV Screening Assistant journey, which runs about 60 s (58 to 61 s), with a close of about 15 s. It is built with [Remotion](https://www.remotion.dev/) as a standalone Node project. The prototype, its films and `tools/` never import from it, and `npm run check` at the repo root runs without it being installed.

Remotion is source-available, not open source. Its free licence covers individuals and companies of up to three people; the project owner confirmed on 28 October 2026 that it applies here.

## Install

Node 22.9 or later is needed. From the repo root:

```sh
npm --prefix video ci
```

npm's install scripts stay blocked: renders work without esbuild's postinstall step, so there is no need to allow it. The first preview or render downloads Chrome Headless Shell once (about 120 MB). After that, a render needs no network: the fonts are bundled.

## Preview

```sh
npm run video:studio
```

Remotion Studio opens at http://localhost:3000. It lists one composition per fragment and `CvScreeningJourney`, the whole story with crossfades:

| Composition | Scenes | Length |
|---|---|---|
| `f1-create` | hook, problem, canvas | 29 s planned, 29.8 s with the clips |
| `f2-risks` | risks | 12 s planned, 12.6 s with the clip |
| `f3-mitigations` | mitigations | 12.5 s planned, 13.3 s with the clip |
| `f4-enhancements` | enhancements | 12 s |
| `f5-closing` | end | 19 s |

The planned lengths are the `seconds` in `src/timeline.json`. A scene plays for its planned length or for its clip plus 0.3 s, whichever is longer, rounded up to a whole frame; `src/timing.mjs` holds that rule. Every scene is built and plays its clip. The bottom 18% of the frame stays free, so a player's subtitles never cover the interface.

To check that the fonts loaded, look at a scene title: it is set in Fraunces, a serif with sharp, high-contrast strokes. A render stops with an error if a font file fails to load.

## Narrate

The narration is voiced with ElevenLabs text-to-speech (Matilda on `eleven_v3`) and committed as `public/audio/<scene>.wav`, so a render needs neither the key nor the network. Remake it only when the narration changes.

1. Copy `.env.example` to `.env.local` at the repo root and add `ELEVENLABS_API_KEY`, a key allowed to use text to speech. The file is git-ignored.
2. Voice the scenes, then rebuild the captions:

```sh
npm run video:narrate                  # every scene
npm run video:narrate -- f2-risks      # only one fragment's scenes
npm run video:narrate -- problem       # only one scene
npm run video:cues
```

`video:narrate` writes each clip's length into `src/timeline.json` as `audioSeconds`. It replaces nothing unless every clip in the run succeeded, and it never prints the key. Listen to each clip before committing: it must say the whole line. Then set each scene's `seconds` to its clip plus 0.3 s, and the close's to its clip plus 1.0 s; the timeline test checks this, so no scene holds dead air. `video:cues` rebuilds `src/captions.json`; the captions test fails until it has run.

The whole narration is voiced in one take, so the voice keeps one pace, then cut into scenes at the per-character timings ElevenLabs returns with the audio (`/with-timestamps`). Those timings run back to back, so `scripts/take.mjs` finds the pauses in the sound itself: it shortens any silence inside a line to 0.35 s, trims each clip's edges to a short lead and trail, and fades every cut over 20 ms so none clicks. `eleven_v3` takes no speed setting, so the shortened pauses set the pace. A take varies each time it is voiced; listen for slips and voice again if one appears. To compare voices, `npm run video:narrate -- --samples` writes the hook, mitigations and close in each voice of `SAMPLE_VOICES` to `video/out/samples/`.

## Render a fragment

```sh
npm run video:render:fragment -- f2-risks
```

This writes `video/out/fragments/f2-risks.mp4`. `video/out/` is git-ignored, so rendered video is never committed. Only the five composition names in the table are accepted.

Fragments are for review. The released video is rendered in one piece from `CvScreeningJourney`, where each scene crossfades into the next over 0.3 s, the silent tail every scene ends with:

```sh
npm run video:assemble
```

This writes `video/out/cv-screening-journey.mp4` and keeps it only if it runs 61 s at most (the user's 60 s target) at 1920x1080, with H.264 video and AAC audio.

## Files

- `src/timeline.json`: scenes, timing and data references (#27). `test/marketing_video_timeline_test.py` checks it.
- `src/compositions.json`: the composition id of each fragment.
- `src/timing.mjs`: how long each scene plays. `scripts/scene-seconds.mjs` prints it for the tests.
- `src/captions.json`: the caption cues, built by `scripts/cues.mjs`. `test/marketing_video_captions_test.py` checks them. The scenes time their animation from them; the released video carries no subtitles.
- `public/audio/`: one narration clip per scene, made by `scripts/narrate.mjs`. `test/marketing_video_audio_test.py` checks them.
- `scripts/take.mjs`: cuts the one narrated take into scene clips at the word timings. `test/marketing_video_take_test.py` checks it.
- `scripts/assemble.mjs`: renders the released video in one piece and keeps it only after its checks. `test/marketing_video_assemble_test.py` checks it.
- `src/sources.mjs`: which EU AI Act articles a source chip names. `test/marketing_video_sources_test.py` checks it.
- `src/theme.ts`: colours and font stacks copied from the prototype's default theme. `test/marketing_video_project_test.py` checks that they still match `index.html`.
- `public/fonts/`: Fraunces and IBM Plex Sans as variable fonts, each with its SIL Open Font License.

## Known audit finding

`npm audit` reports 10 high-severity findings and no critical ones. All 10 come from one advisory in `zod` 4.5.4, which Remotion pins exactly: [GHSA-mrhx-c7xc-m3w5](https://github.com/advisories/GHSA-mrhx-c7xc-m3w5), memory exhaustion while validating oversized collections. Remotion only validates this project's own composition props, on this machine. Forcing a newer `zod` makes Remotion warn of broken renders, so the pinned version stays until Remotion moves to a fixed one. Run `npm audit --prefix video` after every Remotion upgrade; it must report no critical findings.
