import React from "react";
import {useCurrentFrame, useVideoConfig} from "remotion";
import enhancements from "../../data/model_enhancements.json";
import mitigations from "../../../tools/data/mitigation_suggestions.json";
import {color, headingFont, STAGE, video, mutedInk} from "../theme";
import {
  AgentStatus, AppFrame, bump, Button, Card, Checkbox, Cursor, KindTag, ramp, SIDE, SourceChip, Toast,
  TOP_BAR, Zoom, zoomLevel,
} from "../ui/kit";
import {INITIATIVE_NAME, TRIGGER} from "./Canvas";
import {cueWith, type SceneProps} from "./types";

const TOP = 130;
const GAP = 18;
const WIDTH = (video.width - 2 * SIDE - GAP) / 2;
const HEIGHT = 318;
// The prototype has no enhancement step, so its agent steps are the video's own.
const STEPS = ["Read the saved mitigations", "Search mitigation sources", "Draft model enhancements"];
const all = Object.values(mitigations.risks).flat();
const cell = (i: number) => ({x: SIDE + (i % 2) * (WIDTH + GAP), y: TOP + Math.floor(i / 2) * (HEIGHT + GAP)});

/** The third agent run, shown by its status line alone: enhancements that put the saved mitigations into effect, each written out and tied to its
 *  mitigation and source, the first enlarged while the narration names it. */
export const Enhancements: React.FC<SceneProps> = ({scene, cues, seconds}) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const [trigger, , , save, toast] = scene.onScreen;
  const {shown, saved} = scene.dataRefs.enhancements!;
  const cards = shown.map((id) => enhancements.enhancements.find((e) => e.id === id)!);

  const click = 0.35;
  const runFrom = 0.7;
  const runTo = 1.5;
  const shownAt = (i: number) => runTo + 0.15 + i * 0.1;
  const naming = cueWith(cues, "fine-tuning");
  const zoom = {from: shownAt(0) + 0.5, to: (naming.start + naming.end) / 2};
  const run = ramp(t, runFrom, 0.3) * (1 - ramp(t, runTo, 0.3));
  // The toast must stay up for about 1.5 s before the cut, so a late last cue pulls the ticks earlier.
  const firstTick = Math.min(cues[cues.length - 1].start + 0.2, seconds - 2.1 - 0.45 * (saved.length - 1) - 0.6);
  const ticks = saved.map((_, k) => firstTick + k * 0.45);
  const saveAt = ticks[ticks.length - 1] + 0.6;
  const button = {x: TRIGGER.x, y: TRIGGER.y - TOP_BAR};

  return (
    <AppFrame trail={INITIATIVE_NAME} grid={run}>
      {t >= runFrom && (
        <AgentStatus steps={STEPS} t={t} from={runFrom} length={runTo - runFrom - 0.2} until={shownAt(cards.length - 1) + 0.6} />
      )}
      <Zoom t={t} focus={{x: cell(0).x + WIDTH / 2, y: cell(0).y + HEIGHT / 2}} from={zoom.from} to={zoom.to} scale={1.6}>
        {cards.map((e, i) => {
          const k = saved.indexOf(e.id);
          const m = all.find((x) => x.id === e.mitigationId)!;
          const source = "title" in e.source ? e.source.title : "Illustrative";
          const chip = (n: number) => ramp(t, shownAt(i) + 0.25 + 0.05 * n, 0.2);
          const pulse = (n: number) => bump(t, shownAt(i) + 0.45 + 0.05 * n);
          return (
            <Card
              key={e.id}
              accent={STAGE.enhancements}
              style={{
                position: "absolute", left: cell(i).x, top: cell(i).y, width: WIDTH, height: HEIGHT,
                display: "flex", gap: 18, lineHeight: 1.3, opacity: ramp(t, shownAt(i), 0.25),
                transform: `translateY(${(1 - ramp(t, shownAt(i), 0.3)) * 10}px)`,
                borderColor: k >= 0 && t >= ticks[k] ? color.gov : color.border,
              }}
            >
              <Checkbox checked={k >= 0 ? ramp(t, ticks[k], 0.2) : 0} />
              <div style={{display: "flex", flexDirection: "column", gap: 10}}>
                <div style={{display: "flex", alignItems: "center", gap: 16}}>
                  <span style={{flex: "0 0 auto"}}><KindTag kind={e.kind} /></span>
                  <span style={{fontFamily: headingFont, fontSize: 34, fontWeight: 600}}>{e.name}</span>
                </div>
                <span>{e.how}</span>
                <div style={{display: "flex", flexWrap: "wrap", gap: 10}}>
                  <SourceChip tone={color.gov} shown={chip(0)} pulse={pulse(0)}>MIT · {m.mit}</SourceChip>
                  <SourceChip tone={color.val} shown={chip(1)} pulse={pulse(1)}>ISO/IEC 42001 {m.controlKey}</SourceChip>
                </div>
                <div style={{color: mutedInk, fontSize: 22, opacity: chip(2)}}>Source: {source}</div>
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
          label={t < shownAt(0) ? trigger : save}
          pressed={Math.max(0, 1 - Math.abs(t - click) / 0.15, 1 - Math.abs(t - saveAt) / 0.15)}
          glow={t < click ? 1 - ramp(t, 0, click) : 0}
        />
      </div>
      <Toast text={toast} shown={ramp(t, saveAt + 0.15, 0.35)} style={{top: 32, bottom: undefined, right: SIDE + 470, padding: "12px 28px"}} />
      <Cursor
        t={t}
        shown={1 - zoomLevel(t, zoom.from, zoom.to)}
        clicks={[click, ...ticks, saveAt]}
        path={[
          {t: 0, x: button.x, y: button.y},
          {t: firstTick - 0.4, x: 1000, y: 500},
          ...saved.map((id, k) => ({t: ticks[k], x: cell(shown.indexOf(id)).x + 40, y: cell(shown.indexOf(id)).y + 40})),
          {t: saveAt, ...button},
          {t: seconds, x: 1450, y: 100},
        ]}
      />
    </AppFrame>
  );
};
