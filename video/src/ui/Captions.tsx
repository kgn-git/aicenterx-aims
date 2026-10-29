import React from "react";
import {useCurrentFrame, useVideoConfig} from "remotion";
import captions from "../captions.json";
import {bodyFont, captionSafeArea, color} from "../theme";

/** The burned-in captions of one fragment, centred in the caption safe area; cue times count from the fragment. */
export const Captions: React.FC<{fragmentId: string}> = ({fragmentId}) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const cue = captions.cues.find((c) => c.fragment === fragmentId && t >= c.start && t < c.end);
  return (
    <div
      style={{
        position: "absolute", left: 0, right: 0, bottom: 0, height: captionSafeArea,
        display: "flex", alignItems: "center", justifyContent: "center", zIndex: 20,
      }}
    >
      {cue && (
        <div
          style={{
            background: "rgba(8,11,20,.82)", borderRadius: 6, padding: "12px 28px", textAlign: "center",
            fontFamily: bodyFont, fontSize: 38, fontWeight: 500, lineHeight: 1.3, color: color.ink,
          }}
        >
          {cue.lines.map((line) => (
            <div key={line}>{line}</div>
          ))}
        </div>
      )}
    </div>
  );
};
