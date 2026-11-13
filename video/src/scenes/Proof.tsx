import React from "react";
import {useCurrentFrame, useVideoConfig} from "remotion";
import mitigations from "../../../tools/data/mitigation_suggestions.json";
import risks from "../../../tools/data/risk_suggestions.json";
import timeline from "../timeline.json";
import {proofMoments} from "../moments.mjs";
import {appFrameHeight, color, headingFont, mutedInk, video} from "../theme";
import {Footage} from "../ui/Footage";
import {Background, ramp} from "../ui/kit";
import type {SceneProps} from "./types";

const FOOTER = 150;

// Both attribution lists credit MIT under the key "mit", so credits are told apart by source name, not key.
const credits = [...risks.attribution, ...mitigations.attribution].filter(
  (a, i, list) => list.findIndex((b) => b.source === a.source) === i,
);
// The figures' studies, in the order the voice cites them, then the footage's source.
const studies = timeline.scenes
  .flatMap((s) => (s.dataRefs as {sources?: {cite: string}[]}).sources ?? [])
  .map((s) => s.cite);

/** Beat 4, the proof: "Risk profile ready" in under ten minutes over a client meeting, then the "Coming soon" card
 *  with the brand, the tagline and its promise, and every source and disclosure in the footer. */
export const Proof: React.FC<SceneProps> = ({scene, cues}) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const m = proofMoments(scene, cues);
  const [badge, ready, brand, tagline, promise, soon, heading, disclosure, footnote] = scene.onScreen;
  const refs = scene.dataRefs as {footage: string[]};
  const card = ramp(t, m.brandAt, 0.5);
  // The outcome leaves before the brand arrives, so the two never overlap.
  const outcome = ramp(t, m.badge, 0.4) * (1 - ramp(t, m.brandAt - 0.45, 0.3));
  return (
    <Background dots={0}>
      <Footage id={refs.footage[0]} to={m.brandAt + 0.2} />
      <div
        style={{
          position: "absolute", left: 140, top: 360, padding: "34px 44px", borderRadius: 12,
          background: "rgba(18,24,41,.88)", borderLeft: `6px solid ${color.ragLow}`, opacity: outcome,
          transform: `translateY(${(1 - ramp(t, m.badge, 0.4)) * 30}px)`,
        }}
      >
        <div style={{fontSize: 44, fontWeight: 600, color: color.ink}}>{ready}</div>
        <div style={{fontFamily: headingFont, fontSize: 150, fontWeight: 700, lineHeight: 1, color: color.ragLow, marginTop: 14}}>{badge}</div>
      </div>
      <div
        style={{
          position: "absolute", left: 160, right: 160, top: 0, height: appFrameHeight - FOOTER, display: "flex",
          flexDirection: "column", alignItems: "center", justifyContent: "center", textAlign: "center",
          opacity: card, transform: `translateY(${24 * (1 - card)}px)`,
        }}
      >
        <span style={{border: `2px solid ${color.gov}`, color: color.gov, borderRadius: 2, padding: "6px 22px", fontWeight: 600, fontSize: 30, letterSpacing: 1}}>
          {soon}
        </span>
        <div style={{fontFamily: headingFont, fontSize: 140, fontWeight: 650, marginTop: 26, lineHeight: 1}}>{brand}</div>
        <div style={{fontSize: 56, fontWeight: 600, marginTop: 30}}>{tagline}</div>
        <div style={{fontSize: 36, color: mutedInk, marginTop: 18, opacity: ramp(t, m.brandAt + 0.6, 0.5)}}>{promise}</div>
      </div>
      <div
        style={{
          position: "absolute", left: 160, top: appFrameHeight - FOOTER, height: FOOTER - 16, width: video.width - 320,
          borderTop: `1px solid ${color.border}`, paddingTop: 14, fontSize: 20, lineHeight: 1.45, color: mutedInk,
          opacity: ramp(t, m.footer, 0.4),
        }}
      >
        <div>
          <span style={{color: color.ink}}>{heading}: </span>
          {credits.map((c) => `${c.source} (${c.licence})`).join(" · ")}
        </div>
        <div>Figures: {studies.join(" · ")} · Footage: Pexels</div>
        <div>{footnote} {disclosure}</div>
      </div>
    </Background>
  );
};
