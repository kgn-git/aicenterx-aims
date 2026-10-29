import React from "react";
import {useCurrentFrame, useVideoConfig} from "remotion";
import steps from "../../data/agent_steps.json";
import risks from "../../../tools/data/risk_suggestions.json";
import {color, headingFont} from "../theme";
import {
  AgentGrid, AgentRun, AgentStatus, AppFrame, Button, Card, Checkbox, Cursor, ramp, SIDE, SourceChip, Stream, Toast,
  TOP_BAR, Zoom,
} from "../ui/kit";
import {CANVAS_HEADING, CanvasForm, INITIATIVE_NAME, TRIGGER} from "./Canvas";
import type {SceneProps} from "./types";

const COLS = 3;
const GAP = 18;
const TOP = 130;
const WIDTH = (1920 - 2 * SIDE - (COLS - 1) * GAP) / COLS;
const HEIGHT = 315;
const cell = (i: number) => ({x: SIDE + (i % COLS) * (WIDTH + GAP), y: TOP + Math.floor(i / COLS) * (HEIGHT + GAP)});

/** The agent run: the trigger is clicked, the steps tick off, the cited risks are written out and the first is
 *  enlarged while the narration names its sources, then the relevant ones are saved. */
export const Risks: React.FC<SceneProps> = ({scene, cues, seconds}) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const [trigger, , , save, next, toast] = scene.onScreen;
  const name = INITIATIVE_NAME;
  const {shown, saved} = scene.dataRefs.risks!;
  const hiring = risks.initiatives.hiring;
  const cards = shown.map((id) => hiring.suggestions.find((s) => s.id === id)!);

  const click = 0.5;
  const runFrom = 1;
  const runTo = 4;
  const shownAt = (i: number) => runTo + 0.15 + i * 0.25;
  const ticks = saved.map((_, k) => cues[2].start + 0.3 + k * 0.6);
  const saveAt = ticks[ticks.length - 1] + 0.8;
  const nextAt = Math.max(cues[3].start, saveAt + 0.8);
  const run = ramp(t, runFrom, 0.3) * (1 - ramp(t, runTo, 0.3));
  const label = t < runTo ? trigger : t < nextAt ? save : next;
  const target = (i: number) => ({x: cell(i).x + 40, y: cell(i).y + 40});
  const settled = ramp(t, ticks[ticks.length - 1] + 0.3, 0.4);

  return (
    <AppFrame trail={t < click + 0.3 ? CANVAS_HEADING : name}>
      <div style={{position: "absolute", inset: 0, opacity: 1 - ramp(t, click + 0.1, 0.4)}}>
        <CanvasForm t={Infinity} typedBy={0} filledBy={0.5} />
      </div>
      <AgentGrid t={t} shown={run} />
      {t >= runFrom && (
        <AgentStatus
          steps={steps.risks} t={t} from={runFrom} length={runTo - runFrom - 0.2}
        />
      )}
      <Zoom t={t} focus={{x: cell(0).x + WIDTH / 2, y: cell(0).y + HEIGHT / 2}} from={shownAt(0)} to={cues[2].start - 0.6}>
        {run > 0 && (
          <div style={{position: "absolute", left: SIDE, top: TOP + 40, opacity: run}}>
            <AgentRun steps={steps.risks} t={t} from={runFrom} length={runTo - runFrom - 0.2} />
          </div>
        )}
        {cards.map((risk, i) => {
          const k = saved.indexOf(risk.id);
          const incident = risk.incidents[0];
          return (
            <Card
              key={risk.id}
              style={{
                position: "absolute", left: cell(i).x, top: cell(i).y, width: WIDTH, height: HEIGHT,
                opacity: ramp(t, shownAt(i), 0.25) * (k < 0 ? 1 - 0.45 * settled : 1),
                transform: `translateY(${(1 - ramp(t, shownAt(i), 0.4)) * 24}px)`,
                display: "flex", gap: 18, borderColor: k >= 0 && t >= ticks[k] ? color.gov : color.border,
              }}
            >
              <Checkbox checked={k >= 0 ? ramp(t, ticks[k], 0.2) : 0} />
              <div style={{display: "flex", flexDirection: "column", gap: 14, lineHeight: 1.3}}>
                <Stream text={risk.description} t={t} from={shownAt(i)} />
                <div style={{display: "flex", flexWrap: "wrap", gap: 10}}>
                  <SourceChip tone={color.gov} shown={ramp(t, shownAt(i) + 0.6, 0.3)}>MIT · {risk.mit.domain}</SourceChip>
                  <SourceChip tone={color.val} shown={ramp(t, shownAt(i) + 0.75, 0.3)}>AIID {incident.id}</SourceChip>
                </div>
              </div>
            </Card>
          );
        })}
        <Card
          style={{
            position: "absolute", left: cell(cards.length).x, top: cell(cards.length).y, width: WIDTH, height: HEIGHT,
            opacity: ramp(t, shownAt(cards.length), 0.4), borderLeft: `6px solid ${color.arch}`,
            lineHeight: 1.3, display: "flex", flexDirection: "column", gap: 12,
          }}
        >
          <div><SourceChip tone={color.arch}>Context</SourceChip></div>
          <Stream text={hiring.context.statement} t={t} from={shownAt(cards.length)} />
          <div style={{color: color.inkMuted}}>{hiring.context.edition}</div>
        </Card>
      </Zoom>
      <div
        style={{
          position: "absolute", left: SIDE, top: 32, fontFamily: headingFont, fontSize: 56, fontWeight: 600,
          opacity: ramp(t, click + 0.3, 0.4),
        }}
      >
        {name}
      </div>
      <div style={{position: "absolute", right: TRIGGER.right, top: TRIGGER.top}}>
        <Button
          label={label}
          pressed={Math.max(0, 1 - Math.abs(t - click) / 0.15, 1 - Math.abs(t - saveAt) / 0.15)}
          glow={label === next ? ramp(t, nextAt, 0.5) : 0}
        />
      </div>
      <Toast text={toast} shown={ramp(t, saveAt + 0.15, 0.35)} style={{top: 32, bottom: undefined, right: SIDE + 420, padding: "12px 28px"}} />
      <Cursor
        t={t}
        clicks={[click, ...ticks, saveAt]}
        path={[
          {t: 0, x: TRIGGER.x, y: TRIGGER.y - TOP_BAR},
          {t: cues[2].start, x: 1100, y: 600},
          ...saved.map((id, k) => ({t: ticks[k], ...target(shown.indexOf(id))})),
          {t: saveAt, x: TRIGGER.x, y: TRIGGER.y - TOP_BAR},
          {t: seconds, x: TRIGGER.x, y: TRIGGER.y - TOP_BAR},
        ]}
      />
    </AppFrame>
  );
};
