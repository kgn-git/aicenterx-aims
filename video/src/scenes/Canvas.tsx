import React from "react";
import {useCurrentFrame, useVideoConfig} from "remotion";
import canvas from "../../data/canvas_hiring.json";
import {color, headingFont, video} from "../theme";
import {AppFrame, Button, Card, Checkbox, Cursor, ramp, SIDE, TOP_BAR} from "../ui/kit";
import type {SceneProps} from "./types";

const GAP = 18;
const ROWS = [2, 3, 2];
const GRID_TOP = 240;
const ROW_HEIGHT = 166;
// The trigger sits where the risks scene expects it, so the cursor carries on across the cut.
export const TRIGGER = {right: SIDE, top: 32, x: video.width - SIDE - 150, y: TOP_BAR + 64};

/** Defining the initiative: its name, then each AI Canvas block filling in, then its page with the next trigger. */
export const Canvas: React.FC<SceneProps> = ({scene, cues, seconds}) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const [heading, name, , , trigger] = scene.onScreen;
  const page = ramp(t, cues[cues.length - 1].start - 0.3, 0.5);
  const fillFrom = 1.8;
  const fillTo = cues[1].end;
  const typed = name.slice(0, Math.round(name.length * ramp(t, 0.3, 1.4)));
  let index = 0;
  return (
    <AppFrame trail={page > 0.5 ? name : heading}>
      <div style={{position: "absolute", inset: 0, padding: `32px ${SIDE}px`, opacity: 1 - page}}>
        <div style={{fontFamily: headingFont, fontSize: 56, fontWeight: 600}}>{heading}</div>
        <div
          style={{
            marginTop: 20, height: 80, width: 900, border: `1px solid ${color.border}`, borderRadius: 2,
            background: color.surface, display: "flex", alignItems: "center", padding: "0 24px", fontSize: 34,
          }}
        >
          {typed}
          <span style={{opacity: t < 1.9 && Math.floor(t * 2) % 2 === 0 ? 1 : 0, marginLeft: 2}}>|</span>
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
              const at = fillFrom + ((fillTo - fillFrom - 0.6) * (index - count + i)) / canvas.blocks.length;
              return (
                <Card key={block.key} style={{flex: 1, opacity: 0.35 + 0.65 * ramp(t, at, 0.4), padding: 20}}>
                  <div style={{color: color.gov, fontWeight: 600}}>{block.label}</div>
                  <div style={{marginTop: 8, lineHeight: 1.3, opacity: ramp(t, at, 0.5)}}>{block.excerpt}</div>
                </Card>
              );
            })}
          </div>
        ))}
      </div>
      <div style={{position: "absolute", inset: 0, padding: `32px ${SIDE}px`, opacity: page}}>
        <div style={{fontFamily: headingFont, fontSize: 56, fontWeight: 600}}>{name}</div>
        <div style={{marginTop: 36, display: "grid", gridTemplateColumns: "1fr 1fr", gap: "22px 48px", width: 1300}}>
          {canvas.blocks.map((block) => (
            <div key={block.key} style={{display: "flex", alignItems: "center", gap: 18}}>
              <Checkbox checked={1} />
              {block.label}
            </div>
          ))}
        </div>
        <div style={{position: "absolute", right: TRIGGER.right, top: TRIGGER.top}}>
          <Button label={trigger} glow={ramp(t, seconds - 1.2, 0.6)} />
        </div>
      </div>
      <Cursor
        t={t}
        path={[
          {t: 0, x: 1500, y: 700},
          {t: cues[cues.length - 1].start, x: 1300, y: 640},
          {t: seconds - 0.4, x: TRIGGER.x, y: TRIGGER.y - TOP_BAR},
        ]}
      />
    </AppFrame>
  );
};
