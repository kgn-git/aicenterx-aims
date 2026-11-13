import React from "react";
import {AbsoluteFill, OffthreadVideo, Sequence, staticFile, useCurrentFrame, useVideoConfig} from "remotion";
import footage from "../footage.json";
import {ramp} from "./kit";

const clips: Record<string, {from: number; rate: number}> = footage.clips;
// A slow push-in, so a held shot never reads as a still.
const PUSH = 0.004;

/** A Pexels clip (downloaded by npm run video:footage) filling the frame, darkened on the left where the words sit,
 *  for one of shots() in moments.mjs: it fades in at `from` and out at `to`, in seconds within its scene. */
export const Footage: React.FC<{clip: string; from?: number; to?: number; shade?: number}> = ({
  clip, from = 0, to = Infinity, shade = 0.5,
}) => {
  const {fps} = useVideoConfig();
  const t = useCurrentFrame() / fps;
  const shown = (from ? ramp(t, from, 0.3) : 1) * (Number.isFinite(to) ? 1 - ramp(t, to - 0.3, 0.3) : 1);
  return (
    <AbsoluteFill style={{opacity: shown, overflow: "hidden"}}>
      {/* The clip starts as it appears; mounted earlier, it would play unseen and run out on screen. */}
      <Sequence from={Math.round(from * fps)} layout="none">
        <OffthreadVideo
          src={staticFile(`footage/${clip}.mp4`)} trimBefore={Math.round(clips[clip].from * fps)}
          playbackRate={clips[clip].rate} muted
          style={{width: "100%", height: "100%", objectFit: "cover", transform: `scale(${1.03 + PUSH * (t - from)})`}}
        />
      </Sequence>
      <AbsoluteFill
        style={{
          background: `linear-gradient(90deg, rgba(14,19,32,${Math.min(1, shade + 0.35)}) 0%, ` +
            `rgba(14,19,32,${shade}) 50%, rgba(14,19,32,${shade * 0.3}) 100%)`,
        }}
      />
    </AbsoluteFill>
  );
};
