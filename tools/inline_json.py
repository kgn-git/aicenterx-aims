"""Curated JSON data as a JavaScript literal that is safe to place inside the page's <script>."""
import json


def script_literal(data):
    """JSON with <, > and & as \\u escapes: none of them can then end the script or open a script comment ("<!--"),
    and JSON only allows them inside strings, where the escape means the same character."""
    return json.dumps(data).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
