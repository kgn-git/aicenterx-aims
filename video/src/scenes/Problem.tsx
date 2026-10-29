import React from "react";
import {useCurrentFrame, useVideoConfig} from "remotion";
import {appFrameHeight, color, headingFont} from "../theme";
import {Background, ramp} from "../ui/kit";
import type {SceneProps} from "./types";

/** The question the product answers, revealed word by word as the voice says it. */
export const Problem: React.FC<SceneProps> = ({scene, cues}) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const words = scene.onScreen[0].split(" ");
  const end = cues[cues.length - 1].end;
  return (
    <Background>
      <div
        style={{
          position: "absolute", left: 200, right: 200, top: 0, height: appFrameHeight, display: "flex",
          flexDirection: "column", justifyContent: "center", gap: 48,
        }}
      >
        <div style={{fontFamily: headingFont, fontSize: 76, fontWeight: 600, lineHeight: 1.2}}>
          {words.map((w, i) => (
            <span key={i} style={{opacity: 0.15 + 0.85 * ramp(t, (end * i) / words.length, 0.3)}}>
              {w}{" "}
            </span>
          ))}
        </div>
        <div style={{width: 260 * ramp(t, end - 0.4, 0.5), height: 6, background: color.gov}} />
      </div>
    </Background>
  );
};
