import type React from "react";
import {Break} from "./Break";
import {Fix} from "./Fix";
import {Proof} from "./Proof";
import type {SceneProps} from "./types";
import {World} from "./World";

/** The built scenes by scene id; a scene not listed here renders as a placeholder. */
export const SCENES: Record<string, React.FC<SceneProps>> = {world: World, break: Break, fix: Fix, proof: Proof};
