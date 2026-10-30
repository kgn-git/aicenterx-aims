import React from "react";
import {useCurrentFrame, useVideoConfig} from "remotion";
import {color, headingFont} from "../theme";
import {Background, ramp, spokenAt} from "../ui/kit";
import type {SceneProps} from "./types";

const LEFT = 260;
const RIGHT = 1660;
const BAR_Y = 520;
const RADIUS = 220;
const CIRCLES_Y = 400;

/** The statement over the hook's years, marked with the time, effort and harm it names as the voice says each; then
 *  the challenge as two aims, governing responsibly and creating real value, that overlap into one target. */
export const Problem: React.FC<SceneProps> = ({scene, cues}) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const [statement, challenge, years, ...labels] = scene.onScreen;
  const marks = labels.slice(0, 3);
  const [govern, value] = labels.slice(3);
  const end = cues[cues.length - 1].end;
  const split = (end * statement.length) / (statement.length + challenge.length);
  const first = 1 - ramp(t, split - 0.3, 0.5);
  const meet = ramp(t, split + 0.2, 1.2);
  const target = ramp(t, spokenAt(scene.narration, "create real value", end) + 0.2, 0.5);
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
          borderRadius: RADIUS, border: `4px solid ${tone}`, background: `${tone}1f`, opacity: ramp(t, split, 0.5),
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
    <Background>
      <div style={{position: "absolute", inset: 0, opacity: first}}>
        {reveal(statement, 0, split, {position: "absolute", left: 200, right: 200, top: 150, fontSize: 58, fontWeight: 500})}
        <div
          style={{
            position: "absolute", left: LEFT, top: BAR_Y - 3, height: 6, background: color.ragHigh,
            width: (RIGHT - LEFT) * ramp(t, 0.2, 0.8),
          }}
        />
        {marks.map((m, i) => {
          const shown = ramp(t, spokenAt(statement, m.toLowerCase(), split) - 0.1, 0.4);
          const harm = i === marks.length - 1;
          return (
            <div
              key={m}
              style={{
                position: "absolute", left: LEFT + ((RIGHT - LEFT) * (2 * i + 1)) / (2 * marks.length) - 150, width: 300, top: BAR_Y - 96,
                textAlign: "center", opacity: shown, transform: `translateY(${(1 - shown) * 16}px)`,
              }}
            >
              <div style={{fontSize: 40, fontWeight: 600, color: harm ? color.ragHigh : color.ink}}>{m}</div>
              <div
                style={{
                  position: "absolute", left: 135, top: 81, width: 30, height: 30, borderRadius: 15,
                  border: `4px solid ${color.bgBase}`, boxSizing: "border-box",
                  background: harm ? color.ragHigh : color.inkMuted, transform: `scale(${0.4 + 0.6 * shown})`,
                }}
              />
            </div>
          );
        })}
        <div
          style={{
            position: "absolute", left: LEFT, width: RIGHT - LEFT, top: BAR_Y + 40, textAlign: "center",
            fontFamily: headingFont, fontSize: 60, fontWeight: 650, color: color.ragHigh, opacity: ramp(t, 0.6, 0.5),
          }}
        >
          {years}
        </div>
      </div>
      {circle(govern, color.gov, -1)}
      {circle(value, color.val, 1)}
      <div
        style={{
          position: "absolute", left: 960 - 34, top: CIRCLES_Y - 34, width: 68, height: 68, borderRadius: 34,
          background: color.ink, boxShadow: `0 0 ${60 * target}px ${color.val}`, opacity: target,
          transform: `scale(${0.5 + 0.5 * target})`,
        }}
      />
      {reveal(challenge, split, end, {
        position: "absolute", left: 200, right: 200, top: CIRCLES_Y + RADIUS + 60, textAlign: "center", fontSize: 54,
        textWrap: "balance",
        fontWeight: 650, color: color.gov, opacity: ramp(t, split - 0.2, 0.4),
      })}
    </Background>
  );
};
