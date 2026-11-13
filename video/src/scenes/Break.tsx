import React from "react";
import {useCurrentFrame, useVideoConfig} from "remotion";
import {breakMoments} from "../moments.mjs";
import {color, headingFont} from "../theme";
import {Figure} from "../ui/Figure";
import {Footage} from "../ui/Footage";
import {Background, ramp} from "../ui/kit";
import type {SceneProps} from "./types";

// Stalled projects in gold, as in the deck; the pilots that deliver in the value teal.
const TONES = [color.arch, color.val];

/** Beat 2, the break: projects scrapped over the whiteboard, a cut to the desk for the few pilots that deliver, then
 *  the insight that the risks show up too late. */
export const Break: React.FC<SceneProps> = ({scene, cues}) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const m = breakMoments(scene, cues);
  const [forty, fortyLabel, five, fiveLabel, late] = scene.onScreen;
  const refs = scene.dataRefs as {footage: string[]; sources: {cite: string}[]};
  const figures = [[forty, fortyLabel], [five, fiveLabel]];
  const lateShown = ramp(t, m.late, 0.45);
  return (
    <Background dots={0}>
      <Footage id={refs.footage[0]} to={m.cut + 0.3} />
      <Footage id={refs.footage[1]} from={m.cut} shade={0.5 + 0.2 * lateShown} />
      {figures.map(([figure, label], i) => (
        <Figure
          key={figure} t={t} at={m.figures[i]} out={i === 0 ? m.cut - 0.1 : m.late - 0.2} figure={figure} label={label}
          cite={refs.sources[i].cite} tone={TONES[i]}
        />
      ))}
      <div
        style={{
          position: "absolute", left: 140, top: 420, width: 1200, fontFamily: headingFont, fontSize: 104, fontWeight: 650,
          lineHeight: 1.05, color: color.ink, opacity: lateShown, transform: `translateY(${(1 - lateShown) * 30}px)`,
        }}
      >
        {late}
        <div style={{width: 160, height: 8, background: color.ragHigh, marginTop: 34, transform: `scaleX(${ramp(t, m.late + 0.3, 0.5)})`, transformOrigin: "left"}} />
      </div>
    </Background>
  );
};
