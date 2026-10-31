import React from "react";
import {AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig} from "remotion";
import {appFrameHeight, bodyFont, color, headingFont, video, mutedInk} from "../theme";

export const TOP_BAR = 88;
export const SIDE = 48;
export const BODY = 28;

const clamp = {extrapolateLeft: "clamp", extrapolateRight: "clamp"} as const;

/** 0 before `from`, 1 after `from + length`, eased in between; times in seconds. */
export const ramp = (t: number, from: number, length = 0.5) =>
  interpolate(t, [from, from + length], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});

/** When the voice reaches `phrase`, in seconds: the cues share a clip by characters, so a phrase's place in the text
 *  is its place in time, to within a pause. */
export const spokenAt = (narration: string, phrase: string, end: number) => {
  const at = narration.indexOf(phrase);
  if (at < 0) throw new Error(`The narration no longer says "${phrase}", so the scene cannot time its beats.`);
  return (end * at) / narration.length;
};

/** A faint dot grid drifting slowly behind every scene, the agents' presence; it brightens while one works. */
const AgentGrid: React.FC<{shown: number}> = ({shown}) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  return (
    <div
      style={{
        position: "absolute", inset: 0, opacity: shown * 0.5, pointerEvents: "none",
        backgroundImage: `radial-gradient(circle, ${color.gov} 1.6px, transparent 2px)`, backgroundSize: "48px 48px",
        backgroundPosition: `${t * 12}px ${t * 6}px`,
        maskImage: "radial-gradient(ellipse at 50% 40%, black 20%, transparent 75%)",
      }}
    />
  );
};

/** The prototype's backdrop under the dot grid; `grid` is 1 while an agent works. */
/** The video's backdrop; `dots` fades the dotted grid as a whole, `grid` brightens it while the agent works. */
export const Background: React.FC<{grid?: number; dots?: number; children?: React.ReactNode}> = ({
  grid = 0, dots = 1, children,
}) => (
  <AbsoluteFill
    style={{
      background: `radial-gradient(1200px 800px at 70% -10%, ${color.bgG1}, transparent), ${color.bgBase}`,
      color: color.ink,
      fontFamily: bodyFont,
      fontSize: BODY,
    }}
  >
    <AgentGrid shown={dots * (0.25 + 0.95 * grid)} />
    {children}
  </AbsoluteFill>
);

/** The prototype's frame: brand bar on top, content laid out above the caption safe area. */
export const AppFrame: React.FC<{trail?: string; grid?: number; children?: React.ReactNode}> = ({trail, grid, children}) => (
  <Background grid={grid}>
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
      {trail && <div style={{color: mutedInk}}>{trail}</div>}
    </div>
    <div style={{position: "absolute", top: TOP_BAR, left: 0, right: 0, height: appFrameHeight - TOP_BAR}}>{children}</div>
  </Background>
);

/** 1 at the middle of the `length` seconds after `at`, 0 outside them: a single pulse. */
export const bump = (t: number, at: number, length = 0.4) => Math.max(0, 1 - Math.abs(t - at - length / 2) / (length / 2));

/** A panel; `accent` draws a strip down its left edge that a change of border colour, such as a tick, never repaints. */
export const Card: React.FC<{style?: React.CSSProperties; accent?: string; children?: React.ReactNode}> = ({
  style, accent, children,
}) => (
  <div
    style={{
      position: "relative", background: color.surface2, border: `1px solid ${color.border}`, borderRadius: 4, padding: 22,
      boxShadow: "0 8px 24px rgba(0,0,0,.4)", ...style,
    }}
  >
    {accent && (
      <div style={{position: "absolute", left: 0, top: 0, bottom: 0, width: 6, background: accent, borderRadius: "4px 0 0 4px"}} />
    )}
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
      width: 36, height: 36, flex: "0 0 36px", borderRadius: 4, border: `2px solid ${checked ? color.gov : mutedInk}`,
      background: checked ? color.gov : "transparent", display: "flex", alignItems: "center", justifyContent: "center",
    }}
  >
    <svg width="24" height="24" viewBox="0 0 24 24" style={{opacity: checked, transform: `scale(${0.6 + 0.4 * checked})`}}>
      <path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke="#fff" strokeWidth="3" strokeLinecap="round" />
    </svg>
  </div>
);

