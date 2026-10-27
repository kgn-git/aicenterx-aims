import json


def script_literal(data):
    """JSON safe inside a <script>: a \\u escape of <, > or & means the same character but cannot end the script."""
    return json.dumps(data).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
