import logging
import json
import azure.functions as func
from datetime import datetime

app = func.FunctionApp()

# very simple in-memory store: { path: [request_record, ...] }
REQUEST_LOG = {}

@app.route(
    route="mock/{*path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
def mock_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    path = req.route_params.get("path", "")
    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "method": req.method,
        "path": path,
        "query": dict(req.params),
        "headers": dict(req.headers),
        "body": None,
    }

    try:
        # try JSON first, then raw text
        record["body"] = req.get_json()
    except ValueError:
        try:
            record["body"] = req.get_body().decode("utf-8")
        except Exception:
            record["body"] = None

    REQUEST_LOG.setdefault(path, []).append(record)
    logging.info("Captured request for path %s", path)

    response_body = {
        "message": "Mock endpoint captured your request.",
        "path": path,
        "request_id": len(REQUEST_LOG[path]) - 1,
    }

    return func.HttpResponse(
        body=json.dumps(response_body),
        mimetype="application/json",
        status_code=200,
    )

@app.route(
    route="inspect/{*path}",
    methods=["GET"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
def inspect_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    path = req.route_params.get("path", "")
    data = REQUEST_LOG.get(path, [])
    return func.HttpResponse(
        body=json.dumps({"path": path, "requests": data}),
        mimetype="application/json",
        status_code=200,
    )
