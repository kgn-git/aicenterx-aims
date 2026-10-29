import React from "react";
import {AbsoluteFill, Easing, interpolate} from "remotion";
import {appFrameHeight, bodyFont, color, headingFont, video} from "../theme";

export const TOP_BAR = 88;
export const SIDE = 48;
export const BODY = 28;

const clamp = {extrapolateLeft: "clamp", extrapolateRight: "clamp"} as const;

/** 0 before `from`, 1 after `from + length`, eased in between; times in seconds. */
export const ramp = (t: number, from: number, length = 0.5) =>
  interpolate(t, [from, from + length], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});

export const Background: React.FC<{children?: React.ReactNode}> = ({children}) => (
  <AbsoluteFill
    style={{
      background: `radial-gradient(1200px 800px at 70% -10%, ${color.bgG1}, transparent), ${color.bgBase}`,
      color: color.ink,
      fontFamily: bodyFont,
      fontSize: BODY,
    }}
  >
    {children}
  </AbsoluteFill>
);

/** The prototype's frame: brand bar on top, content laid out above the caption safe area. */
export const AppFrame: React.FC<{trail?: string; children?: React.ReactNode}> = ({trail, children}) => (
  <Background>
    <div
      style={{
        position: "absolute", top: 0, left: 0, right: 0, height: TOP_BAR, padding: `0 ${SIDE}px`,
        display: "flex", alignItems: "center", justifyContent: "space-between",
        borderBottom: `1px solid ${color.border}`, background: color.surface,
      }}
    >
      <div style={{fontFamily: headingFont, fontSize: 36, fontWeight: 650, display: "flex", alignItems: "center", gap: 14}}>
        <span style={{width: 14, height: 14, borderRadius: 7, background: color.gov, display: "inline-block"}} />
        AI Center X
      </div>
      {trail && <div style={{color: color.inkMuted}}>{trail}</div>}
    </div>
    <div style={{position: "absolute", top: TOP_BAR, left: 0, right: 0, height: appFrameHeight - TOP_BAR}}>{children}</div>
  </Background>
);

export const Card: React.FC<{style?: React.CSSProperties; children?: React.ReactNode}> = ({style, children}) => (
  <div
    style={{
      background: color.surface2, border: `1px solid ${color.border}`, borderRadius: 4, padding: 22,
      boxShadow: "0 8px 24px rgba(0,0,0,.4)", ...style,
    }}
  >
    {children}
  </div>
);

export const Button: React.FC<{label: string; pressed?: number; glow?: number; style?: React.CSSProperties}> = ({
  label, pressed = 0, glow = 0, style,
}) => (
  <div
    style={{
      display: "inline-flex", alignItems: "center", height: 64, padding: "0 28px", borderRadius: 2,
      background: color.gov, border: `1px solid ${color.gov}`, color: "#fff", fontWeight: 600,
      transform: `scale(${1 - 0.05 * pressed})`,
      boxShadow: `0 0 ${36 * glow}px ${color.gov}`,
      ...style,
    }}
  >
    {label}
  </div>
);

export const Checkbox: React.FC<{checked: number}> = ({checked}) => (
  <div
    style={{
      width: 36, height: 36, flex: "0 0 36px", borderRadius: 4, border: `2px solid ${checked ? color.gov : color.inkMuted}`,
      background: checked ? color.gov : "transparent", display: "flex", alignItems: "center", justifyContent: "center",
    }}
  >
    <svg width="24" height="24" viewBox="0 0 24 24" style={{opacity: checked, transform: `scale(${0.6 + 0.4 * checked})`}}>
      <path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke="#fff" strokeWidth="3" strokeLinecap="round" />
    </svg>
  </div>
);

/** A pointer that glides between keyframes {t, x, y} and dips at each time in `clicks`. */
export const Cursor: React.FC<{t: number; path: {t: number; x: number; y: number}[]; clicks?: number[]}> = ({
  t, path, clicks = [],
}) => {
  const times = path.map((p) => p.t);
  const ease = {...clamp, easing: Easing.inOut(Easing.cubic)};
  const x = path.length > 1 ? interpolate(t, times, path.map((p) => p.x), ease) : path[0].x;
  const y = path.length > 1 ? interpolate(t, times, path.map((p) => p.y), ease) : path[0].y;
  const press = Math.max(0, ...clicks.map((c) => 1 - Math.abs(t - c) / 0.15));
  return (
    <svg
      width="44" height="44" viewBox="0 0 24 24"
      style={{position: "absolute", left: x, top: y, transform: `scale(${1 - 0.15 * press})`, transformOrigin: "0 0", zIndex: 10}}
    >
      <path d="M3 2l17 9.5-7.2 1.6L9.5 21z" fill="#fff" stroke={color.bgBase} strokeWidth="1.5" strokeLinejoin="round" />
    </svg>
  );
};

/** The confirmation that slides in, by default at the bottom right above the caption safe area. */
export const Toast: React.FC<{text: string; shown: number; style?: React.CSSProperties}> = ({text, shown, style}) => (
  <div
    style={{
      position: "absolute", right: SIDE, bottom: video.height - appFrameHeight + 28, opacity: shown,
      transform: `translateY(${(1 - shown) * 24}px)`, background: color.surface2, border: `1px solid ${color.ragLow}`,
      borderLeft: `8px solid ${color.ragLow}`, borderRadius: 4, padding: "18px 28px", fontWeight: 600,
      boxShadow: "0 8px 24px rgba(0,0,0,.4)", zIndex: 5, ...style,
    }}
  >
    {text}
  </div>
);

/** The agent's steps, each ticking off in turn between `from` and `from + length` seconds. */
export const AgentRun: React.FC<{steps: string[]; t: number; from: number; length: number}> = ({
  steps, t, from, length,
}) => (
  <Card style={{width: 820, display: "flex", flexDirection: "column", gap: 16}}>
    {steps.map((step, i) => {
      const at = from + (length * (i + 1)) / steps.length;
      const done = t >= at;
      const active = !done && t >= at - length / steps.length;
      return (
        <div key={step} style={{display: "flex", alignItems: "center", gap: 18, opacity: done || active ? 1 : 0.45}}>
          <div
            style={{
              width: 30, height: 30, borderRadius: 15, flex: "0 0 30px",
              border: `3px solid ${done ? color.ragLow : color.gov}`, background: done ? color.ragLow : "transparent",
              transform: active ? `rotate(${t * 360}deg)` : undefined,
              borderTopColor: active ? "transparent" : undefined,
            }}
          />
          {step}
        </div>
      );
    })}
  </Card>
);
