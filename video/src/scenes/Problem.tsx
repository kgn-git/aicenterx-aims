import React from "react";
import {useCurrentFrame, useVideoConfig} from "remotion";
import {problemMoments} from "../moments.mjs";
import {color, headingFont} from "../theme";
import {Background, ramp} from "../ui/kit";
import type {SceneProps} from "./types";

const RADIUS = 220;
const CIRCLES_Y = 450;
// The statement's two lines sit above the circles, so both are on screen from the first word.
const STATEMENT_TOP = 70;
const STATEMENT_BOTTOM = 210;

/** The statement over the two aims, governing responsibly and creating real value, already on screen; as the voice
 *  turns to the challenge they overlap into one target. */
export const Problem: React.FC<SceneProps> = ({scene, cues}) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const [statement, challenge, govern, value] = scene.onScreen;
  const m = problemMoments(scene, cues);
  const first = 1 - ramp(t, m.split - 0.3, 0.5);
  const meet = ramp(t, m.meet, 1.2);
  const target = ramp(t, m.target, 0.5);
  // The dotted grid, the product's backdrop, arrives with the challenge the product answers.
  const dots = ramp(t, m.dots, 0.8);
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
  const circle = (label: string, tone: string, side: -1 | 1) => {
    const x = 960 + side * (RADIUS * 0.62 + 320 * (1 - meet));
    return (
      <div
        style={{
          position: "absolute", left: x - RADIUS, top: CIRCLES_Y - RADIUS, width: RADIUS * 2, height: RADIUS * 2,
          borderRadius: RADIUS, border: `4px solid ${tone}`, background: `${tone}1f`, opacity: ramp(t, m.circles, 0.5),
          display: "flex", alignItems: "center", justifyContent: side < 0 ? "flex-start" : "flex-end",
          padding: "0 44px", boxSizing: "border-box",
        }}
      >
        <div style={{width: 200, textAlign: "center", fontSize: 34, fontWeight: 600, lineHeight: 1.25, color: tone}}>
          {label}
        </div>
      </div>
    );
  };
  return (
    <Background dots={dots}>
      {reveal(statement, 0, m.split, {
        position: "absolute", left: 200, right: 200, top: STATEMENT_TOP, height: STATEMENT_BOTTOM - STATEMENT_TOP,
        textAlign: "center", textWrap: "balance", fontSize: 54, fontWeight: 500, opacity: first,
      })}
      {circle(govern, color.gov, -1)}
      {circle(value, color.val, 1)}
      <div
        style={{
          position: "absolute", left: 960 - 34, top: CIRCLES_Y - 34, width: 68, height: 68, borderRadius: 34,
          background: color.ink, boxShadow: `0 0 ${60 * target}px ${color.val}`, opacity: target,
          transform: `scale(${0.5 + 0.5 * target})`,
        }}
      />
      {reveal(challenge, m.split, m.end, {
        position: "absolute", left: 200, right: 200, top: CIRCLES_Y + RADIUS + 50, textAlign: "center", fontSize: 54,
        textWrap: "balance",
        fontWeight: 650, color: color.gov, opacity: ramp(t, m.split - 0.2, 0.4),
      })}
    </Background>
  );
};
