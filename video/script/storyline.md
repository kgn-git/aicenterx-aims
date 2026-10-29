# Marketing video storyline: the CV Screening Assistant journey

The story runs in six scenes, grouped into five fragments. `video/src/timeline.json` holds the timing, the fragments and the data each scene shows. The seconds and narration below match it, and `test/marketing_video_timeline_test.py` checks that.

From the canvas scene to the mitigations scene, each scene ends on the button that starts the next one, while the narration bridges to it.

| Scene | Seconds | Narration | On screen |
|---|---|---|---|
| hook | 4 | Amazon's experimental hiring tool allegedly showed gender bias in rankings. | The incident title, cited to the AI Incident Database, incident 37, over a timeline: 2014 development starts, 2015 bias against women found, 2018 Reuters makes it public |
| problem | 6 | In 2026, how do you govern AI initiatives responsibly and create real value? | The question as a title card |
| canvas | 11 | With AI Center X, you define the CV Screening Assistant in its AI Canvas: the problem, the data, the people affected. Next, simulate the risks. | "Define an initiative", AI Canvas excerpts, then the initiative page with "Simulate risks" |
| risks | 13 | An AI agent suggests risks, each cited from the MIT AI Risk Repository and the AI Incident Database. You select and save the relevant risks. Then generate mitigations. | Cited risks, the relevant ones ticked, "Save selected risks" with the toast "Selected risks saved", then "Generate mitigations" |
| mitigations | 13 | For each saved risk, the agent proposes mitigations, classed by MIT's draft taxonomy and tied to the EU AI Act. You select and save the relevant mitigations. Next, suggest model enhancements. | Cited mitigations, the relevant ones ticked, "Save selected mitigations", then "Suggest model enhancements" |
| enhancements | 12 | The agent proposes how to put the saved mitigations into effect: fine-tuning on audited shortlists, two checking agents, and recruiter review. You select and save the relevant enhancements. | Enhancements, each tied to a saved mitigation, the relevant ones ticked, then "Save selected enhancements" |
| end | 7 | From idea to governed initiative. AI Center X: making innovation, governance and change management work together. | A "Coming soon" card with the sources and licences and "The narration voice is AI-generated.", and the footnote "This is a product concept video." in small type at the bottom |
