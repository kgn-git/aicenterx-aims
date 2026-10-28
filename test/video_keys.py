"""The rule linking a CV Screening Assistant risk to its mitigations, shared by the marketing video's tests.
Its cases are pinned in test/marketing_video_enhancements_data_test.py."""


def mitigation_key(suggestion):
    """A suggestion that matches a register risk keeps its mitigations under that risk; any other under its own id."""
    return suggestion.get('matchesRisk') or suggestion['id']


def hiring_mitigations(risk_data, mitigation_data):
    """{mitigation id: id of the CV Screening Assistant risk suggestion it answers}, so the video names risks the way
    the agent shows them."""
    return {m['id']: s['id'] for s in risk_data['initiatives']['hiring']['suggestions']
            for m in mitigation_data['risks'].get(mitigation_key(s), [])}