/** A pointer that glides between keyframes {t, x, y} and dips at each time in `clicks`. */
export const Cursor: React.FC<{t: number; path: {t: number; x: number; y: number}[]; clicks?: number[]; shown?: number}> = ({
  t, path, clicks = [], shown = 1,
}) => {
  const times = path.map((p) => p.t);
  const ease = {...clamp, easing: Easing.inOut(Easing.cubic)};
  const x = path.length > 1 ? interpolate(t, times, path.map((p) => p.x), ease) : path[0].x;
  const y = path.length > 1 ? interpolate(t, times, path.map((p) => p.y), ease) : path[0].y;
  const press = Math.max(0, ...clicks.map((c) => 1 - Math.abs(t - c) / 0.15));
  return (
    <svg
      width="44" height="44" viewBox="0 0 24 24"
      style={{
        position: "absolute", left: x, top: y, transform: `scale(${1 - 0.15 * press})`, transformOrigin: "0 0", zIndex: 10,
        opacity: shown,
      }}
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
      transform: `translateY(${(1 - shown) * 24}px)`, background: `linear-gradient(${color.ragLow}2e, ${color.ragLow}2e), ${color.surface2}`,
      border: `1px solid ${color.ragLow}`, borderLeft: `8px solid ${color.ragLow}`, borderRadius: 4, padding: "18px 28px",
      fontWeight: 600, boxShadow: "0 8px 24px rgba(0,0,0,.4)", zIndex: 5, display: "flex", alignItems: "center", gap: 14,
      ...style,
    }}
  >
    <svg width="26" height="26" viewBox="0 0 24 24">
      <path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke={color.ragLow} strokeWidth="3.5" strokeLinecap="round" />
    </svg>
    {text}
  </div>
);

const MONO = "ui-monospace, Consolas, 'Courier New', monospace";

/** A dot that breathes slowly, so the agent's header reads as live. */
const Pulse: React.FC<{t: number; size?: number}> = ({t, size = 14}) => (
  <span
    style={{
      width: size, height: size, borderRadius: size / 2, flex: `0 0 ${size}px`, display: "inline-block",
      background: color.gov, boxShadow: `0 0 ${10 + 8 * Math.sin(t * 4)}px ${color.gov}`,
    }}
  />
);

/** The agent's steps under an "AI agent" header, each ticking off in turn between `from` and `from + length`
 *  seconds. */
export const AgentRun: React.FC<{steps: string[]; t: number; from: number; length: number}> = ({
  steps, t, from, length,
}) => (
  <Card
    style={{
      width: 820, display: "flex", flexDirection: "column", gap: 16, border: "2px solid transparent",
      // A border that keeps turning while the agent works, so the box reads as live rather than as a prompt.
      background: `linear-gradient(${color.surface2}, ${color.surface2}) padding-box, conic-gradient(from ${(t * 140) % 360}deg, ${color.gov}, ${color.val}, ${color.gov}44, ${color.gov}) border-box`,
    }}
  >
    <div style={{display: "flex", alignItems: "center", gap: 14, color: color.gov, fontWeight: 600, fontFamily: MONO}}>
      <Pulse t={t} />
      AI agent
    </div>
    {steps.map((step, i) => {
      const at = from + (length * (i + 1)) / steps.length;
      const done = t >= at;
      const active = !done && t >= at - length / steps.length;
      return (
        <div key={step} style={{display: "flex", alignItems: "center", gap: 18, opacity: done || active ? 1 : 0.45}}>
          <div
            style={{
              width: 30, height: 30, borderRadius: 15, flex: "0 0 30px", display: "flex", alignItems: "center",
              justifyContent: "center", border: `3px solid ${done ? color.ragLow : color.gov}`,
              background: done ? color.ragLow : "transparent",
              transform: active ? `rotate(${t * 360}deg)` : undefined, borderTopColor: active ? "transparent" : undefined,
            }}
          >
            {done && (
              <svg width="18" height="18" viewBox="0 0 24 24">
                <path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke={color.bgBase} strokeWidth="3.5" strokeLinecap="round" />
              </svg>
            )}
          </div>
          {step}
        </div>
      );
    })}
  </Card>
);

