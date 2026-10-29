import React from "react";
import {Audio, Composition, Series, staticFile} from "remotion";
import "./fonts";
import compositions from "./compositions.json";
import {Placeholder} from "./Placeholder";
import {SCENES} from "./scenes";
import captions from "./captions.json";
import timeline from "./timeline.json";
import {video} from "./theme";
import {sceneSeconds} from "./timing.mjs";

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
    .map((c) => ({start: c.start - start, end: c.end - start}));
};

const FragmentScenes: React.FC<{fragmentId: string}> = ({fragmentId}) => (
  <>
    <Series>
      {scenesOf(fragmentId).map((scene) => {
        const View = SCENES[scene.id];
        return (
          <Series.Sequence key={scene.id} durationInFrames={frames(sceneSeconds(scene))} name={scene.id}>
            {View ? (
              <View scene={scene} cues={sceneCues(fragmentId, scene.id)} seconds={sceneSeconds(scene)} />
            ) : (
              <Placeholder scene={scene} />
            )}
            {"audioSeconds" in scene && <Audio src={staticFile(`audio/${scene.id}.wav`)} />}
          </Series.Sequence>
        );
      })}
    </Series>
  </>
);

/** Plays the five fragments in order, for previewing only: the released video joins the rendered fragments. */
const CvScreeningJourney: React.FC = () => (
  <Series>
    {timeline.fragments.map((f) => (
      <Series.Sequence key={f.id} durationInFrames={fragmentFrames(f.id)} name={compositions[f.id as FragmentId]}>
        <FragmentScenes fragmentId={f.id} />
      </Series.Sequence>
    ))}
  </Series>
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
      durationInFrames={timeline.fragments.reduce((sum, f) => sum + fragmentFrames(f.id), 0)}
      {...video}
    />
  </>
);
