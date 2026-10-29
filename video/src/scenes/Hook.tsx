import React from "react";
import {useCurrentFrame, useVideoConfig} from "remotion";
import {color, headingFont} from "../theme";
import {Background, ramp} from "../ui/kit";
import type {SceneProps} from "./types";

const LINE_Y = 520;
const LEFT = 260;
const RIGHT = 1660;

/** The problem as a timeline: the cited incident's title, its three milestones in turn, then its source. */
export const Hook: React.FC<SceneProps> = ({scene}) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const [title, source, ...milestones] = scene.onScreen;
  const step = (RIGHT - LEFT) / (milestones.length - 1);
  const at = (i: number) => 0.6 + i * 0.9;
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
      <div style={{position: "absolute", left: 160, top: 760, fontSize: 30, color: color.inkMuted, opacity: ramp(t, 3.2)}}>
        {source}
      </div>
    </Background>
  );
};
