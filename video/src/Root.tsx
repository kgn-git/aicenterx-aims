import React from "react";
import {Composition, Series} from "remotion";
import "./fonts";
import compositions from "./compositions.json";
import timeline from "./timeline.json";
import {Placeholder} from "./Placeholder";
import {video} from "./theme";

type FragmentId = keyof typeof compositions;

const scenes = new Map(timeline.scenes.map((s) => [s.id, s]));
const frames = (seconds: number) => Math.round(seconds * video.fps);
const scenesOf = (id: string) => timeline.fragments.find((f) => f.id === id)!.scenes.map((s) => scenes.get(s)!);
const fragmentFrames = (id: string) => scenesOf(id).reduce((sum, s) => sum + frames(s.seconds), 0);

const Fragment: React.FC<{fragmentId: string}> = ({fragmentId}) => (
  <Series>
    {scenesOf(fragmentId).map((scene) => (
      <Series.Sequence key={scene.id} durationInFrames={frames(scene.seconds)} name={scene.id}>
        <Placeholder scene={scene} />
      </Series.Sequence>
    ))}
  </Series>
);

/** Plays the five fragments in order, for previewing the whole story; #32 joins the rendered fragments instead. */
const CvScreeningJourney: React.FC = () => (
  <Series>
    {timeline.fragments.map((f) => (
      <Series.Sequence key={f.id} durationInFrames={fragmentFrames(f.id)} name={compositions[f.id as FragmentId]}>
        <Fragment fragmentId={f.id} />
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
        component={Fragment}
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
