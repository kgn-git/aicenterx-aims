import React from "react";
import {random, useCurrentFrame, useVideoConfig} from "remotion";
import {color} from "../theme";

const COLUMNS = 18;
const WIDTH = 1920;
const HEIGHT = 1080;
const BAR = 34;
// One rise, stall and fade of an ordinary column, in seconds; each starts at its own phase so they never pulse together.
const CYCLE = 7;
const RISE = 3.2;
const HOLD = 1.2;
const FADE = 1.6;
// The one column that keeps rising, as the AI that delivers value does, sits right of centre.
const HERO = 12;
const PARTICLES = 3;

const TONES = [color.gov, color.val, color.arch];

/** How far a stalling column has risen (0..1 of its own height) and how bright it is, at time `t` of its cycle. */
const stalling = (t: number) => {
  if (t < RISE) return {grown: 1 - (1 - t / RISE) ** 3, glow: 1};
  if (t < RISE + HOLD) return {grown: 1, glow: 1};
  if (t < RISE + HOLD + FADE) return {grown: 1, glow: 1 - (t - RISE - HOLD) / FADE};
  return {grown: 0, glow: 0};
};

/** The opening's moving light, drawn rather than filmed: columns of light rise like a bar chart, most stall and
 *  dissolve before the top, and one keeps climbing. `shown` dims it under the figures. */
export const LightColumns: React.FC<{shown: number}> = ({shown}) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const step = WIDTH / COLUMNS;
  return (
    <svg width={WIDTH} height={HEIGHT} style={{position: "absolute", inset: 0, opacity: shown}}>
      <defs>
        {TONES.map((tone, i) => (
          <linearGradient key={tone} id={`light-${i}`} x1="0" y1="1" x2="0" y2="0">
            <stop offset="0" stopColor={tone} stopOpacity={0} />
            <stop offset="0.75" stopColor={tone} stopOpacity={0.35} />
            <stop offset="1" stopColor={tone} stopOpacity={0.9} />
          </linearGradient>
        ))}
        <radialGradient id="light-floor" cx="0.5" cy="1" r="0.7">
          <stop offset="0" stopColor={color.gov} stopOpacity={0.28} />
          <stop offset="1" stopColor={color.gov} stopOpacity={0} />
        </radialGradient>
      </defs>
      <rect x={0} y={HEIGHT * 0.45} width={WIDTH} height={HEIGHT * 0.55} fill="url(#light-floor)" />
      {Array.from({length: COLUMNS}, (_, i) => {
        const tone = i === HERO ? 2 : Math.floor(random(`tone-${i}`) * 2);
        const reach = HEIGHT * (0.3 + 0.4 * random(`reach-${i}`));
        const {grown, glow} = i === HERO
          ? {grown: Math.min(1, t / 16), glow: 1}
          : stalling((t + random(`phase-${i}`) * CYCLE) % CYCLE);
        const height = (i === HERO ? HEIGHT * 0.92 : reach) * grown;
        const x = i * step + (step - BAR) / 2;
        return (
          <g key={i} opacity={glow * (i === HERO ? 1 : 0.75)}>
            <rect x={x} y={HEIGHT - height} width={BAR} height={height} fill={`url(#light-${tone})`} rx={4} />
            <rect x={x - 6} y={HEIGHT - height - 3} width={BAR + 12} height={6} rx={3} fill={TONES[tone]} opacity={0.9} />
            {Array.from({length: PARTICLES}, (__, k) => {
              const rise = ((t * (40 + 30 * random(`speed-${i}-${k}`)) + random(`start-${i}-${k}`) * height) % Math.max(height, 1));
              return <circle key={k} cx={x + BAR * random(`x-${i}-${k}`)} cy={HEIGHT - rise} r={2.5} fill={TONES[tone]} opacity={0.8} />;
            })}
          </g>
        );
      })}
    </svg>
  );
};
