import React from "react";
import {interpolate} from "remotion";
import {TALLY_COUNT} from "../moments.mjs";
import {appFrameHeight, color, headingFont, video, mutedInk} from "../theme";
import {ramp} from "../ui/kit";

const clamp = {extrapolateLeft: "clamp", extrapolateRight: "clamp"} as const;
const lerp = (k: number, from: number, to: number) => interpolate(k, [0, 1], [from, to], clamp);
const MIDDLE = {x: video.width / 2, y: appFrameHeight / 2};
/** The initiative's outcome: its risks, mitigations and enhancements count up in their stage colours and are ticked,
 *  under the hour it took; then the card folds to the size its portfolio card has at the portfolio's opening zoom, so
 *  the pull-back starts from this very card. */
export const Outcome: React.FC<{
  t: number; initiative: string; heading: string; chip: string; counts: [number, string][]; tones: string[];
  at: {card: number; rows: number[]; clock: number; ready: number; fold: number};
}> = ({t, initiative, heading, chip, counts, tones, at}) => {
  const fold = ramp(t, at.fold, 0.4);
  const open = 1 - fold;
  const height = lerp(fold, OUTCOME.open, OUTCOME.closed);
  return (
    <div
      style={{
        position: "absolute", left: MIDDLE.x - OUTCOME.width / 2, top: MIDDLE.y - height / 2, width: OUTCOME.width, height,
        boxSizing: "border-box", borderRadius: 12, padding: "30px 42px", background: color.surface2,
        border: `9px solid ${color.val}`, overflow: "hidden", opacity: ramp(t, at.card, 0.4),
      }}
    >
      <div style={{fontSize: 57, fontWeight: 600, whiteSpace: "nowrap", lineHeight: 1.15}}>{initiative}</div>
      <div style={{display: "flex", alignItems: "center", gap: 14, marginTop: 6, fontSize: 48, fontWeight: 600, color: color.val}}>
        <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke={color.val} strokeWidth={2.2} strokeLinecap="round" style={{opacity: ramp(t, at.clock, 0.3)}}>
          <circle cx="12" cy="12" r="9" />
          <path d="M12 7v5l3.5 2" />
        </svg>
        <span style={{opacity: ramp(t, at.clock, 0.3)}}>{chip}</span>
        <span style={{fontSize: 34, color: color.ink, opacity: open * ramp(t, at.ready, 0.4)}}>· {heading}</span>
      </div>
      <div style={{marginTop: 26, display: "flex", flexDirection: "column", gap: 12, opacity: open}}>
        {counts.map(([n, label], i) => {
          const shown = ramp(t, at.rows[i], 0.3);
          const done = ramp(t, at.rows[i] + TALLY_COUNT, 0.25);
          return (
            <div key={label} style={{display: "flex", alignItems: "center", gap: 22, height: 68, opacity: shown}}>
              <div style={{width: 10, alignSelf: "stretch", background: tones[i], borderRadius: 2}} />
              <div style={{width: 70, fontFamily: headingFont, fontSize: 64, fontWeight: 650, color: tones[i], lineHeight: 1}}>
                {Math.round(n * ramp(t, at.rows[i], TALLY_COUNT))}
              </div>
              <div style={{flex: 1, fontSize: 38, color: color.ink}}>{label}</div>
              <svg width="40" height="40" viewBox="0 0 24 24" style={{opacity: done, transform: `scale(${0.6 + 0.4 * done})`}}>
                <path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke={tones[i]} strokeWidth="3" strokeLinecap="round" />
              </svg>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const GRID = {left: 560, top: 330, column: 240, gap: 40, card: 64, cardGap: 14};
const WAVES = [3, 2, 3];
const GRID_RIGHT = GRID.left + WAVES.length * GRID.column + (WAVES.length - 1) * GRID.gap;
const CV = {x: GRID.left + GRID.column / 2, y: GRID.top + GRID.card / 2};
// The outcome card open, and folded to the initiative card at the portfolio's opening 3x zoom.
const OUTCOME = {width: GRID.column * 3, open: 500, closed: GRID.card * 3};
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
