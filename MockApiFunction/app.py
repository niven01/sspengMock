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
    logging.info("mock_endpoint: START %s %s", req.method, req.url)
    
    try:
        path = req.route_params.get("path", "")
        logging.info("mock_endpoint: path='%s'", path)
        
        record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "method": req.method,
            "path": path,
            "query": dict(req.params),
            "headers": dict(req.headers),
            "body": None,
        }

        # try JSON first, then raw text
        try:
            record["body"] = req.get_json()
            logging.info("mock_endpoint: parsed JSON body")
        except ValueError:
            try:
                record["body"] = req.get_body().decode("utf-8")
                logging.info("mock_endpoint: parsed text body")
            except Exception:
                logging.warning("mock_endpoint: could not read body")
                record["body"] = None

        REQUEST_LOG.setdefault(path, []).append(record)
        logging.info(
            "mock_endpoint: stored request for '%s' (total=%d)",
            path,
            len(REQUEST_LOG[path]),
        )
        logging.debug("mock_endpoint: record=%s", json.dumps(record))

        response_body = {
            "message": "Mock endpoint captured your request.",
            "path": path,
            "request_id": len(REQUEST_LOG[path]) - 1,
        }

        logging.info(
            "mock_endpoint: returning 200 for path '%s', request_id=%d",
            path,
            response_body["request_id"],
        )

        return func.HttpResponse(
            body=json.dumps(response_body),
            mimetype="application/json",
            status_code=200,
        )

    except Exception as e:
        # log full stack trace and return a safe 500
        logging.exception("mock_endpoint: FAILED with unhandled exception: %s", e)
        return func.HttpResponse(
            body=json.dumps({"error": "internal server error"}),
            mimetype="application/json",
            status_code=500,
        )

@app.route(
    route="inspect/{*path}",
    methods=["GET"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
def inspect_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("inspect_endpoint: START %s %s", req.method, req.url)
    
    try:
        path = req.route_params.get("path", "")
        logging.info("inspect_endpoint: path='%s'", path)
        
        data = REQUEST_LOG.get(path, [])
        logging.info(
            "inspect_endpoint: returning %d records for path '%s'",
            len(data),
            path,
        )

        return func.HttpResponse(
            body=json.dumps({"path": path, "requests": data}),
            mimetype="application/json",
            status_code=200,
        )

    except Exception as e:
        logging.exception("inspect_endpoint: FAILED with unhandled exception: %s", e)
        return func.HttpResponse(
            body=json.dumps({"error": "internal server error"}),
            mimetype="application/json",
            status_code=500,
        )
