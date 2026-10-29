# Marketing video

This folder holds the narrated marketing video of the CV Screening Assistant journey, which runs just under 60 s. It is built with [Remotion](https://www.remotion.dev/) as a standalone Node project. The prototype, its films and `tools/` never import from it, and `npm run check` at the repo root runs without it being installed.

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
| `f1-create` | hook, canvas | 15 s |
| `f2-risks` | risks | 14 s |
| `f3-mitigations` | mitigations | 12 s |
| `f4-enhancements` | enhancements | 12 s |
| `f5-closing` | end | 6 s |

The lengths come from `src/timeline.json`, which is the only place timing is set. Each scene is a placeholder until #30 and #31 build it. The dashed line marks the caption safe area, the bottom 18% of the frame, which stays free for the captions.

To check that the fonts loaded, look at a scene title: it is set in Fraunces, a serif with sharp, high-contrast strokes. A render stops with an error if a font file fails to load.

## Render a fragment

```sh
npm run video:render:fragment -- f2-risks
```

This writes `video/out/fragments/f2-risks.mp4`. `video/out/` is git-ignored, so rendered video is never committed. Only the five composition names in the table are accepted.

Every fragment is encoded the same way (H.264, yuv420p, BT.709, AAC) and always carries an audio track, set in `remotion.config.ts`, so the approved fragments can be joined without re-encoding. `CvScreeningJourney` is for previewing only; the released video joins the rendered fragments. To render it anyway, run `npx remotion render CvScreeningJourney` inside `video/`, which writes `video/out/CvScreeningJourney.mp4`.

## Files

- `src/timeline.json`: scenes, timing and data references (#27). `test/marketing_video_timeline_test.py` checks it.
- `src/compositions.json`: the composition id of each fragment.
- `src/theme.ts`: colours and font stacks copied from the prototype's default theme. `test/marketing_video_project_test.py` checks that they still match `index.html`.
- `public/fonts/`: Fraunces and IBM Plex Sans as variable fonts, each with its SIL Open Font License.

## Known audit finding

`npm audit` reports 10 high-severity findings and no critical ones. All 10 come from one advisory in `zod` 4.5.4, which Remotion pins exactly: [GHSA-mrhx-c7xc-m3w5](https://github.com/advisories/GHSA-mrhx-c7xc-m3w5), memory exhaustion while validating oversized collections. Remotion only validates this project's own composition props, on this machine. Forcing a newer `zod` makes Remotion warn of broken renders, so the pinned version stays until Remotion moves to a fixed one. Run `npm audit --prefix video` after every Remotion upgrade; it must report no critical findings.
