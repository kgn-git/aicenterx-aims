import React from "react";
import {useCurrentFrame, useVideoConfig} from "remotion";
import {color, headingFont, mutedInk} from "../theme";
import {Background, ramp} from "../ui/kit";
import type {SceneProps} from "./types";

const LINE_Y = 520;
const LEFT = 260;
const RIGHT = 1660;
const SPAN_Y = 660;

/** The problem as a timeline: the cited incident's title, its three milestones in turn, the years they span as the
 *  narration counts them, then its source. */
export const Hook: React.FC<SceneProps> = ({scene, cues}) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const [title, source, ...milestones] = scene.onScreen;
  const step = (RIGHT - LEFT) / (milestones.length - 1);
  const at = (i: number) => 0.6 + i * 0.9;
  const years = Number(milestones[milestones.length - 1].slice(0, 4)) - Number(milestones[0].slice(0, 4));
  const span = ramp(t, cues[cues.length - 1].start, 0.6);
  return (
    <Background>
      <div
        style={{
          position: "absolute", left: 160, right: 160, top: 150, fontFamily: headingFont, fontSize: 54, fontWeight: 600,
          lineHeight: 1.2, opacity: ramp(t, 0.1, 0.6), transform: `translateY(${(1 - ramp(t, 0.1, 0.6)) * 20}px)`,
        }}
      >
        {title}
      </div>
      <div
        style={{
          position: "absolute", left: LEFT, top: LINE_Y - 2, height: 4, background: color.border,
          width: (RIGHT - LEFT) * ramp(t, 0.4, at(milestones.length - 1) - 0.4),
        }}
      />
      {milestones.map((m, i) => {
        const [year, label] = m.split(" – ");
        const last = i === milestones.length - 1;
        const shown = ramp(t, at(i), 0.4);
        return (
          <div
            key={m}
            style={{
              position: "absolute", left: LEFT + i * step - 230, width: 460, top: LINE_Y - 110, textAlign: "center",
              opacity: shown, transform: `translateY(${(1 - shown) * 16}px)`,
            }}
          >
            <div style={{fontFamily: headingFont, fontSize: 64, fontWeight: 650, color: last ? color.ragHigh : color.ink}}>
              {year}
            </div>
            <div
              style={{
                width: 32, height: 32, borderRadius: 16, margin: "14px auto 0", border: `4px solid ${color.bgBase}`,
                background: last ? color.ragHigh : color.gov, transform: `scale(${0.4 + 0.6 * shown})`,
              }}
            />
            <div style={{marginTop: 22, fontSize: 32, lineHeight: 1.3}}>{label}</div>
          </div>
        );
      })}
      <svg width="1920" height="1080" style={{position: "absolute", left: 0, top: 0}}>
        <path
          d={`M ${LEFT} ${SPAN_Y - 24} v 24 H ${LEFT + (RIGHT - LEFT) * span} ${span === 1 ? `v -24` : ""}`}
          fill="none" stroke={color.ragHigh} strokeWidth="4" strokeLinecap="round" opacity={span}
        />
      </svg>
      <div
        style={{
          position: "absolute", left: LEFT, width: RIGHT - LEFT, top: SPAN_Y + 20, textAlign: "center", fontFamily: headingFont,
          fontSize: 64, fontWeight: 650, color: color.ragHigh, opacity: ramp(t, cues[cues.length - 1].start + 0.4, 0.4),
        }}
      >
        {years} years
      </div>
      <div style={{position: "absolute", left: 160, top: 820, fontSize: 30, color: mutedInk, opacity: ramp(t, 3.2)}}>
        {source}
      </div>
    </Background>
  );
};