/** The agent's status in the brand bar: its current step while it runs, then that the choice is the user's. */
export const AgentStatus: React.FC<{
  steps: string[]; t: number; from: number; length: number; until?: number; after?: string;
}> = ({steps, t, from, length, until = from + length, after = "Suggestions ready. You decide what to save."}) => {
  // The last step holds until `until`, when the suggestions are written, so "ready" never shows before the cards have landed.
  const i = t >= until ? steps.length : Math.min(steps.length - 1, Math.floor(((t - from) / length) * steps.length));
  return (
    <div
      style={{
        position: "absolute", top: -TOP_BAR, left: 0, right: 0, height: TOP_BAR, display: "flex", alignItems: "center",
        justifyContent: "center", gap: 14, fontFamily: MONO, fontSize: 24, color: mutedInk, opacity: ramp(t, from, 0.3),
        pointerEvents: "none",
      }}
    >
      <Pulse t={t} size={12} />
      <span style={{color: color.gov, fontWeight: 600}}>AI agent</span>·<span>{i < steps.length ? steps[i] : after}</span>
    </div>
  );
};

/** A citation chip, tinted by source, that lands just after its card and can pulse once to draw the eye. */
export const SourceChip: React.FC<{tone: string; shown?: number; pulse?: number; children?: React.ReactNode}> = ({
  tone, shown = 1, pulse = 0, children,
}) => (
  <span
    style={{
      display: "inline-block", background: `${tone}22`, border: `1px solid ${tone}88`, color: tone, borderRadius: 2,
      padding: "2px 12px", fontSize: 24, fontWeight: 600, maxWidth: "100%", opacity: shown,
      transform: `translateY(${(1 - shown) * 10}px) scale(${0.9 + 0.1 * shown + 0.08 * pulse})`, transformOrigin: "0 50%",
      boxShadow: pulse ? `0 0 ${18 * pulse}px ${tone}` : undefined,
    }}
  >
    {children}
  </span>
);

export const KIND_COLOUR: Record<string, string> = {
  "fine-tuning": color.arch, "agent workflow": color.gov, "human feedback": color.val,
};

/** An enhancement's kind as a chip in its colour, in sentence case. */
export const KindTag: React.FC<{kind: string}> = ({kind}) => (
  <SourceChip tone={KIND_COLOUR[kind]}>{kind[0].toUpperCase() + kind.slice(1)}</SourceChip>
);

/** How far a Zoom between `from` and `to` seconds is in at `t`, 0 to 1, so a scene can hide what the zoom hides.
 *  A re-voiced take can move the cue that ends the zoom; holding at least half a second avoids a half-zoom lurch. */
export const zoomLevel = (t: number, from: number, to: number) =>
  ramp(t, from, 0.5) * (1 - ramp(t, Math.max(to, from + 1), 0.5));

/** Moves `focus` (in the layer's own pixels) to the middle and enlarges it between `from` and `to` seconds, so a
 *  phone-sized viewer can read the card being narrated. */
export const Zoom: React.FC<{
  t: number; focus: {x: number; y: number}; from: number; to: number; scale?: number; children?: React.ReactNode;
}> = ({t, focus, from, to, scale = 1.7, children}) => {
  const z = zoomLevel(t, from, to);
  const middle = {x: video.width / 2, y: (appFrameHeight - TOP_BAR) / 2};
  return (
    <div style={{position: "absolute", inset: 0, overflow: "hidden"}}>
      <div
        style={{
          position: "absolute", inset: 0, transformOrigin: `${focus.x}px ${focus.y}px`,
          transform: `translate(${z * (middle.x - focus.x)}px, ${z * (middle.y - focus.y)}px) scale(${1 + (scale - 1) * z})`,
        }}
      >
        {children}
      </div>
    </div>
  );
};
