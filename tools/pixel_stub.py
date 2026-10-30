"""Answers the landing page's Seenbase pixel locally in browser tests, so a test run never counts as a visit."""
import base64

PIXEL_URL = "https://trxl-elba.online/**"
# A transparent 1x1 GIF: a fulfilled image, unlike an aborted request, logs no console error for verify.py to catch.
GIF = base64.b64decode("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7")


def stub_pixel(context, seen=None):
    """Route the pixel host to a local GIF in this Playwright context; each answered url is appended to seen."""
    def answer(route):
        if seen is not None:
            seen.append(route.request.url)
        route.fulfill(status=200, content_type="image/gif", body=GIF)
    context.route(PIXEL_URL, answer)
