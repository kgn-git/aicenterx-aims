import type React from "react";
import {Canvas} from "./Canvas";
import {End} from "./End";
import {Enhancements} from "./Enhancements";
import {Mitigations} from "./Mitigations";
import {Problem} from "./Problem";
import {Risks} from "./Risks";
import type {SceneProps} from "./types";

/** The built scenes by scene id; a scene not listed here renders as a placeholder. */
export const SCENES: Record<string, React.FC<SceneProps>> = {
  problem: Problem, canvas: Canvas, risks: Risks, mitigations: Mitigations, enhancements: Enhancements,
  end: End,
};
