# Marketing video storyline: the CV Screening Assistant journey

The story runs in six scenes, grouped into five fragments. `video/src/timeline.json` holds the timing, the fragments and the data each scene shows. The seconds and narration below match it, and `test/marketing_video_timeline_test.py` checks that.

From the canvas scene to the mitigations scene, each scene ends on the button that starts the next one, while the narration bridges to it.

| Scene | Seconds | Narration | On screen |
|---|---|---|---|
| hook | 4 | Amazon's experimental hiring tool allegedly showed gender bias in rankings. | The incident title, cited to the AI Incident Database, incident 37 |
| canvas | 11 | With AI Center X, you define the CV Screening Assistant in its AI Canvas: the problem, the data, the people affected. Next, simulate the risks. | "Define an initiative", AI Canvas excerpts, then the initiative page with "Simulate risks" |
| risks | 14 | An AI agent suggests risks, each cited from the MIT AI Risk Repository and the AI Incident Database. You tick three to act on and save them. Then generate mitigations. | 5 cited risks, 3 ticked, "Save selected risks", then "Generate mitigations" |
| mitigations | 12 | For each saved risk, the agent proposes mitigations, classed by MIT's draft taxonomy and tied to the EU AI Act. You save four. Next, suggest model enhancements. | 5 cited mitigations, 4 ticked, "Save selected mitigations", then "Suggest model enhancements" |
| enhancements | 12 | The agent proposes how to put the four mitigations into effect: fine-tuning on audited shortlists, two checking agents, and recruiter review. You save all four. | 4 enhancements, each tied to a saved mitigation, then "Save selected enhancements" |
| end | 6 | From idea to governed initiative, every suggestion cited. That is AI Center X. | Sources and licences, and "The narration voice is AI-generated." |
