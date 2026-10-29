import {cancelRender, continueRender, delayRender, staticFile} from "remotion";

// The fonts are bundled rather than fetched from Google Fonts, so a render needs no network. The render waits for
// them, and a font that fails to load cancels it instead of rendering with a fallback face.
const faces = [
  {family: "Fraunces", file: "fonts/Fraunces-Variable.ttf", weight: "100 900"},
  {family: "IBM Plex Sans", file: "fonts/IBMPlexSans-Variable.ttf", weight: "100 700"},
];

const handle = delayRender("Loading the bundled fonts");

Promise.all(
  faces.map(({family, file, weight}) =>
    new FontFace(family, `url('${staticFile(file)}') format('truetype')`, {weight}).load(),
  ),
)
  .then((loaded) => {
    loaded.forEach((face) => document.fonts.add(face));
    continueRender(handle);
  })
  .catch((err) => cancelRender(err));
