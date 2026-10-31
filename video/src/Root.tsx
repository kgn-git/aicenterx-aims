import React from "react";
import {fade} from "@remotion/transitions/fade";
import {linearTiming, TransitionSeries} from "@remotion/transitions";
import {Audio, Composition, Series, staticFile} from "remotion";
import "./fonts";
import compositions from "./compositions.json";
import {Placeholder} from "./Placeholder";
import {SCENES} from "./scenes";
import captions from "./captions.json";
import timeline from "./timeline.json";
import {video} from "./theme";
import {sceneSeconds, TAIL} from "./timing.mjs";

type FragmentId = keyof typeof compositions;

const scenes = new Map(timeline.scenes.map((s) => [s.id, s]));
const frames = (seconds: number) => Math.round(seconds * video.fps);
const scenesOf = (id: string) => timeline.fragments.find((f) => f.id === id)!.scenes.map((s) => scenes.get(s)!);
const fragmentFrames = (id: string) => scenesOf(id).reduce((sum, s) => sum + frames(sceneSeconds(s)), 0);

/** A scene's cues in seconds from the scene's own start, since cue times count from the fragment's start. */
const sceneCues = (fragmentId: string, sceneId: string) => {
  const list = scenesOf(fragmentId);
  const start = list.slice(0, list.findIndex((s) => s.id === sceneId)).reduce((sum, s) => sum + sceneSeconds(s), 0);
  return captions.cues
    .filter((c) => c.fragment === fragmentId && c.scene === sceneId)
    .map((c) => ({start: c.start - start, end: c.end - start, text: c.lines.join(" ")}));
};

type Scene = (typeof timeline.scenes)[number];

const SceneView: React.FC<{fragmentId: string; scene: Scene}> = ({fragmentId, scene}) => {
  const View = SCENES[scene.id];
  return (
    <>
      {View ? (
        <View scene={scene} cues={sceneCues(fragmentId, scene.id)} seconds={sceneSeconds(scene)} />
      ) : (
        <Placeholder scene={scene} />
      )}
      {"audioSeconds" in scene && <Audio src={staticFile(`audio/${scene.id}.wav`)} />}
    </>
  );
};

const FragmentScenes: React.FC<{fragmentId: string}> = ({fragmentId}) => (
  <Series>
    {scenesOf(fragmentId).map((scene) => (
      <Series.Sequence key={scene.id} durationInFrames={frames(sceneSeconds(scene))} name={scene.id}>
        <SceneView fragmentId={fragmentId} scene={scene} />
      </Series.Sequence>
    ))}
  </Series>
);

// A crossfade as long as the silent tail every scene ends with, so two voices never overlap.
const CROSSFADE = frames(TAIL);
const journey = timeline.fragments.flatMap((f) => scenesOf(f.id).map((scene) => ({fragmentId: f.id, scene})));

/** The whole story in one piece, each scene crossfading into the next; the released video is rendered from this. */
const CvScreeningJourney: React.FC = () => (
  <TransitionSeries>
    {journey.flatMap(({fragmentId, scene}, i) => [
      ...(i ? [<TransitionSeries.Transition key={`fade-${scene.id}`} presentation={fade()} timing={linearTiming({durationInFrames: CROSSFADE})} />] : []),
      <TransitionSeries.Sequence key={scene.id} durationInFrames={frames(sceneSeconds(scene))} name={scene.id}>
        <SceneView fragmentId={fragmentId} scene={scene} />
      </TransitionSeries.Sequence>,
    ])}
  </TransitionSeries>
);

export const RemotionRoot: React.FC = () => (
  <>
    {timeline.fragments.map((f) => (
      <Composition
        key={f.id}
        id={compositions[f.id as FragmentId]}
        component={FragmentScenes}
        defaultProps={{fragmentId: f.id}}
        durationInFrames={fragmentFrames(f.id)}
        {...video}
      />
    ))}
    <Composition
      id="CvScreeningJourney"
      component={CvScreeningJourney}
      durationInFrames={journey.reduce((sum, {scene}) => sum + frames(sceneSeconds(scene)), 0) - (journey.length - 1) * CROSSFADE}
      {...video}
    />
  </>
);
