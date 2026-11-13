import React from "react";
import {useCurrentFrame, useVideoConfig} from "remotion";
import {breakMoments, shots} from "../moments.mjs";
import {color} from "../theme";
import {Figure} from "../ui/Figure";
import {Footage} from "../ui/Footage";
import {Background} from "../ui/kit";
import type {SceneProps} from "./types";

// Stalled projects in gold, as in the deck; the pilots that deliver in the value teal.
const TONES = [color.arch, color.val];

/** Beat 2, the break: projects scrapped over the whiteboard, then a cut to the desk for the few pilots that
 *  deliver. */
export const Break: React.FC<SceneProps> = ({scene, cues, seconds}) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const m = breakMoments(scene, cues);
  const [forty, fortyLabel, five, fiveLabel] = scene.onScreen;
  const refs = scene.dataRefs as {sources: {cite: string}[]};
  const [board, desk] = shots(scene, cues, seconds);
  const figures = [[forty, fortyLabel], [five, fiveLabel]];
  return (
    <Background dots={0}>
      <Footage {...board} />
      <Footage {...desk} />
      {figures.map(([figure, label], i) => (
        <Figure
          key={figure} t={t} at={m.figures[i]} out={i === 0 ? m.cut - 0.1 : undefined} figure={figure} label={label}
          cite={refs.sources[i].cite} tone={TONES[i]}
        />
      ))}
    </Background>
  );
};
