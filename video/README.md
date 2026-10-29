# Marketing video

This folder holds the narrated marketing video of the CV Screening Assistant journey, which targets 60 s; until the user's combined review, a plan of up to 66 s and a voiced length of 54 to 72 s are accepted. It is built with [Remotion](https://www.remotion.dev/) as a standalone Node project. The prototype, its films and `tools/` never import from it, and `npm run check` at the repo root runs without it being installed.

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

Remotion Studio opens at http://localhost:3000. It lists one composition per fragment and `CvScreeningJourney`, which plays all five in order:

| Composition | Scenes | Length |
|---|---|---|
| `f1-create` | hook, problem, canvas | 21 s planned, 23 s with the clips |
| `f2-risks` | risks | 13 s |
| `f3-mitigations` | mitigations | 13 s planned, 14.8 s with the clip |
| `f4-enhancements` | enhancements | 12 s planned, 12.1 s with the clip |
| `f5-closing` | end | 7 s planned, 8.7 s with the clip |

The planned lengths are the `seconds` in `src/timeline.json`. A scene plays for its planned length or for its clip plus 0.3 s, whichever is longer, rounded up to a whole frame; `src/timing.mjs` holds that rule. The hook, problem, canvas and risks scenes are built; the rest are placeholders, and every scene plays its clip. The bottom 18% of the frame stays free, so a player's subtitles never cover the interface.

To check that the fonts loaded, look at a scene title: it is set in Fraunces, a serif with sharp, high-contrast strokes. A render stops with an error if a font file fails to load.

## Narrate

The narration is voiced with OpenAI text-to-speech and committed as `public/audio/<scene>.wav`, so a render needs neither the key nor the model. Remake it only when the narration changes. Each run costs well under a cent.

1. Copy `.env.example` to `.env.local` at the repo root and add `OPENAI_API_KEY`. The file is git-ignored.
2. In the key's project on platform.openai.com, allow both `gpt-4o-mini-tts-2025-12-15` and `gpt-4o-mini-tts` under the model limits. Without the second, OpenAI refuses some requests with HTTP 403. A change there can take about 30 minutes to apply everywhere.
3. Voice the scenes, then rebuild the captions:

```sh
npm run video:narrate                  # every scene
npm run video:narrate -- f2-risks      # only one fragment's scenes
npm run video:narrate -- problem       # only one scene
npm run video:cues
```

`video:narrate` writes each clip's length into `src/timeline.json` as `audioSeconds`. It replaces nothing unless every clip in the run succeeded, and it never prints the key. Listen to each clip before committing: it must say the whole line. `video:cues` rebuilds `src/captions.json`; the captions test fails until it has run.

The voice is Marin, chosen by the project owner on 29 October 2026, and set as `VOICE` in `scripts/narrate.mjs` with the speaking instructions. To compare voices again, `npm run video:narrate -- --samples` writes the hook in each candidate voice to `video/out/samples/`.

OpenAI plans to retire the dated model on 6 January 2027. The committed clips keep working, but a new narration after that date needs a newer model, and possibly another voice choice.

## Render a fragment

```sh
npm run video:render:fragment -- f2-risks
```

This writes `video/out/fragments/f2-risks.mp4`. `video/out/` is git-ignored, so rendered video is never committed. Only the five composition names in the table are accepted.

Every fragment is encoded the same way (H.264, yuv420p, BT.709, AAC) and always carries an audio track, set in `remotion.config.ts`, so the approved fragments can be joined without re-encoding. `CvScreeningJourney` is for previewing only; the released video joins the rendered fragments. To render it anyway, run `npx remotion render CvScreeningJourney` inside `video/`, which writes `video/out/CvScreeningJourney.mp4`.

## Files

- `src/timeline.json`: scenes, timing and data references (#27). `test/marketing_video_timeline_test.py` checks it.
- `src/compositions.json`: the composition id of each fragment.
- `src/timing.mjs`: how long each scene plays. `scripts/scene-seconds.mjs` prints it for the tests.
- `src/captions.json`: the caption cues, built by `scripts/cues.mjs`. `test/marketing_video_captions_test.py` checks them. They are not burned into the picture: the released video carries them as a switchable subtitle track and an .srt (user decision, 29 October 2026).
- `public/audio/`: one narration clip per scene, made by `scripts/narrate.mjs`. `test/marketing_video_audio_test.py` checks them.
- `src/theme.ts`: colours and font stacks copied from the prototype's default theme. `test/marketing_video_project_test.py` checks that they still match `index.html`.
- `public/fonts/`: Fraunces and IBM Plex Sans as variable fonts, each with its SIL Open Font License.

## Known audit finding

`npm audit` reports 10 high-severity findings and no critical ones. All 10 come from one advisory in `zod` 4.5.4, which Remotion pins exactly: [GHSA-mrhx-c7xc-m3w5](https://github.com/advisories/GHSA-mrhx-c7xc-m3w5), memory exhaustion while validating oversized collections. Remotion only validates this project's own composition props, on this machine. Forcing a newer `zod` makes Remotion warn of broken renders, so the pinned version stays until Remotion moves to a fixed one. Run `npm audit --prefix video` after every Remotion upgrade; it must report no critical findings.
