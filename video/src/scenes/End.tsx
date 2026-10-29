import React from "react";
import {useCurrentFrame, useVideoConfig} from "remotion";
import enhancements from "../../data/model_enhancements.json";
import mitigations from "../../../tools/data/mitigation_suggestions.json";
import risks from "../../../tools/data/risk_suggestions.json";
import {appFrameHeight, color, headingFont, video} from "../theme";
import {Background, ramp} from "../ui/kit";
import type {SceneProps} from "./types";

const FOOTER = 150;
const SMALL = 22;

// Both attribution lists credit MIT under the key "mit", so credits are told apart by source name, not key.
const credits = [...risks.attribution, ...mitigations.attribution].filter(
  (a, i, list) => list.findIndex((b) => b.source === a.source) === i,
);

/** The enhancement sources grouped by document, so four long titles fit one footer line:
 *  "EU AI Act: Article 10, Article 26 · MIT AI Risk Mitigation Taxonomy (draft): 3.1, 3.5, 2.2". */
const sources = (() => {
  const groups = new Map<string, string[]>();
  for (const e of enhancements.enhancements) {
    if (!("title" in e.source)) continue;
    const [doc, part] = e.source.title.split(/, (?=Article|\d)/);
    const name = doc.split(" (Regulation")[0];
    const label = part?.match(/^(Article \d+|\d\.\d)/)?.[0] ?? part ?? "";
    groups.set(name, [...(groups.get(name) ?? []), label].filter((x, i, l) => x && l.indexOf(x) === i));
  }
  return [...groups].map(([name, parts]) => `${name}: ${parts.join(", ")}`).join(" · ");
})();

/** The "Coming soon" card: the brand and its promise as the message, every source and disclosure in the footer. */
export const End: React.FC<SceneProps> = ({scene}) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const [brand, soon, heading, disclosure, footnote, tagline] = scene.onScreen;
  const shown = ramp(t, 0.3, 0.8);
  return (
    <Background>
      <div
        style={{
          position: "absolute", left: 160, right: 160, top: 0, height: appFrameHeight - FOOTER,
          display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
          textAlign: "center", opacity: shown,
        }}
      >
        <span
          style={{
            border: `2px solid ${color.gov}`, color: color.gov, borderRadius: 2, padding: "4px 18px",
            fontWeight: 600, letterSpacing: 1,
          }}
        >
          {soon}
        </span>
        <div style={{fontFamily: headingFont, fontSize: 150, fontWeight: 650, marginTop: 28, lineHeight: 1}}>{brand}</div>
        <div style={{fontSize: 46, lineHeight: 1.3, marginTop: 36, maxWidth: 1200, opacity: ramp(t, 1.2, 0.8)}}>
          {tagline}
        </div>
      </div>
      <div
        style={{
          position: "absolute", left: 160, right: 160, top: appFrameHeight - FOOTER, height: FOOTER - 16,
          borderTop: `1px solid ${color.border}`, paddingTop: 14, fontSize: SMALL, lineHeight: 1.45,
          color: color.inkMuted, opacity: ramp(t, 0.8, 0.8), width: video.width - 320,
        }}
      >
        <div>
          <span style={{color: color.ink}}>{heading}: </span>
          {credits.map((c) => `${c.source} (${c.licence})`).join(" · ")}
        </div>
        <div>{sources}</div>
        <div>
          {footnote} {disclosure}
        </div>
      </div>
    </Background>
  );
};
