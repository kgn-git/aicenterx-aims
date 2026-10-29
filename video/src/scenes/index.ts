import type React from "react";
import {Canvas} from "./Canvas";
import {Hook} from "./Hook";
import {Risks} from "./Risks";
import type {SceneProps} from "./types";

/** The built scenes by scene id; a scene not listed here still renders as a placeholder. */
export const SCENES: Record<string, React.FC<SceneProps>> = {hook: Hook, canvas: Canvas, risks: Risks};
