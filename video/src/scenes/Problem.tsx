import React from "react";
import {interpolateColors, useCurrentFrame, useVideoConfig} from "remotion";
import {problemMoments} from "../moments.mjs";
import {color, headingFont} from "../theme";
import {Background, ramp} from "../ui/kit";
import type {SceneProps} from "./types";

const RADIUS = 220;
const CIRCLES_Y = 430;
const TILE = 190;
const TILE_GAP = 400;
const TILES_Y = CIRCLES_Y;

// Line icons on a 24-unit grid, drawn in the stroke colour of their tile or circle.
const ICONS: Record<string, React.ReactNode> = {
  time: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3.5 2" />
    </>
  ),
  effort: (
    <>
      <circle cx="9" cy="8" r="3" />
      <path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6" />
      <circle cx="17" cy="9" r="2.5" />
      <path d="M15.5 14.2c3 .2 5.5 2.7 5.5 5.8" />
    </>
  ),
  harm: (
    <>
      <path d="M12 3l10 18H2z" />
      <path d="M12 10v5" />
      <path d="M12 18v.5" />
    </>
  ),
  govern: (
    <>
      <path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z" />
      <path d="M8.5 12l2.5 2.5 4.5-5" />
    </>
  ),
  value: (
    <>
      <path d="M4 4v16h16" />
      <path d="M7 15l4-4 3 3 5-6" />
      <path d="M15 8h4v4" />
    </>
  ),
};

const Icon: React.FC<{name: string; tone: string; size: number}> = ({name, tone, size}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={tone} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
    {ICONS[name]}
  </svg>
);

/** The problem in pictures: three empty rings fill with the time, effort and harm the voice names, and turn red as
 *  one cost on harm; then they give way to the two aims, governing responsibly and creating real value, which overlap
 *  into one target. */
export const Problem: React.FC<SceneProps> = ({scene, cues}) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const [time, effort, harm, govern, value] = scene.onScreen;
  const m = problemMoments(scene, cues);
  const red = ramp(t, m.marks[2], 0.4);
  const rings = ramp(t, m.rings, 0.4);
  const costs = 1 - ramp(t, m.costsOut, 0.4);
  const venn = ramp(t, m.circles, 0.5);
  const meet = ramp(t, m.meet, 1.0);
  const target = ramp(t, m.target, 0.5);
  // The dotted grid, the product's backdrop, arrives with the challenge the product answers.
  const dots = ramp(t, m.dots, 0.8);
  const tile = (label: string, icon: string, i: number) => {
    const shown = ramp(t, m.marks[i], 0.35);
    // Time and effort warm to the harm red once harm lands, so the three read as one cost.
    const tone = i === 2 ? color.ragHigh : interpolateColors(red, [0, 1], [color.ink, color.ragHigh]);
    return (
      <div
        key={label}
        style={{
          position: "absolute", left: 960 + (i - 1) * TILE_GAP - TILE / 2, top: TILES_Y - TILE / 2, width: TILE,
          textAlign: "center", opacity: rings * (0.3 + 0.7 * shown), transform: `scale(${0.9 + 0.1 * shown})`,
        }}
      >
        <div
          style={{
            position: "relative", width: TILE, height: TILE, borderRadius: TILE / 2, border: `4px solid ${tone}`,
            background: color.bgBase, display: "flex", alignItems: "center", justifyContent: "center", boxSizing: "border-box",
            overflow: "hidden",
          }}
        >
          <div style={{position: "absolute", inset: 0, background: tone, opacity: 0.12 * shown}} />
          <div style={{opacity: shown, transform: `translateY(${(1 - shown) * -30}px)`}}>
            <Icon name={icon} tone={tone} size={96} />
          </div>
        </div>
        <div style={{marginTop: 22, fontFamily: headingFont, fontSize: 48, fontWeight: 650, color: tone, opacity: shown}}>
          {label}
        </div>
      </div>
    );
  };
  const circle = (label: string, icon: string, tone: string, side: -1 | 1) => {
    const x = 960 + side * (RADIUS * 0.62 + 320 * (1 - meet));
    return (
      <div
        style={{
          position: "absolute", left: x - RADIUS, top: CIRCLES_Y - RADIUS, width: RADIUS * 2, height: RADIUS * 2,
          borderRadius: RADIUS, border: `4px solid ${tone}`, background: `${tone}1f`, opacity: venn,
          display: "flex", alignItems: "center", justifyContent: side < 0 ? "flex-start" : "flex-end",
          padding: "0 30px", boxSizing: "border-box",
        }}
      >
        <div style={{width: 260, display: "flex", flexDirection: "column", alignItems: "center", gap: 14}}>
          <Icon name={icon} tone={tone} size={84} />
          <div style={{textAlign: "center", fontSize: 46, fontWeight: 600, lineHeight: 1.15, color: tone}}>{label}</div>
        </div>
      </div>
    );
  };
  return (
    <Background dots={dots}>
      <div style={{position: "absolute", inset: 0, opacity: costs}}>
        <div
          style={{
            position: "absolute", left: 960 - TILE_GAP, top: TILES_Y - 3, height: 6, background: color.ragHigh,
            width: 2 * TILE_GAP * ramp(t, m.marks[0], m.marks[2] - m.marks[0] + 0.3), opacity: 0.35 + 0.65 * red,
          }}
        />
        {[time, effort, harm].map((label, i) => tile(label, ["time", "effort", "harm"][i], i))}
      </div>
      {circle(govern, "govern", color.gov, -1)}
      {circle(value, "value", color.val, 1)}
      <div
        style={{
          position: "absolute", left: 960 - 34, top: CIRCLES_Y - 34, width: 68, height: 68, borderRadius: 34,
          background: color.ink, boxShadow: `0 0 ${60 * target}px ${color.val}`, opacity: target,
          transform: `scale(${0.5 + 0.5 * target})`,
        }}
      />
    </Background>
  );
};
