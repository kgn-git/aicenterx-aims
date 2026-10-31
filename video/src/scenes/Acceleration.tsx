import React from "react";
import {interpolate, interpolateColors} from "remotion";
import {appFrameHeight, color, headingFont, video, mutedInk} from "../theme";
import {ramp} from "../ui/kit";

const clamp = {extrapolateLeft: "clamp", extrapolateRight: "clamp"} as const;
const lerp = (k: number, from: number, to: number) => interpolate(k, [0, 1], [from, to], clamp);
const MIDDLE = {x: video.width / 2, y: appFrameHeight / 2};
// The hook's timeline width, so the years it spans come back as the same bar.
const SPAN = 1400;

/** The hook's years collapsing into the hour the journey took, over what that hour saved and the message it proves;
 *  the years stay, struck through, so before and after share a frame. */
export const Contrast: React.FC<{
  t: number; years: string; chip: string; message: string; counts: [number, string][];
  at: {collapse: number; tallies: number; message: number};
}> = ({t, years, chip, message, counts, at}) => {
  const c = ramp(t, at.collapse, 0.9);
  const width = lerp(c, SPAN, 320);
  const height = lerp(c, 6, 92);
  return (
    <>
      <div
        style={{
          position: "absolute", left: MIDDLE.x - SPAN / 2, width: SPAN, top: 170, textAlign: "center",
          fontFamily: headingFont, fontSize: 60, fontWeight: 650, color: color.ragHigh,
          opacity: ramp(t, 0, 0.4) * (1 - 0.55 * c),
        }}
      >
        <span style={{position: "relative"}}>
          {years}
          <span
            style={{
              position: "absolute", left: 0, top: "52%", height: 5, width: `${100 * ramp(t, at.collapse + 0.5, 0.4)}%`,
              background: color.ragHigh,
            }}
          />
        </span>
      </div>
      <div
        style={{
          position: "absolute", left: MIDDLE.x - width / 2, width, top: 300 - height / 2, height, borderRadius: height / 2,
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
              position: "absolute", left: MIDDLE.x + (i - 1) * 400 - 180, width: 360, top: 420, textAlign: "center",
              opacity: shown, transform: `translateY(${(1 - shown) * 20}px)`,
            }}
          >
            <div style={{fontFamily: headingFont, fontSize: 110, fontWeight: 650, color: color.gov, lineHeight: 1}}>{Math.round(n * ramp(t, at.tallies + i * 0.35, 0.8))}</div>
            <div style={{fontSize: 34, color: mutedInk, marginTop: 10}}>{label}</div>
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
const GRID_RIGHT = GRID.left + WAVES.length * GRID.column + (WAVES.length - 1) * GRID.gap;
const CV = {x: GRID.left + GRID.column / 2, y: GRID.top + GRID.card / 2};
const PILL = {width: 420, gap: 80, top: 360, line: 435};

/** A capability still to come: a dashed outline with nothing moving inside it, tagged as coming, so it never reads
 *  as a working screen next to the solid initiative card. */
const Planned: React.FC<{text: string; tag: string; tone: string; shown: number; style: React.CSSProperties}> = ({
  text, tag, tone, shown, style,
}) => (
  <div
    style={{
      position: "absolute", display: "flex", alignItems: "center", gap: 16, padding: "22px 26px", fontSize: 32,
      fontWeight: 600, lineHeight: 1.25, border: `3px dashed ${tone}`, borderRadius: 4, boxSizing: "border-box",
      opacity: shown, transform: `scale(${0.92 + 0.08 * shown})`, ...style,
    }}
  >
    <span
      style={{
        position: "absolute", left: 18, top: -15, padding: "0 10px", background: color.bgBase, color: tone, fontSize: 20,
        fontWeight: 600, lineHeight: "28px",
      }}
    >
      {tag}
    </span>
    <span style={{width: 16, height: 16, flex: "0 0 16px", borderRadius: 8, background: tone}} />
    {text}
  </div>
);

/** The camera pulls back from the one initiative to a portfolio in delivery waves, and the five capabilities still to
 *  come build around it, each as the voice names it; the grid then steps back so they carry the frame. */
export const Portfolio: React.FC<{
  t: number; from: number; tag: string; heading: string; initiative: string; chip: string; wave: string;
  capabilities: string[]; times: number[];
}> = ({t, from, tag, heading, initiative, chip, wave, capabilities, times}) => {
  const pull = ramp(t, from, 1.4);
  const s = lerp(pull, 3, 1);
  const [models, lineage, programmes, architecture, intelligence] = capabilities;
  const shown = times.map((at) => ramp(t, at - 0.2, 0.5));
  const grid = 1 - 0.5 * ramp(t, times[0], 0.6);
  return (
    <>
      <div
        style={{
          position: "absolute", left: 0, right: 0, top: 50, textAlign: "center", fontFamily: headingFont, fontSize: 56,
          fontWeight: 650, opacity: ramp(t, from + 0.6, 0.6),
        }}
      >
        {heading}
      </div>
      <div
        style={{
          position: "absolute", inset: 0, transformOrigin: `${CV.x}px ${CV.y}px`, opacity: grid,
          transform: `translate(${(MIDDLE.x - CV.x) * (1 - pull)}px, ${(MIDDLE.y - CV.y) * (1 - pull)}px) scale(${s})`,
        }}
      >
        {WAVES.map((n, w) => {
          const x = GRID.left + w * (GRID.column + GRID.gap);
          return (
            <React.Fragment key={w}>
              <div style={{position: "absolute", left: x, top: GRID.top - 44, fontSize: 28, color: mutedInk, opacity: pull}}>
                {wave} {w + 1}
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
      <svg width={video.width} height={appFrameHeight} style={{position: "absolute", left: 0, top: 0}}>
        <path
          d={`M ${GRID.left} 262 v -12 H ${GRID_RIGHT} v 12`} fill="none" stroke={color.ink} strokeWidth="2"
          opacity={shown[2]}
        />
        <line
          x1={GRID.left - PILL.gap} y1={PILL.line} x2={GRID.left} y2={PILL.line} stroke={color.gov} strokeWidth="3"
          strokeDasharray="10 8" opacity={shown[0]}
        />
        <line
          x1={GRID_RIGHT} y1={PILL.line} x2={GRID_RIGHT + PILL.gap} y2={PILL.line} stroke={color.val} strokeWidth="3"
          strokeDasharray="10 8" opacity={shown[1]}
        />
      </svg>
      <div
        style={{
          position: "absolute", left: GRID.left - 200, width: GRID_RIGHT - GRID.left + 400, top: 200, textAlign: "center",
          fontSize: 32, fontWeight: 600, opacity: shown[2],
        }}
      >
        {programmes}
      </div>
      <Planned
        text={models} tag={tag} tone={color.gov} shown={shown[0]}
        style={{left: GRID.left - PILL.gap - PILL.width, top: PILL.top, width: PILL.width}}
      />
      <Planned
        text={lineage} tag={tag} tone={color.val} shown={shown[1]}
        style={{left: GRID_RIGHT + PILL.gap, top: PILL.top, width: PILL.width}}
      />
      <Planned
        text={architecture} tag={tag} tone={color.arch} shown={shown[3]}
        style={{left: GRID.left, top: 600, width: GRID_RIGHT - GRID.left, justifyContent: "center"}}
      />
      <Planned
        text={intelligence} tag={tag} tone={color.ragMedium} shown={shown[4]}
        style={{left: 160, top: 730, width: video.width - 320, justifyContent: "center"}}
      />
    </>
  );
};
