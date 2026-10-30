import React from "react";
import {interpolate, interpolateColors} from "remotion";
import {color, headingFont} from "../theme";
import {Card, ramp} from "../ui/kit";

const clamp = {extrapolateLeft: "clamp", extrapolateRight: "clamp"} as const;
const lerp = (k: number, from: number, to: number) => interpolate(k, [0, 1], [from, to], clamp);

/** The hook's years collapsing into the hour the journey took, over what that hour saved and the message it proves. */
export const Contrast: React.FC<{
  t: number; years: string; chip: string; message: string; counts: [number, string][];
  at: {collapse: number; tallies: number; message: number};
}> = ({t, years, chip, message, counts, at}) => {
  const c = ramp(t, at.collapse, 0.9);
  const width = lerp(c, 1400, 320);
  const height = lerp(c, 6, 92);
  return (
    <>
      <div
        style={{
          position: "absolute", left: 960 - 700, width: 1400, top: 170, textAlign: "center", fontFamily: headingFont,
          fontSize: 60, fontWeight: 650, color: color.ragHigh, opacity: ramp(t, 0, 0.4) * (1 - c),
        }}
      >
        {years}
      </div>
      <div
        style={{
          position: "absolute", left: 960 - width / 2, width, top: 300 - height / 2, height, borderRadius: height / 2,
          background: interpolateColors(c, [0, 1], [color.ragHigh, color.val]), display: "flex", alignItems: "center",
          justifyContent: "center", fontFamily: headingFont, fontSize: 50, fontWeight: 650, color: color.bgBase,
          opacity: ramp(t, 0, 0.4),
        }}
      >
        <span style={{opacity: ramp(t, at.collapse + 0.6, 0.3)}}>{chip}</span>
      </div>
      {counts.map(([n, label], i) => {
        const shown = ramp(t, at.tallies + i * 0.35, 0.5);
        return (
          <div
            key={label}
            style={{
              position: "absolute", left: 560 + i * 400 - 180, width: 360, top: 420, textAlign: "center", opacity: shown,
              transform: `translateY(${(1 - shown) * 20}px)`,
            }}
          >
            <div style={{fontFamily: headingFont, fontSize: 110, fontWeight: 650, color: color.gov, lineHeight: 1}}>{n}</div>
            <div style={{fontSize: 34, color: color.inkMuted, marginTop: 10}}>{label}</div>
          </div>
        );
      })}
      <div
        style={{
          position: "absolute", left: 210, right: 210, top: 660, textAlign: "center", fontFamily: headingFont,
          fontSize: 48, fontWeight: 600, lineHeight: 1.25, opacity: ramp(t, at.message, 0.6),
        }}
      >
        {message}
      </div>
    </>
  );
};

const GRID = {left: 560, top: 330, column: 240, gap: 40, card: 64, cardGap: 14};
const WAVES = [3, 2, 3];
const CV = {x: GRID.left + GRID.column / 2, y: GRID.top + GRID.card / 2};

const Pill: React.FC<{text: string; tone: string; shown: number; style: React.CSSProperties}> = ({text, tone, shown, style}) => (
  <Card
    style={{
      position: "absolute", display: "flex", alignItems: "center", gap: 16, padding: "18px 24px", fontSize: 28,
      fontWeight: 600, lineHeight: 1.25, borderColor: `${tone}aa`, opacity: shown, boxSizing: "border-box",
      transform: `scale(${0.92 + 0.08 * shown})`, ...style,
    }}
  >
    <span style={{width: 16, height: 16, flex: "0 0 16px", borderRadius: 8, background: tone}} />
    {text}
  </Card>
);

/** The camera pulls back from the one initiative to a portfolio in delivery waves, and the five capabilities still to
 *  come build around it, each as the voice names it; labels and outlines only, since none is a working screen yet. */
