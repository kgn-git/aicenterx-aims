import React from "react";
import {AbsoluteFill, OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig} from "remotion";
import footage from "../footage.json";
import {ramp} from "./kit";

const clips: Record<string, {from: number}> = footage.clips;
// A slow push-in, so a held shot never reads as a still.
const PUSH = 0.004;

/** A Pexels clip (downloaded by npm run video:footage) filling the frame, darkened on the left where the words sit;
 *  `from` and `to` fade it in and out within its scene, in seconds. */
export const Footage: React.FC<{id: string; from?: number; to?: number; shade?: number}> = ({
  id, from = 0, to = Infinity, shade = 0.5,
}) => {
  const {fps} = useVideoConfig();
  const t = useCurrentFrame() / fps;
  const shown = (from ? ramp(t, from, 0.3) : 1) * (Number.isFinite(to) ? 1 - ramp(t, to - 0.3, 0.3) : 1);
  return (
    <AbsoluteFill style={{opacity: shown, overflow: "hidden"}}>
      <OffthreadVideo
        src={staticFile(`footage/${id}.mp4`)} trimBefore={Math.round(clips[id].from * fps)} muted
        style={{width: "100%", height: "100%", objectFit: "cover", transform: `scale(${1.03 + PUSH * (t - from)})`}}
      />
      <AbsoluteFill
        style={{
          background: `linear-gradient(90deg, rgba(14,19,32,${Math.min(1, shade + 0.35)}) 0%, ` +
            `rgba(14,19,32,${shade}) 50%, rgba(14,19,32,${shade * 0.3}) 100%)`,
        }}
      />
    </AbsoluteFill>
  );
};
