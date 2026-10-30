import React from "react";
import {useCurrentFrame, useVideoConfig} from "remotion";
import enhancements from "../../data/model_enhancements.json";
import mitigations from "../../../tools/data/mitigation_suggestions.json";
import risks from "../../../tools/data/risk_suggestions.json";
import timeline from "../timeline.json";
import {aiActArticles} from "../sources.mjs";
import {appFrameHeight, color, headingFont, video} from "../theme";
import {Background, ramp, spokenAt} from "../ui/kit";
import {Contrast, Portfolio} from "./Acceleration";
import type {SceneProps} from "./types";

const FOOTER = 150;
const SMALL = 22;

// Both attribution lists credit MIT under the key "mit", so credits are told apart by source name, not key.
const credits = [...risks.attribution, ...mitigations.attribution].filter(
  (a, i, list) => list.findIndex((b) => b.source === a.source) === i,
);

/** The sources grouped by document, so the long titles fit one footer line: the EU AI Act articles of every
 *  mitigation shown and every enhancement, then the other enhancement sources:
 *  "EU AI Act: Article 10, Article 14, Article 26 · MIT AI Risk Mitigation Taxonomy (draft): 3.1, 3.5, 2.2". */
const sources = (() => {
  const shown = timeline.scenes.find((s) => s.id === "mitigations")!.dataRefs.mitigations!.shown;
  const all = Object.values(mitigations.risks).flat();
  const cited = enhancements.enhancements.flatMap((e) => ("title" in e.source ? [{sources: [e.source]}] : []));
  const articles = [...new Set([...shown.map((id) => all.find((m) => m.id === id)!), ...cited].flatMap(aiActArticles))].sort((a, b) => a - b);
  const groups = new Map<string, string[]>([["EU AI Act", articles.map((n) => `Article ${n}`)]]);
  for (const e of enhancements.enhancements) {
    if (!("title" in e.source) || e.source.title.startsWith("EU AI Act")) continue;
    const [doc, part] = e.source.title.split(/, (?=\d)/);
    const label = part?.match(/^\d\.\d/)?.[0] ?? part ?? "";
    groups.set(doc, [...(groups.get(doc) ?? []), label].filter((x, i, l) => x && l.indexOf(x) === i));
  }
  return [...groups].map(([name, parts]) => `${name}: ${parts.join(", ")}`).join(" · ");
})();

const KINDS = ["risks", "mitigations", "enhancements"] as const;
const counts = KINDS.map((k): [number, string] => {
  const refs = timeline.scenes.find((s) => s.id === k)!.dataRefs as Record<string, {saved: string[]}>;
  return [refs[k].saved.length, k];
});
const initiative = timeline.scenes.find((s) => s.id === "canvas")!.onScreen[1];
// The word the voice says as each capability lands, in the order the capabilities are listed on screen.
const KEYWORDS = ["models", "data lineage", "programmes", "architecture", "intelligence"];
// The phrases each beat waits for, in the order the voice must say them.
const BEATS = ["now less", "your key", "are identified", "Then scale up", ...KEYWORDS];

/** The close in three beats: the hook's years against the hour the journey took, the pull-back to the portfolio and
 *  the capabilities still to come, then the "Coming soon" card with every source and disclosure in the footer. */
export const End: React.FC<SceneProps> = ({scene, cues}) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const [brand, soon, heading, disclosure, footnote, tagline, message, years, chip, platform, next, ...rest] =
    scene.onScreen;
  const capabilities = rest.slice(0, KEYWORDS.length);
  const wave = rest[KEYWORDS.length];
  const end = cues[cues.length - 1].end;
  const at = (phrase: string) => spokenAt(scene.narration, phrase, end);
  const order = [...BEATS, brand].map(at);
  if (order.some((x, i) => i && x <= order[i - 1])) {
    throw new Error(`The close's narration must say ${[...BEATS, brand].join(", ")} in that order.`);
  }
  const scaleAt = at("Then scale up") - 0.3;
  const brandAt = at(brand);
  const contrast = 1 - ramp(t, scaleAt, 0.6);
  const portfolio = ramp(t, scaleAt, 0.4) * (1 - ramp(t, brandAt - 0.5, 0.4));
  const shown = ramp(t, brandAt - 0.2, 0.7);
  const centred: React.CSSProperties = {
    position: "absolute", left: 160, right: 160, top: 0, height: appFrameHeight - FOOTER, display: "flex",
    flexDirection: "column", alignItems: "center", justifyContent: "center", textAlign: "center",
  };
  return (
    <Background>
      <div style={{position: "absolute", inset: 0, height: appFrameHeight, opacity: contrast}}>
        <Contrast
          t={t} years={years} chip={chip} message={message} counts={counts}
          at={{collapse: at("now less"), tallies: at("your key"), message: at("are identified") - 0.4}}
        />
      </div>
      <div style={{position: "absolute", inset: 0, height: appFrameHeight, opacity: portfolio}}>
        <Portfolio
          t={t} from={scaleAt} tag={next} heading={platform} initiative={initiative} chip={chip} wave={wave}
          capabilities={capabilities} times={KEYWORDS.map(at)}
        />
      </div>
      <div style={{...centred, opacity: shown, transform: `translateY(${24 * (1 - shown)}px)`}}>
        <span
          style={{
            border: `2px solid ${color.gov}`, color: color.gov, borderRadius: 2, padding: "6px 22px",
            fontWeight: 600, fontSize: 32, letterSpacing: 1,
          }}
        >
          {soon}
        </span>
        <div style={{fontFamily: headingFont, fontSize: 150, fontWeight: 650, marginTop: 28, lineHeight: 1}}>{brand}</div>
        <div style={{fontSize: 52, fontWeight: 600, lineHeight: 1.3, marginTop: 36, maxWidth: 1200, opacity: ramp(t, brandAt + 0.7, 0.7)}}>
          {tagline}
        </div>
      </div>
      <div
        style={{
          position: "absolute", left: 160, right: 160, top: appFrameHeight - FOOTER, height: FOOTER - 16,
          borderTop: `1px solid ${color.border}`, paddingTop: 14, fontSize: SMALL, lineHeight: 1.45,
          color: color.inkMuted, opacity: ramp(t, brandAt + 0.3, 0.8), width: video.width - 320,
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
