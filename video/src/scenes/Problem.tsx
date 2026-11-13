import React from "react";
import {useCurrentFrame, useVideoConfig} from "remotion";
import {problemMoments} from "../moments.mjs";
import {color, headingFont, mutedInk} from "../theme";
import {Background, ramp} from "../ui/kit";
import {LightColumns} from "../ui/LightColumns";
import type {SceneProps} from "./types";

const TILE_W = 520;
const TILE_H = 500;
const TILE_GAP = 50;
const TILES_TOP = 200;
const RULES_TOP = 790;
// The deck's colour for each figure: transformation blue, the gap's teal, stalled projects gold.
const TONES = [color.gov, color.val, color.arch];
// A figure counts up from zero as it lands, long enough to read as growth and short enough to settle on its number.
const COUNT = 0.6;

/** "~5%" as its parts, so the number can count up while the sign and suffix stay put. */
const parts = (figure: string) => {
  const [, before = "", number = "0", after = ""] = figure.match(/^(\D*)(\d+)(.*)$/) ?? [];
  return {before, number: Number(number), after};
};

/** The opening: the pitch deck's three figures land on the light as the voice says each number, each with its
 *  source, then the line on the rules changing; the light dims under them so they stay legible. */
export const Problem: React.FC<SceneProps> = ({scene, cues}) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const m = problemMoments(scene, cues);
  const figures = scene.onScreen.slice(0, 3);
  const labels = scene.onScreen.slice(3, 6);
  const rulesLine = scene.onScreen[6];
  const cites = ((scene.dataRefs as {sources?: {cite: string}[]}).sources ?? []).map((s) => s.cite);
  const left = (1920 - 3 * TILE_W - 2 * TILE_GAP) / 2;
  const rules = ramp(t, m.rules, 0.5);
  return (
    <Background dots={0}>
      <LightColumns shown={1 - 0.55 * ramp(t, m.figures[0], 1.0)} />
      {figures.map((figure, i) => {
        const shown = ramp(t, m.figures[i], 0.45);
        const {before, number, after} = parts(figure);
        const counted = Math.round(number * ramp(t, m.figures[i], COUNT));
        return (
          <div
            key={figure}
            style={{
              position: "absolute", left: left + i * (TILE_W + TILE_GAP), top: TILES_TOP, width: TILE_W, height: TILE_H,
              padding: "36px 40px", boxSizing: "border-box", borderRadius: 10, background: "rgba(18,24,41,.86)",
              borderTop: `5px solid ${TONES[i]}`, opacity: shown, transform: `translateY(${(1 - shown) * 40}px)`,
              display: "flex", flexDirection: "column",
            }}
          >
            <div style={{fontFamily: headingFont, fontSize: 124, fontWeight: 700, lineHeight: 1, color: TONES[i]}}>
              {before}{counted}{after}
            </div>
            <div style={{marginTop: 24, fontSize: 33, lineHeight: 1.3, color: color.ink}}>{labels[i]}</div>
            <div style={{marginTop: "auto", paddingTop: 16, fontSize: 22, lineHeight: 1.35, color: mutedInk}}>{cites[i]}</div>
          </div>
        );
      })}
      <div
        style={{
          position: "absolute", left, top: RULES_TOP, paddingLeft: 26, borderLeft: `6px solid ${color.arch}`,
          fontSize: 46, fontWeight: 500, color: color.ink, opacity: rules, transform: `translateX(${(1 - rules) * -30}px)`,
        }}
      >
        {rulesLine}
      </div>
    </Background>
  );
};
