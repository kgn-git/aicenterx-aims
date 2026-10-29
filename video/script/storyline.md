# Marketing video storyline: the CV Screening Assistant journey

The story runs in six scenes, grouped into five fragments. `video/src/timeline.json` holds the timing, the fragments and the data each scene shows. The seconds and narration below match it, and `test/marketing_video_timeline_test.py` checks that.

From the canvas scene to the mitigations scene, each scene ends on the button that starts the next one, while the narration bridges to it.

| Scene | Seconds | Narration | On screen |
|---|---|---|---|
| hook | 6 | Amazon's experimental hiring tool allegedly ranked women lower. Abandoning it took three years. | The incident title, cited to the AI Incident Database, incident 37, over a timeline: 2014 development starts, 2015 bias against women found, 2017 project abandoned |
| problem | 11.5 | Today, no company can afford to spend such time and effort and end up potentially causing harm. The challenge is to govern AI responsibly and create real value. | The question as a title card |
| canvas | 11.5 | In AI Center X, you start with the AI Canvas: the CV Screening Assistant's business problem, its data, and the people it affects. Then you simulate the risks. | "Define an initiative", AI Canvas excerpts, then the initiative page with "Simulate risks" |
| risks | 12 | An AI agent suggests risks, each cited from the MIT AI Risk Repository and the AI Incident Database. You select the relevant ones and save them. Now, generate the mitigations. | Cited risks, the relevant ones ticked, "Save selected risks" with the toast "Selected risks saved", then "Generate mitigations" |
| mitigations | 13 | For every saved risk, the agent proposes mitigations, each classed by MIT's draft taxonomy and tied to the EU AI Act. Again, you select and save. Next come the model enhancements. | Cited mitigations, the relevant ones ticked, "Save selected mitigations", then "Suggest model enhancements" |
| enhancements | 12 | The agent shows how to put those mitigations into effect: fine-tuning on audited shortlists, two checking agents, and learning from recruiter feedback. You save the ones you need. | Enhancements, each tied to a saved mitigation, the relevant ones ticked, then "Save selected enhancements" |
| end | 7 | From idea to business value. AI Center X: making innovation and governance work together. | A "Coming soon" card with the sources and licences and "The narration voice is AI-generated.", and the footnote "This is a product concept video." in small type at the bottom |
