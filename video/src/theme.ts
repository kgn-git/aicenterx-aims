// Copied from the :root, [data-theme='midnight-executive'] block of index.html, so the video looks like the
// prototype; test/marketing_video_project_test.py fails when the two drift apart.
export const color = {
  bgBase: "#0e1320",
  bgG1: "#121829",
  surface: "rgba(22,29,48,.94)",
  surface2: "rgba(28,37,60,.97)",
  border: "rgba(168,179,196,.2)",
  ink: "#f4f7fb",
  inkMuted: "#a4afc4",
  gov: "#6e8bd6",
  val: "#3fb6a8",
  arch: "#c9a14a",
  ragLow: "#56c08f",
  ragMedium: "#d49a4a",
  ragHigh: "#e2899a",
};

export const accent = color.gov;

export const headingFont = "'Fraunces', Georgia,'Times New Roman',serif";
export const bodyFont = "'IBM Plex Sans', ui-sans-serif, system-ui, 'Segoe UI', sans-serif";

export const video = {width: 1920, height: 1080, fps: 30};

// The bottom 18% of the frame stays free for the burned-in captions #30 adds; rounded once, so every layer that
// lays out above it uses the same pixel edge.
export const captionSafeArea = Math.round(video.height * 0.18);
export const appFrameHeight = video.height - captionSafeArea;
