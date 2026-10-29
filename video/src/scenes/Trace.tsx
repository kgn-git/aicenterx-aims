import React from "react";
import {useCurrentFrame, useVideoConfig} from "remotion";
import enhancements from "../../data/model_enhancements.json";
import labels from "../../data/trace_labels.json";
import mitigations from "../../../tools/data/mitigation_suggestions.json";
import risks from "../../../tools/data/risk_suggestions.json";
import timeline from "../timeline.json";
import {color, headingFont} from "../theme";
import {articleLabel, traceRows} from "../trace.mjs";
import {AgentGrid, AppFrame, Card, KindTag, ramp, SIDE, SourceChip} from "../ui/kit";
import {INITIATIVE_NAME} from "./Canvas";
import type {SceneProps} from "./types";

type Row = {
  risk: {id: string; label: string};
  mitigation: {id: string; label: string; articles: number[]};
  enhancement: {id: string; label: string; kind: string};
};

const rows: Row[] = traceRows({timeline, enhancements, risks, mitigations, labels});
const ROW_TOP = 166;
const ROW_H = 136;
const ROW_GAP = 22;
const LINK = 150;
const RISK = {x: SIDE, w: 480};
const MITIGATION = {x: RISK.x + RISK.w + LINK, w: 560};
const ENHANCEMENT = {x: MITIGATION.x + MITIGATION.w + LINK, w: 484};
const rowY = (i: number) => ROW_TOP + i * (ROW_H + ROW_GAP);
const middle = (i: number) => rowY(i) + ROW_H / 2;
// traceRows groups the rows by risk, so a risk answered by two saved mitigations spans both of its rows.
const riskNodes = rows
  .map((r, i) => ({...r.risk, first: i, last: rows.map((x) => x.risk.id).lastIndexOf(r.risk.id)}))
  .filter((r, i, list) => list.findIndex((x) => x.id === r.id) === i);

const curve = (x1: number, y1: number, x2: number, y2: number) =>
  `M ${x1} ${y1} C ${x1 + LINK / 2} ${y1}, ${x2 - LINK / 2} ${y2}, ${x2} ${y2}`;

/** The payoff: every saved enhancement drawn back through its saved mitigation, with its EU AI Act articles, to the
 *  saved risk it answers, then each chain lit in turn. */
export const Trace: React.FC<SceneProps> = ({scene}) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const [heading, riskColumn, mitigationColumn, enhancementColumn] = scene.onScreen;
  const lit = (i: number) => ramp(t, 2.1 + i * 0.25, 0.25);
  const node = (shown: number, glow: number): React.CSSProperties => ({
    position: "absolute", opacity: shown, transform: `translateY(${(1 - shown) * 16}px)`, lineHeight: 1.25,
    display: "flex", flexDirection: "column", justifyContent: "center", gap: 10, padding: "14px 20px",
    borderColor: glow > 0 ? color.gov : color.border, boxShadow: `0 0 ${24 * glow}px ${color.gov}55`,
  });

  return (
    <AppFrame trail={INITIATIVE_NAME}>
      <AgentGrid t={t} shown={0.6} />
      <div
        style={{
          position: "absolute", left: SIDE, top: 32, fontFamily: headingFont, fontSize: 56, fontWeight: 600,
          opacity: ramp(t, 0.1, 0.4),
        }}
      >
        {heading}
      </div>
      {[[RISK, riskColumn], [MITIGATION, mitigationColumn], [ENHANCEMENT, enhancementColumn]].map(([col, text], i) => (
        <div
          key={text as string}
          style={{
            position: "absolute", left: (col as typeof RISK).x, top: 122, fontSize: 24, color: color.inkMuted,
            letterSpacing: 1, opacity: ramp(t, 0.2 + 0.5 * i, 0.4),
          }}
        >
          {text as string}
        </div>
      ))}
      <svg width="1920" height="800" style={{position: "absolute", left: 0, top: 0}}>
        {rows.map((r, i) => {
          const risk = riskNodes.find((x) => x.id === r.risk.id)!;
          const riskMiddle = (rowY(risk.first) + rowY(risk.last) + ROW_H) / 2;
          const stroke = {fill: "none", pathLength: 1, strokeDasharray: "1 1", strokeLinecap: "round" as const};
          return (
            <g key={r.enhancement.id} stroke={lit(i) > 0 ? color.gov : color.inkMuted} strokeWidth={2 + 2 * lit(i)}>
              <path
                d={curve(RISK.x + RISK.w, riskMiddle, MITIGATION.x, middle(i))} {...stroke}
                strokeDashoffset={1 - ramp(t, 0.6 + 0.08 * i, 0.5)}
              />
              <path
                d={curve(MITIGATION.x + MITIGATION.w, middle(i), ENHANCEMENT.x, middle(i))} {...stroke}
                strokeDashoffset={1 - ramp(t, 1.3 + 0.08 * i, 0.5)}
              />
            </g>
          );
        })}
      </svg>
      {riskNodes.map((r) => (
        <Card
          key={r.id}
          style={{
            ...node(ramp(t, 0.3, 0.4), Math.max(...rows.map((x, i) => (x.risk.id === r.id ? lit(i) : 0)))),
            left: RISK.x, top: rowY(r.first), width: RISK.w, height: rowY(r.last) + ROW_H - rowY(r.first),
          }}
        >
          {r.label}
        </Card>
      ))}
      {rows.map((r, i) => (
        <React.Fragment key={r.enhancement.id}>
          <Card style={{...node(ramp(t, 0.9 + 0.08 * i, 0.4), lit(i)), left: MITIGATION.x, top: rowY(i), width: MITIGATION.w, height: ROW_H}}>
            {r.mitigation.label}
            {r.mitigation.articles.length > 0 && (
              <div><SourceChip tone={color.arch}>{articleLabel(r.mitigation.articles)}</SourceChip></div>
            )}
          </Card>
          <Card style={{...node(ramp(t, 1.6 + 0.08 * i, 0.4), lit(i)), left: ENHANCEMENT.x, top: rowY(i), width: ENHANCEMENT.w, height: ROW_H}}>
            <div><KindTag kind={r.enhancement.kind} /></div>
            {r.enhancement.label}
          </Card>
        </React.Fragment>
      ))}
    </AppFrame>
  );
};
