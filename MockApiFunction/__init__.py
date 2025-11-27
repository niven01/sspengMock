import json
import azure.functions as func
import logging

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Mock API function processed a request.")

    # Safely parse JSON body
    body = req.get_json(silent=True) or {}

    response = {
        "message": "Mock API Response",
        "method": req.method,
        "path": req.url,
        "query": dict(req.params),
        "body": body
    }

    return func.HttpResponse(
        json.dumps(response),
        status_code=200,
        mimetype="application/json"
    )
