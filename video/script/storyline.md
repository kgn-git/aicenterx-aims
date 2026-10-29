# Marketing video storyline: the CV Screening Assistant journey

A 59-second story in six scenes and five fragments, with 126 narrated words. `video/src/timeline.json` holds the timing and the data each scene shows. The narration below matches it word for word, and `test/marketing_video_timeline_test.py` checks that.

Each scene ends on the button that starts the next one, while the narration bridges to it.

| Scene | Seconds | Narration | On screen |
|---|---|---|---|
| hook | 4 | Amazon's experimental hiring tool allegedly showed gender bias in rankings. | The incident title, cited to the AI Incident Database, incident 37 |
| canvas | 11 | With AI Center X, you define the CV Screening Assistant in its AI Canvas: the problem, the data, the people affected. Next, simulate the risks. | "Define an initiative", AI Canvas excerpts, then the initiative page with "Simulate risks" |
| risks | 14 | The agent suggests risks, each cited from the MIT AI Risk Repository and the AI Incident Database. You tick the three that matter and save them. Then generate mitigations. | 5 cited risks, 3 ticked, "Save selected risks", then "Generate mitigations" |
| mitigations | 12 | For each saved risk, the agent proposes mitigations, cited from the MIT mitigation taxonomy and the EU AI Act. You keep four. Next, suggest model enhancements. | 5 cited mitigations, 4 ticked, "Save selected mitigations", then "Suggest model enhancements" |
| enhancements | 12 | The agent proposes ways to put them into effect: fine-tuning on audited shortlists, bias-check agents, and recruiter review. You save all four. | 4 enhancements, each tied to a saved mitigation, then "Save selected enhancements" |
| end | 6 | From idea to governed initiative, every step cited. That is AI Center X. | Sources and licences, and "The narration voice is AI-generated." |

Fragments: f1 is hook and canvas (15 s), f2 is risks (14 s), f3 is mitigations (12 s), f4 is enhancements (12 s) and f5 is end (6 s).
