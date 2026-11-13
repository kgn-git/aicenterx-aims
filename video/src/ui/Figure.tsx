import React from "react";
import {color, headingFont, mutedInk} from "../theme";
import {ramp} from "./kit";

// A figure counts up from zero as it lands, long enough to read as growth and short enough to settle on its number.
const COUNT = 0.6;

/** "~5%" as its parts, so the number can count up while the sign and suffix stay put. */
const parts = (figure: string) => {
  const [, before = "", number = "0", after = ""] = figure.match(/^(\D*)(\d+)(.*)$/) ?? [];
  return {before, number: Number(number), after};
};

/** One of the pitch's figures over footage: the number in its tone, its label and its source, landing at `at` and
 *  leaving at `out`. */
export const Figure: React.FC<{t: number; at: number; out?: number; figure: string; label: string; cite: string; tone: string}> = ({
  t, at, out = Infinity, figure, label, cite, tone,
}) => {
  const shown = ramp(t, at, 0.45) * (Number.isFinite(out) ? 1 - ramp(t, out, 0.35) : 1);
  const {before, number, after} = parts(figure);
  return (
    <div
      style={{
        position: "absolute", left: 140, top: 300, width: 1040, opacity: shown,
        transform: `translateY(${(1 - ramp(t, at, 0.45)) * 40}px)`,
      }}
    >
      <div style={{width: 120, height: 6, background: tone, marginBottom: 28}} />
      <div style={{fontFamily: headingFont, fontSize: 220, fontWeight: 700, lineHeight: 0.95, color: tone}}>
        {before}{Math.round(number * ramp(t, at, COUNT))}{after}
      </div>
      <div style={{marginTop: 26, fontSize: 52, fontWeight: 500, lineHeight: 1.2, color: color.ink}}>{label}</div>
      <div style={{marginTop: 22, fontSize: 24, color: mutedInk}}>{cite}</div>
    </div>
  );
};
