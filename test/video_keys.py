"""The rule linking a CV Screening Assistant risk to its mitigations, shared by the marketing video's tests."""


def mitigation_key(suggestion):
    """A suggestion that matches a register risk keeps its mitigations under that risk; any other under its own id."""
    return suggestion.get('matchesRisk') or suggestion['id']


def hiring_mitigations(risk_data, mitigation_data):
    """{mitigation id: the key of the CV Screening Assistant risk it belongs to}."""
    keys = {mitigation_key(s) for s in risk_data['initiatives']['hiring']['suggestions']}
    return {m['id']: k for k in keys for m in mitigation_data['risks'].get(k, [])}
