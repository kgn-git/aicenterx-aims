"""Answers the landing page's Plausible analytics locally in browser tests, so tests run offline and send nothing."""

ANALYTICS_URL = "https://plausible.io/**"


def stub_analytics(target, seen=None):
    """Route Plausible to an empty answer in this Playwright context or page; each answered url is appended to seen."""
    def answer(route):
        if seen is not None:
            seen.append(route.request.url)
        # An empty script, unlike an aborted request, logs no console error for verify.py to catch.
        route.fulfill(status=200, content_type="application/javascript", body="")
    target.route(ANALYTICS_URL, answer)
