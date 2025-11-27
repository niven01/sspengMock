import json
import logging
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Mock API function processed a request.")

    # Parse incoming JSON safely
    try:
        body = req.get_json()
    except ValueError:
        body = None

    # Example mock response (customize as needed)
    response_payload = {
        "status": "success",
        "message": "Mock API response",
        "request_body": body,
        "query_params": req.params,
        "path": req.url
    }

    return func.HttpResponse(
        json.dumps(response_payload),
        mimetype="application/json",
        status_code=200
    )
