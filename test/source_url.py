"""The link rule the agent's data and pages share; its cases are pinned in test/risk_suggestions_data_test.py."""
import re


def url_ok(u, host):
    """A plain https url on exactly this host. A fixed prefix, not a parsed hostname: parsers and browsers read
    userinfo, ports and backslashes differently, so a parsed check can pass a url that a browser sends elsewhere."""
    return isinstance(u, str) and re.fullmatch(rf'https://{re.escape(host)}(?:[/?#]\S*)?', u) is not None
