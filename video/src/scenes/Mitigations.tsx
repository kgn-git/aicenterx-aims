import React from "react";
import {useCurrentFrame, useVideoConfig} from "remotion";
import controls from "../../data/controls_hiring.json";
import steps from "../../data/agent_steps.json";
import mitigations from "../../../tools/data/mitigation_suggestions.json";
import {color, headingFont, video} from "../theme";
import {
  AgentStatus, AppFrame, Button, Card, Checkbox, Cursor, ramp, SIDE, SourceChip, Stream, Toast, TOP_BAR, Zoom,
  zoomLevel,
} from "../ui/kit";
import {aiActArticles, articleLabel} from "../sources.mjs";
import {INITIATIVE_NAME, TRIGGER} from "./Canvas";
import {cueWith, type SceneProps} from "./types";

const TOP = 120;
const ROW = 124;
const GAP = 10;
const PADDING = 22;
const CHECKBOX = 36;
const COLUMN_GAP = 24;
const DESCRIPTION = 800;
const CONTROL = 380;
// The classes and the law sit between the description and the control, in the order the narration names them.
const CLASSES_LEFT = SIDE + PADDING + CHECKBOX + COLUMN_GAP + DESCRIPTION + COLUMN_GAP;
const CLASSES = video.width - CLASSES_LEFT - COLUMN_GAP - CONTROL - PADDING - SIDE;
const all = Object.values(mitigations.risks).flat();
const objective = new Map(controls.controls.map((c) => [c.key, c.objective]));

/** The second agent run, shown by its status line alone: mitigations for the saved risks, each written out with its MIT class, law and control; the
 *  classes are enlarged while the narration names them, and the descriptions, which the zoom would cut, fade out. */
export const Mitigations: React.FC<SceneProps> = ({scene, cues, seconds}) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const [trigger, , , save, next, toast] = scene.onScreen;
  const {shown, saved} = scene.dataRefs.mitigations!;
  const rows = shown.map((id) => all.find((m) => m.id === id)!);

  const click = 0.35;
  const runFrom = 0.7;
  // The risks scene already showed the agent at work, so here its status line alone covers a short run.
  const runTo = 1.6;
  const shownAt = (i: number) => runTo + 0.15 + i * 0.2;
  const nextAt = seconds - 1;
  const saveAt = nextAt - 0.8;
  const ticks = saved.map((_, k) => saveAt - 0.7 - (saved.length - 1 - k) * 0.5);
  const zoom = {from: Math.max(shownAt(0) + 0.5, cueWith(cues, "taxonomy").start - 0.3), to: ticks[0] - 0.6};
  const z = zoomLevel(t, zoom.from, zoom.to);
  const settled = ramp(t, ticks[ticks.length - 1] + 0.3, 0.4);
  const run = ramp(t, runFrom, 0.3) * (1 - ramp(t, runTo, 0.3));
  const label = t < runTo ? trigger : t < nextAt ? save : next;
  const top = (i: number) => TOP + i * (ROW + GAP);
  const button = {x: TRIGGER.x, y: TRIGGER.y - TOP_BAR};

  return (
    <AppFrame trail={INITIATIVE_NAME} grid={run}>
      {t >= runFrom && (
        <AgentStatus
          steps={steps.mitigations} t={t} from={runFrom} length={runTo - runFrom - 0.2} until={shownAt(rows.length - 1) + 0.6}
        />
      )}
      <Zoom t={t} focus={{x: CLASSES_LEFT + CLASSES / 2, y: top(0) + ROW / 2}} from={zoom.from} to={zoom.to} scale={1.5}>
        {rows.map((m, i) => {
          const k = saved.indexOf(m.id);
          const law = articleLabel(aiActArticles(m));
          const chip = (n: number) => ramp(t, shownAt(i) + 0.6 + 0.1 * n, 0.3);
          return (
            <Card
              key={m.id}
              style={{
                position: "absolute", left: SIDE, top: top(i), width: video.width - 2 * SIDE, height: ROW,
                padding: `12px ${PADDING}px`, display: "flex", gap: COLUMN_GAP, alignItems: "center", lineHeight: 1.25,
                opacity: ramp(t, shownAt(i), 0.25) * (k < 0 ? 1 - 0.45 * settled : 1),
                transform: `translateX(${(1 - ramp(t, shownAt(i), 0.4)) * 30}px)`,
                borderColor: k >= 0 && t >= ticks[k] ? color.gov : color.border,
              }}
            >
              <Checkbox checked={k >= 0 ? ramp(t, ticks[k], 0.2) : 0} />
              <div style={{flex: `0 0 ${DESCRIPTION}px`, opacity: 1 - z}}>
                <Stream text={m.description} t={t} from={shownAt(i)} />
              </div>
              <div style={{flex: `0 0 ${CLASSES}px`, display: "flex", flexDirection: "column", gap: 8, alignItems: "flex-start"}}>
                <SourceChip tone={color.gov} shown={chip(0)}>MIT · {m.mit}</SourceChip>
                {law && <SourceChip tone={color.arch} shown={chip(1)}>{law}</SourceChip>}
              </div>
              <div style={{flex: `0 0 ${CONTROL}px`, display: "flex", flexDirection: "column", gap: 6}}>
                <div><SourceChip tone={color.val} shown={chip(2)}>ISO/IEC 42001 {m.controlKey}</SourceChip></div>
                <div style={{fontSize: 22, color: color.inkMuted, opacity: chip(2)}}>{objective.get(m.controlKey)}</div>
              </div>
            </Card>
          );
        })}
      </Zoom>
      <div style={{position: "absolute", left: SIDE, top: 32, fontFamily: headingFont, fontSize: 56, fontWeight: 600}}>
        {INITIATIVE_NAME}
      </div>
      <div style={{position: "absolute", right: TRIGGER.right, top: TRIGGER.top}}>
        <Button
          label={label}
          pressed={Math.max(0, 1 - Math.abs(t - click) / 0.15, 1 - Math.abs(t - saveAt) / 0.15)}
          glow={label === next ? ramp(t, nextAt, 0.5) : t < click ? 1 - ramp(t, 0, click) : 0}
        />
      </div>
      <Toast text={toast} shown={ramp(t, saveAt + 0.15, 0.35)} style={{top: 32, bottom: undefined, right: SIDE + 470, padding: "12px 28px"}} />
      <Cursor
        t={t}
        shown={1 - z}
        clicks={[click, ...ticks, saveAt]}
        path={[
          {t: 0, x: button.x, y: button.y},
          {t: ticks[0] - 0.5, x: 1100, y: 600},
          ...saved.map((id, k) => ({t: ticks[k], x: SIDE + 40, y: top(shown.indexOf(id)) + ROW / 2})),
          {t: saveAt, ...button},
          {t: seconds, ...button},
        ]}
      />
    </AppFrame>
  );
};
