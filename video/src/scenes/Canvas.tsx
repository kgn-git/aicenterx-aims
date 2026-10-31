import React from "react";
import {useCurrentFrame, useVideoConfig} from "remotion";
import canvas from "../../data/canvas_hiring.json";
import timeline from "../timeline.json";
import {canvasMoments} from "../moments.mjs";
import {color, headingFont, video} from "../theme";
import {AppFrame, Button, Card, Cursor, ramp, SIDE, TOP_BAR} from "../ui/kit";
import type {SceneProps} from "./types";

const GAP = 18;
const ROWS = [2, 3, 2];
const GRID_TOP = 240;
const ROW_HEIGHT = 166;
// The trigger sits where the risks scene expects it, so the cursor carries on across the cut; the pointer rests on
// the button's lower right, which every label leaves clear.
export const TRIGGER = {right: SIDE, top: 32, x: video.width - SIDE - 30, y: TOP_BAR + 84};
// The blocks the narration names, in the order it names them: the business problem, its data, the people it affects.
const NAMED = ["businessProblem", "dataStrategy", "customerValue"];

const canvasScene = timeline.scenes.find((s) => s.id === "canvas")!;
export const [CANVAS_HEADING, INITIATIVE_NAME] = canvasScene.onScreen;

/** The "Define an initiative" form: the name typed in by `typedBy`, each block filled in turn up to `filledBy`, and
 *  the named blocks lit from the moment each is named. */
export const CanvasForm: React.FC<{t: number; typedBy: number; filledBy: number; named?: Record<string, number>}> = ({
  t, typedBy, filledBy, named = {},
}) => {
  const typed = INITIATIVE_NAME.slice(0, Math.round(INITIATIVE_NAME.length * ramp(t, typedBy - 1.4, 1.4)));
  const fillFrom = typedBy + 0.1;
  let index = 0;
  return (
    <div style={{position: "absolute", inset: 0, padding: `32px ${SIDE}px`}}>
      <div style={{fontFamily: headingFont, fontSize: 56, fontWeight: 600}}>{CANVAS_HEADING}</div>
      <div
        style={{
          marginTop: 20, height: 80, width: 900, border: `1px solid ${color.border}`, borderRadius: 2,
          background: color.surface, display: "flex", alignItems: "center", padding: "0 24px", fontSize: 34,
        }}
      >
        {typed}
        <span style={{opacity: t < typedBy + 0.1 && Math.floor(t * 2) % 2 === 0 ? 1 : 0, marginLeft: 2}}>|</span>
      </div>
      {ROWS.map((count, row) => (
        <div
          key={row}
          style={{
            position: "absolute", left: SIDE, right: SIDE, top: GRID_TOP + row * (ROW_HEIGHT + GAP),
            height: ROW_HEIGHT, display: "flex", gap: GAP,
          }}
        >
          {canvas.blocks.slice(index, (index += count)).map((block, i) => {
            const at = fillFrom + ((filledBy - fillFrom - 0.4) * (index - count + i)) / canvas.blocks.length;
            const lit = block.key in named ? ramp(t, named[block.key], 0.3) : 0;
            return (
              <Card
                key={block.key}
                style={{
                  flex: 1, opacity: 0.35 + 0.65 * ramp(t, at, 0.4), padding: 20,
                  borderColor: lit > 0.5 ? color.gov : color.border, boxShadow: `0 0 ${28 * lit}px ${color.gov}66`,
                }}
              >
                <div style={{color: color.gov, fontWeight: 600}}>{block.label}</div>
                <div style={{marginTop: 8, lineHeight: 1.3, opacity: ramp(t, at, 0.5)}}>
                  {block.excerpt[0].toUpperCase() + block.excerpt.slice(1)}
                </div>
              </Card>
            );
          })}
        </div>
      ))}
    </div>
  );
};

/** Defining the initiative: its name, each AI Canvas block filling in, the named blocks lit, then the trigger for the
 *  next step. */
export const Canvas: React.FC<SceneProps> = ({scene, cues, seconds}) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const trigger = scene.onScreen[4];
  const {naming, appear, approach, arrive, glow} = canvasMoments(cues, seconds);
  const named = Object.fromEntries(NAMED.map((key, i) => [key, naming.start + ((naming.end - naming.start) * i) / NAMED.length]));
  return (
    <AppFrame trail={CANVAS_HEADING}>
      <CanvasForm t={t} typedBy={1.7} filledBy={naming.end} named={named} />
      <div
        style={{
          position: "absolute", right: TRIGGER.right, top: TRIGGER.top, opacity: ramp(t, appear, 0.4),
          transform: `translateY(${(1 - ramp(t, appear, 0.4)) * -16}px)`,
        }}
      >
        <Button label={trigger} glow={ramp(t, glow, 0.6)} />
      </div>
      <Cursor
        t={t}
        shown={ramp(t, appear - 0.6, 0.4)}
        path={[
          {t: 0, x: 1500, y: 760},
          {t: approach, x: 1300, y: 640},
          {t: arrive, x: TRIGGER.x, y: TRIGGER.y - TOP_BAR},
        ]}
      />
    </AppFrame>
  );
};
