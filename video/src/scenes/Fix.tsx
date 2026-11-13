import React from "react";
import {useCurrentFrame, useVideoConfig} from "remotion";
import mitigations from "../../../tools/data/mitigation_suggestions.json";
import risks from "../../../tools/data/risk_suggestions.json";
import {fixMoments, pressed} from "../moments.mjs";
import {aiActArticles, articleLabel} from "../sources.mjs";
import {color, headingFont, STAGE} from "../theme";
import {Footage} from "../ui/Footage";
import {AppFrame, bump, Button, Card, Checkbox, ramp, SIDE, SourceChip} from "../ui/kit";
import type {SceneProps} from "./types";

type Refs = {footage: string[]; risks: {shown: string[]; saved: string[]}; mitigations: {shown: string[]; saved: string[]}};

const TOP = 150;
const GAP = 16;
const RISK_W = (1920 - 2 * SIDE - 2 * GAP) / 3;
const RISK_H = 300;
const ROW_H = 118;
const hiring = risks.initiatives.hiring.suggestions;
const allMitigations = Object.values(mitigations.risks).flat();
const riskCell = (i: number) => ({left: SIDE + (i % 3) * (RISK_W + GAP), top: TOP + Math.floor(i / 3) * (RISK_H + GAP)});

/** Beat 3, the fix: the team at work, then the product as a fast montage. "Simulate risks" lands the cited risks,
 *  whose AIID and MIT chips light as their sources are named, and the saved ones are ticked; "Generate mitigations"
 *  lands the mitigations with their MIT class and EU AI Act article, and the relevant ones are ticked. */
export const Fix: React.FC<SceneProps> = ({scene, cues, seconds}) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const m = fixMoments(scene, cues, seconds);
  const [initiative, simulate, generate] = scene.onScreen;
  const refs = scene.dataRefs as Refs;
  const product = ramp(t, m.productAt, 0.4);
  const risksOut = ramp(t, m.mitClick, 0.3);
  return (
    <>
      <Footage id={refs.footage[0]} to={m.productAt + 0.4} />
      <div style={{position: "absolute", inset: 0, opacity: product, transform: `translateX(${(1 - product) * 80}px)`}}>
        <AppFrame trail={initiative}>
          <div style={{position: "absolute", left: SIDE, top: 40, fontFamily: headingFont, fontSize: 52, fontWeight: 600}}>
            {initiative}
          </div>
          <div style={{position: "absolute", right: SIDE, top: 40}}>
            <Button
              label={t < m.mitClick - 0.1 ? simulate : generate} pressed={pressed(t, [m.click, m.mitClick])}
              glow={t < m.click ? 1 - ramp(t, m.productAt, m.click - m.productAt) : 0}
            />
          </div>
          <div style={{position: "absolute", inset: 0, opacity: 1 - risksOut}}>
            {refs.risks.shown.map((id, i) => {
              const risk = hiring.find((s) => s.id === id)!;
              const k = refs.risks.saved.indexOf(id);
              return (
                <Card
                  key={id} accent={STAGE.risks}
                  style={{
                    position: "absolute", ...riskCell(i), width: RISK_W, height: RISK_H, display: "flex", gap: 16,
                    opacity: ramp(t, m.cards[i], 0.2), transform: `translateY(${(1 - ramp(t, m.cards[i], 0.25)) * 12}px)`,
                    borderColor: k >= 0 && t >= m.ticks[k] ? color.gov : color.border,
                  }}
                >
                  <Checkbox checked={k >= 0 ? ramp(t, m.ticks[k], 0.15) : 0} />
                  <div style={{display: "flex", flexDirection: "column", gap: 14, lineHeight: 1.3}}>
                    <span>{risk.description}</span>
                    <div style={{display: "flex", flexWrap: "wrap", gap: 10}}>
                      <SourceChip tone={color.val} shown={ramp(t, m.cards[i] + 0.15, 0.2)} pulse={bump(t, m.named[0] + 0.04 * i, 0.7)}>
                        AIID {risk.incidents[0].id}
                      </SourceChip>
                      <SourceChip tone={color.gov} shown={ramp(t, m.cards[i] + 0.2, 0.2)} pulse={bump(t, m.named[1] + 0.04 * i, 0.7)}>
                        MIT · {risk.mit.domain}
                      </SourceChip>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
          {refs.mitigations.shown.map((id, i) => {
            const mit = allMitigations.find((x) => x.id === id)!;
            const k = refs.mitigations.saved.indexOf(id);
            const law = articleLabel(aiActArticles(mit));
            return (
              <Card
                key={id} accent={STAGE.mitigations}
                style={{
                  position: "absolute", left: SIDE, top: TOP + i * (ROW_H + 12), width: 1920 - 2 * SIDE, height: ROW_H,
                  display: "flex", alignItems: "center", gap: 24, lineHeight: 1.25,
                  opacity: ramp(t, m.rows[i], 0.2), transform: `translateY(${(1 - ramp(t, m.rows[i], 0.25)) * 12}px)`,
                  borderColor: k >= 0 && t >= m.rowTicks[k] ? color.gov : color.border,
                }}
              >
                <Checkbox checked={k >= 0 ? ramp(t, m.rowTicks[k], 0.15) : 0} />
                <div style={{flex: "1 1 auto"}}>{mit.description}</div>
                <div style={{flex: "0 0 470px", display: "flex", flexDirection: "column", gap: 8, alignItems: "flex-start"}}>
                  <SourceChip tone={color.gov}>MIT · {mit.mit}</SourceChip>
                  {law && <SourceChip tone={color.arch}>{law}</SourceChip>}
                </div>
              </Card>
            );
          })}
        </AppFrame>
      </div>
    </>
  );
};