export const Portfolio: React.FC<{
  t: number; from: number; badge: string; heading: string; initiative: string; chip: string;
  capabilities: string[]; times: number[];
}> = ({t, from, badge, heading, initiative, chip, capabilities, times}) => {
  const pull = ramp(t, from, 1.4);
  const s = lerp(pull, 3, 1);
  const [models, lineage, programmes, architecture, intelligence] = capabilities;
  const shown = times.map((at) => ramp(t, at - 0.2, 0.5));
  const dash = -t * 40;
  return (
    <>
      <div style={{position: "absolute", left: 0, right: 0, top: 40, textAlign: "center", opacity: ramp(t, from + 0.6, 0.6)}}>
        <span
          style={{
            border: `2px solid ${color.gov}`, color: color.gov, borderRadius: 2, padding: "4px 18px", fontWeight: 600,
            fontSize: 24, letterSpacing: 1,
          }}
        >
          {badge}
        </span>
        <div style={{fontFamily: headingFont, fontSize: 56, fontWeight: 650, marginTop: 18}}>{heading}</div>
      </div>
      <div
        style={{
          position: "absolute", inset: 0, transformOrigin: `${CV.x}px ${CV.y}px`,
          transform: `translate(${(960 - CV.x) * (1 - pull)}px, ${(443 - CV.y) * (1 - pull)}px) scale(${s})`,
        }}
      >
        {WAVES.map((n, w) => {
          const x = GRID.left + w * (GRID.column + GRID.gap);
          return (
            <React.Fragment key={w}>
              <div style={{position: "absolute", left: x, top: GRID.top - 40, fontSize: 22, color: color.inkMuted, opacity: pull}}>
                Wave {w + 1}
              </div>
              {Array.from({length: n}, (_, i) => {
                const cv = w === 0 && i === 0;
                return (
                  <div
                    key={i}
                    style={{
                      position: "absolute", left: x, top: GRID.top + i * (GRID.card + GRID.cardGap), width: GRID.column,
                      height: GRID.card, boxSizing: "border-box", borderRadius: 4, padding: "10px 14px",
                      background: color.surface2, border: `${cv ? 3 : 1}px solid ${cv ? color.val : color.border}`,
                      opacity: cv ? 1 : ramp(t, from + 0.3 + (w + i) * 0.12, 0.5),
                    }}
                  >
                    {cv ? (
                      <>
                        <div style={{fontSize: 19, fontWeight: 600, whiteSpace: "nowrap"}}>{initiative}</div>
                        <div style={{fontSize: 16, color: color.val, fontWeight: 600, marginTop: 2}}>{chip}</div>
                      </>
                    ) : (
                      <>
                        <div style={{height: 12, width: "70%", background: color.border, borderRadius: 2}} />
                        <div style={{height: 10, width: "45%", background: color.border, borderRadius: 2, marginTop: 12}} />
                      </>
                    )}
                  </div>
                );
              })}
            </React.Fragment>
          );
        })}
      </div>
      <svg width="1920" height="886" style={{position: "absolute", left: 0, top: 0}}>
        <path d="M 560 262 v -12 H 1360 v 12" fill="none" stroke={color.ink} strokeWidth="2" opacity={shown[2]} />
        <line x1="470" y1="435" x2="560" y2="435" stroke={color.gov} strokeWidth="3" opacity={shown[0]} />
        <line
          x1="1360" y1="435" x2="1450" y2="435" stroke={color.val} strokeWidth="3" strokeDasharray="10 8"
          strokeDashoffset={dash} opacity={shown[1]}
        />
      </svg>
      <div style={{position: "absolute", left: 460, width: 1000, top: 208, textAlign: "center", fontSize: 26, fontWeight: 600, opacity: shown[2]}}>
        {programmes}
      </div>
      <Pill text={models} tone={color.gov} shown={shown[0]} style={{left: 110, top: 375, width: 360}} />
      <Pill text={lineage} tone={color.val} shown={shown[1]} style={{left: 1450, top: 375, width: 360}} />
      <Pill
        text={architecture} tone={color.arch} shown={shown[3]}
        style={{left: 560, top: 590, width: 800, justifyContent: "center", background: `${color.arch}22`}}
      />
      <Card
        style={{
          position: "absolute", left: 160, width: 1600, top: 700, height: 64, padding: "0 28px", boxSizing: "border-box",
          display: "flex", alignItems: "center", gap: 16, fontSize: 26, fontWeight: 600, opacity: shown[4], overflow: "hidden",
          borderColor: `${color.ragMedium}aa`,
          backgroundImage: `linear-gradient(90deg, transparent ${((t * 25) % 130) - 30}%, ${color.ragMedium}33 ${((t * 25) % 130) - 15}%, transparent ${(t * 25) % 130}%)`,
        }}
      >
        <span
          style={{
            width: 14, height: 14, borderRadius: 7, background: color.ragMedium,
            boxShadow: `0 0 ${10 + 8 * Math.sin(t * 4)}px ${color.ragMedium}`,
          }}
        />
        {intelligence}
      </Card>
    </>
  );
};
