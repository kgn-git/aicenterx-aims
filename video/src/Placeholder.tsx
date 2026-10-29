import React from "react";
import {AbsoluteFill} from "remotion";
import {appFrameHeight, bodyFont, captionSafeArea, color, headingFont} from "./theme";

type Scene = {id: string; seconds: number; narration: string; onScreen: string[]};

/** Stands in for a scene until #30 and #31 build it: the scene's id, timing and on-screen items, above the caption
 *  safe area. */
export const Placeholder: React.FC<{scene: Scene}> = ({scene}) => (
  <AbsoluteFill style={{background: `radial-gradient(1200px 800px at 70% -10%, ${color.bgG1}, transparent), ${color.bgBase}`}}>
    <div
      style={{
        position: "absolute", top: 0, left: 0, right: 0, height: appFrameHeight, padding: 72,
        display: "flex", flexDirection: "column", gap: 24, color: color.ink, fontFamily: bodyFont,
      }}
    >
      <div style={{fontFamily: headingFont, fontSize: 72, fontWeight: 600}}>{scene.id}</div>
      <div style={{fontSize: 32, color: color.inkMuted}}>{scene.seconds} s placeholder</div>
      <div
        style={{
          background: color.surface, border: `1px solid ${color.border}`, borderRadius: 16, padding: 32,
          display: "flex", flexDirection: "column", gap: 12, fontSize: 30,
        }}
      >
        {scene.onScreen.map((item) => (
          <div key={item}>{item}</div>
        ))}
      </div>
    </div>
    <div
      style={{
        position: "absolute", left: 0, right: 0, bottom: 0, height: captionSafeArea,
        borderTop: `2px dashed ${color.border}`,
      }}
    />
  </AbsoluteFill>
);
