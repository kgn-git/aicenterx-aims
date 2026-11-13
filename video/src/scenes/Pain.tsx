import React from "react";
import {useCurrentFrame, useVideoConfig} from "remotion";
import {painMoments, shots} from "../moments.mjs";
import {color, headingFont} from "../theme";
import {Footage} from "../ui/Footage";
import {Background, ramp} from "../ui/kit";
import type {SceneProps} from "./types";

// A point already made steps back as the next lands, so the eye follows the voice while the list still builds.
const MADE = 0.45;

/** Beat 3, the pain: why AI is hard to deliver, one point at a time, each over its own shot: the complexity, the wish
 *  to do it responsibly, and the consultants an SME cannot pay for. */
export const Pain: React.FC<SceneProps> = ({scene, cues, seconds}) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const m = painMoments(scene, cues);
  return (
    <Background dots={0}>
      {shots(scene, cues, seconds).map((shot) => <Footage key={shot.clip} {...shot} shade={0.6} />)}
      <div style={{position: "absolute", left: 140, top: 300, width: 1100, display: "flex", flexDirection: "column", gap: 44}}>
        {scene.onScreen.map((point, i) => {
          const shown = ramp(t, m.points[i], 0.45);
          const next = m.points[i + 1] ?? Infinity;
          const dim = Number.isFinite(next) ? 1 - (1 - MADE) * ramp(t, next, 0.4) : 1;
          return (
            <div
              key={point}
              style={{
                display: "flex", alignItems: "center", gap: 32, opacity: shown * dim,
                transform: `translateY(${(1 - shown) * 30}px)`,
              }}
            >
              <div style={{width: 10, height: 84, background: color.ragHigh, flex: "0 0 auto"}} />
              <div style={{fontFamily: headingFont, fontSize: 84, fontWeight: 650, lineHeight: 1.05, color: color.ink}}>{point}</div>
            </div>
          );
        })}
      </div>
    </Background>
  );
};
