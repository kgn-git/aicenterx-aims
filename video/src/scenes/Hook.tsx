import React from "react";
import {useCurrentFrame, useVideoConfig} from "remotion";
import {appFrameHeight, color, headingFont} from "../theme";
import {Background, ramp} from "../ui/kit";
import type {SceneProps} from "./types";

/** The problem: the cited incident's title, then its source. */
export const Hook: React.FC<SceneProps> = ({scene}) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const [title, source] = scene.onScreen;
  return (
    <Background>
      <div
        style={{
          position: "absolute", top: 0, left: 160, right: 160, height: appFrameHeight,
          display: "flex", flexDirection: "column", justifyContent: "center", gap: 40,
        }}
      >
        <div style={{width: 120 * ramp(t, 0.1, 0.8), height: 6, background: color.ragHigh}} />
        <div
          style={{
            fontFamily: headingFont, fontSize: 72, fontWeight: 600, lineHeight: 1.15,
            opacity: ramp(t, 0.2, 0.8), transform: `translateY(${(1 - ramp(t, 0.2, 0.8)) * 30}px)`,
          }}
        >
          {title}
        </div>
        <div style={{fontSize: 34, color: color.inkMuted, opacity: ramp(t, 1.4)}}>{source}</div>
      </div>
    </Background>
  );
};
