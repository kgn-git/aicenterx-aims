import React from "react";
import {useCurrentFrame, useVideoConfig} from "remotion";
import {shots, worldMoments} from "../moments.mjs";
import {color} from "../theme";
import {Figure} from "../ui/Figure";
import {Footage} from "../ui/Footage";
import {Background} from "../ui/kit";
import type {SceneProps} from "./types";

/** Beat 1, the world: a sponsor reviewing results, and the figure that says most see no gain from AI yet. */
export const World: React.FC<SceneProps> = ({scene, cues, seconds}) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const m = worldMoments(scene, cues);
  const [figure, label] = scene.onScreen;
  const refs = scene.dataRefs as {sources: {cite: string}[]};
  const [shot] = shots(scene, cues, seconds);
  return (
    <Background dots={0}>
      <Footage {...shot} />
      <Figure t={t} at={m.figure} figure={figure} label={label} cite={refs.sources[0].cite} tone={color.gov} />
    </Background>
  );
};
