import React from "react";
import {useCurrentFrame, useVideoConfig} from "remotion";
import controls from "../../data/controls_hiring.json";
import steps from "../../data/agent_steps.json";
import mitigations from "../../../tools/data/mitigation_suggestions.json";
import {color, headingFont, video} from "../theme";
import {AgentRun, AppFrame, Button, Card, Checkbox, Cursor, ramp, SIDE, Toast, TOP_BAR} from "../ui/kit";
import {INITIATIVE_NAME, TRIGGER} from "./Canvas";
import type {SceneProps} from "./types";

const TOP = 120;
const ROW = 124;
const GAP = 10;
const all = Object.values(mitigations.risks).flat();
const objective = new Map(controls.controls.map((c) => [c.key, c.objective]));

/** "EU AI Act, Article 10" from a EUR-Lex source title, so each row stays within three lines. */
const shortSource = (title: string) => [title.split(" (")[0], title.match(/Article \d+/)?.[0]].filter(Boolean).join(", ");

/** The second agent run: mitigations for the saved risks, each with its control, MIT class and law. */
export const Mitigations: React.FC<SceneProps> = ({scene, cues, seconds}) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const [trigger, , , save, next, toast] = scene.onScreen;
  const {shown, saved} = scene.dataRefs.mitigations!;
  const rows = shown.map((id) => all.find((m) => m.id === id)!);

  const click = 0.5;
  const runFrom = 1;
  const runTo = 3.4;
  const ticks = saved.map((_, k) => cues[2].start + 0.2 + k * 0.5);
  const saveAt = ticks[ticks.length - 1] + 0.7;
  const nextAt = Math.max(cues[3].start, saveAt + 0.8);
  const settled = ramp(t, ticks[ticks.length - 1] + 0.3, 0.4);
  const run = ramp(t, runFrom, 0.3) * (1 - ramp(t, runTo, 0.3));
  const label = t < runTo ? trigger : t < nextAt ? save : next;
  const top = (i: number) => TOP + i * (ROW + GAP);
  const button = {x: TRIGGER.x, y: TRIGGER.y - TOP_BAR};

  return (
    <AppFrame trail={INITIATIVE_NAME}>
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
      {run > 0 && (
        <div style={{position: "absolute", left: SIDE, top: TOP + 40, opacity: run}}>
          <AgentRun steps={steps.mitigations} t={t} from={runFrom} length={runTo - runFrom - 0.2} />
        </div>
      )}
      {rows.map((m, i) => {
        const shownAt = runTo + 0.15 + i * 0.2;
        const k = saved.indexOf(m.id);
        const law = m.sources.find((s) => s.url?.includes("eur-lex") && s.title);
        return (
          <Card
            key={m.id}
            style={{
              position: "absolute", left: SIDE, top: top(i), width: video.width - 2 * SIDE, height: ROW,
              padding: "12px 22px", display: "flex", gap: 24, alignItems: "center", lineHeight: 1.25,
              opacity: ramp(t, shownAt, 0.4) * (k < 0 ? 1 - 0.45 * settled : 1),
              transform: `translateX(${(1 - ramp(t, shownAt, 0.4)) * 30}px)`,
              borderColor: k >= 0 && t >= ticks[k] ? color.gov : color.border,
            }}
          >
            <Checkbox checked={k >= 0 ? ramp(t, ticks[k], 0.2) : 0} />
            <div style={{flex: "0 0 800px"}}>{m.description}</div>
            <div style={{flex: "0 0 440px", color: color.val}}>
              {m.controlKey} {objective.get(m.controlKey)}
            </div>
            <div style={{flex: 1, color: color.inkMuted}}>
              <div>{m.mit}</div>
              {law?.title && <div>{shortSource(law.title)}</div>}
            </div>
          </Card>
        );
      })}
      <Cursor
        t={t}
        clicks={[click, ...ticks, saveAt]}
        path={[
          {t: 0, x: button.x, y: button.y},
          {t: cues[2].start, x: 1100, y: 600},
          ...saved.map((id, k) => ({t: ticks[k], x: SIDE + 40, y: top(shown.indexOf(id)) + ROW / 2})),
          {t: saveAt, ...button},
          {t: seconds, ...button},
        ]}
      />
    </AppFrame>
  );
};
