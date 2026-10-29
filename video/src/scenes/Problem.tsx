import React from "react";
import {useCurrentFrame, useVideoConfig} from "remotion";
import {appFrameHeight, color, headingFont} from "../theme";
import {Background, ramp} from "../ui/kit";
import type {SceneProps} from "./types";

/** The statement, then the challenge set apart in the brand colour, each revealed word by word as the voice says
 *  it; the voice's time is split between them by their share of the characters, as the cues are. */
export const Problem: React.FC<SceneProps> = ({scene, cues}) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const [statement, challenge] = scene.onScreen;
  const end = cues[cues.length - 1].end;
  const split = (end * statement.length) / (statement.length + challenge.length);
  const reveal = (text: string, from: number, to: number, style: React.CSSProperties) => {
    const words = text.split(" ");
    return (
      <div style={{fontFamily: headingFont, lineHeight: 1.2, ...style}}>
        {words.map((w, i) => (
          <span key={i} style={{opacity: 0.15 + 0.85 * ramp(t, from + ((to - from) * i) / words.length, 0.3)}}>
            {w}{" "}
          </span>
        ))}
      </div>
    );
  };
  return (
    <Background>
      <div
        style={{
          position: "absolute", left: 200, right: 200, top: 0, height: appFrameHeight, display: "flex",
          flexDirection: "column", justifyContent: "center", gap: 40,
        }}
      >
        {reveal(statement, 0, split, {fontSize: 66, fontWeight: 500})}
        <div style={{width: 260 * ramp(t, split - 0.4, 0.5), height: 6, background: color.gov}} />
        {reveal(challenge, split, end, {fontSize: 84, fontWeight: 650, color: color.gov})}
      </div>
    </Background>
  );
};
