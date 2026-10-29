import React from "react";
import {useCurrentFrame, useVideoConfig} from "remotion";
import enhancements from "../../data/model_enhancements.json";
import mitigations from "../../../tools/data/mitigation_suggestions.json";
import risks from "../../../tools/data/risk_suggestions.json";
import {appFrameHeight, color, headingFont} from "../theme";
import {Background, ramp} from "../ui/kit";
import type {SceneProps} from "./types";

// Both attribution lists credit MIT under the key "mit", so credits are told apart by source name, not key.
const credits = [...risks.attribution, ...mitigations.attribution].filter(
  (a, i, list) => list.findIndex((b) => b.source === a.source) === i,
);
const titles = [...new Set(enhancements.enhancements.flatMap((e) => ("title" in e.source ? [e.source.title] : [])))];

/** The "Coming soon" card: the brand and tagline, every source with its licence, and the AI-voice disclosure. */
export const End: React.FC<SceneProps> = ({scene}) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const [brand, soon, heading, disclosure, footnote, tagline] = scene.onScreen;
  const shown = ramp(t, 0.3, 0.8);
  return (
    <Background>
      <div style={{position: "absolute", left: 140, top: 150, width: 760, opacity: shown}}>
        <span
          style={{
            display: "inline-block", border: `2px solid ${color.gov}`, color: color.gov, borderRadius: 2,
            padding: "4px 18px", fontWeight: 600, letterSpacing: 1,
          }}
        >
          {soon}
        </span>
        <div style={{fontFamily: headingFont, fontSize: 120, fontWeight: 650, marginTop: 24, lineHeight: 1}}>{brand}</div>
        <div style={{fontSize: 38, lineHeight: 1.3, marginTop: 32, opacity: ramp(t, 1.2, 0.8)}}>{tagline}</div>
        <div style={{color: color.inkMuted, marginTop: 48}}>{disclosure}</div>
      </div>
      <div
        style={{
          position: "absolute", left: 1000, top: 150, width: 780, opacity: ramp(t, 0.8, 0.8),
          borderLeft: `1px solid ${color.border}`, paddingLeft: 40, lineHeight: 1.3,
        }}
      >
        <div style={{fontWeight: 600, marginBottom: 16}}>{heading}</div>
        {credits.map((c) => (
          <div key={c.source} style={{marginBottom: 6}}>
            {c.source} <span style={{color: color.inkMuted}}>· {c.licence}</span>
          </div>
        ))}
        <div style={{marginTop: 22, color: color.inkMuted}}>
          {titles.map((title) => (
            <div key={title} style={{marginBottom: 6}}>{title}</div>
          ))}
        </div>
      </div>
      <div
        style={{
          position: "absolute", left: 140, top: appFrameHeight - 64, fontSize: 24, color: color.inkMuted,
          opacity: shown,
        }}
      >
        {footnote}
      </div>
    </Background>
  );
};
