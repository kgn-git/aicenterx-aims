import React from "react";
import {useCurrentFrame, useVideoConfig} from "remotion";
import enhancements from "../../data/model_enhancements.json";
import mitigations from "../../../tools/data/mitigation_suggestions.json";
import {color, headingFont, video} from "../theme";
import {AppFrame, Button, Card, Checkbox, Cursor, ramp, SIDE, Toast, TOP_BAR} from "../ui/kit";
import {INITIATIVE_NAME, TRIGGER} from "./Canvas";
import type {SceneProps} from "./types";

const TOP = 130;
const GAP = 18;
const WIDTH = (video.width - 2 * SIDE - GAP) / 2;
const HEIGHT = 318;
const KIND_COLOUR: Record<string, string> = {"fine-tuning": color.arch, "agent workflow": color.gov, "human review": color.val};
const all = Object.values(mitigations.risks).flat();
const cell = (i: number) => ({x: SIDE + (i % 2) * (WIDTH + GAP), y: TOP + Math.floor(i / 2) * (HEIGHT + GAP)});

/** The enhancements that put the saved mitigations into effect, each tied to its mitigation and source. */
export const Enhancements: React.FC<SceneProps> = ({scene, cues, seconds}) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const [trigger, , , save, toast] = scene.onScreen;
  const {shown, saved} = scene.dataRefs.enhancements!;
  const cards = shown.map((id) => enhancements.enhancements.find((e) => e.id === id)!);

  const click = 0.5;
  const appearFrom = 1.1;
  const ticks = saved.map((_, k) => cues[cues.length - 1].start + 0.2 + k * 0.45);
  const saveAt = ticks[ticks.length - 1] + 0.6;
  const button = {x: TRIGGER.x, y: TRIGGER.y - TOP_BAR};

  return (
    <AppFrame trail={INITIATIVE_NAME}>
      <div style={{position: "absolute", left: SIDE, top: 32, fontFamily: headingFont, fontSize: 56, fontWeight: 600}}>
        {INITIATIVE_NAME}
      </div>
      <div style={{position: "absolute", right: TRIGGER.right, top: TRIGGER.top}}>
        <Button
          label={t < appearFrom ? trigger : save}
          pressed={Math.max(0, 1 - Math.abs(t - click) / 0.15, 1 - Math.abs(t - saveAt) / 0.15)}
          glow={t < click ? 1 - ramp(t, 0, click) : 0}
        />
      </div>
      <Toast text={toast} shown={ramp(t, saveAt + 0.15, 0.35)} style={{top: 32, bottom: undefined, right: SIDE + 470, padding: "12px 28px"}} />
      {cards.map((e, i) => {
        const shownAt = appearFrom + i * 0.3;
        const k = saved.indexOf(e.id);
        const m = all.find((x) => x.id === e.mitigationId)!;
        const source = "title" in e.source ? e.source.title : "Illustrative";
        return (
          <Card
            key={e.id}
            style={{
              position: "absolute", left: cell(i).x, top: cell(i).y, width: WIDTH, height: HEIGHT,
              display: "flex", gap: 18, lineHeight: 1.3, opacity: ramp(t, shownAt, 0.4),
              transform: `translateY(${(1 - ramp(t, shownAt, 0.4)) * 24}px)`,
              borderColor: k >= 0 && t >= ticks[k] ? color.gov : color.border,
            }}
          >
            <Checkbox checked={k >= 0 ? ramp(t, ticks[k], 0.2) : 0} />
            <div style={{display: "flex", flexDirection: "column", gap: 10}}>
              <div style={{display: "flex", alignItems: "flex-start", gap: 16}}>
                <span
                  style={{
                    border: `2px solid ${KIND_COLOUR[e.kind]}`, color: KIND_COLOUR[e.kind], borderRadius: 2,
                    padding: "0 12px", fontWeight: 600, whiteSpace: "nowrap", flex: "0 0 auto",
                  }}
                >
                  {e.kind}
                </span>
                <span style={{fontFamily: headingFont, fontSize: 34, fontWeight: 600}}>{e.name}</span>
              </div>
              <div>{e.how}</div>
              <div style={{color: color.val}}>
                ↳ {m.controlKey} · {m.mit}
              </div>
              <div style={{color: color.inkMuted}}>{source}</div>
            </div>
          </Card>
        );
      })}
      <Cursor
        t={t}
        clicks={[click, ...ticks, saveAt]}
        path={[
          {t: 0, x: button.x, y: button.y},
          {t: cues[cues.length - 1].start, x: 1000, y: 500},
          ...saved.map((id, k) => ({t: ticks[k], x: cell(shown.indexOf(id)).x + 40, y: cell(shown.indexOf(id)).y + 40})),
          {t: saveAt, ...button},
          {t: seconds, x: 1450, y: 100},
        ]}
      />
    </AppFrame>
  );
};
