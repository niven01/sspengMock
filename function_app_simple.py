import logging
import json
import azure.functions as func
from datetime import datetime
import uuid

app = func.FunctionApp()

# Simple in-memory storage (will reset on restart but works immediately)
REQUEST_LOG = {}
INSTANCE_ID = str(uuid.uuid4())[:8]

@app.route(route="MockApiFunction", methods=["GET", "POST", "PUT", "DELETE"], auth_level=func.AuthLevel.ANONYMOUS)
def main_mock_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("MockApiFunction: REQUEST RECEIVED")
    
    try:
        # Capture request details
        request_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "method": req.method,
            "url": req.url,
            "headers": dict(req.headers),
            "instance_id": INSTANCE_ID
        }
        
        # Capture body for POST/PUT
        if req.method in ["POST", "PUT"]:
            try:
                request_data["body"] = req.get_body().decode('utf-8')
            except:
                request_data["body"] = "Could not decode body"
        
        # Store the request
        REQUEST_LOG[f"MockApiFunction_{datetime.utcnow().timestamp()}"] = request_data
        
        # Return success response
        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "message": "Request captured successfully",
                "instance_id": INSTANCE_ID,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }),
            status_code=200,
            headers={"Content-Type": "application/json"}
        )
        
    except Exception as e:
        logging.error(f"Error in MockApiFunction: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"}
        )

@app.route(route="inspect/{path:alpha}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def inspect_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    path = req.route_params.get('path', '')
    
    try:
        # Filter requests for the specified path
        filtered_requests = {}
        for key, value in REQUEST_LOG.items():
            if path.lower() in key.lower():
                filtered_requests[key] = value
        
        # Create HTML response
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Request Inspector - {path}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .request {{ border: 1px solid #ddd; margin: 10px 0; padding: 10px; }}
                pre {{ background: #f5f5f5; padding: 10px; overflow: auto; }}
            </style>
        </head>
        <body>
            <h1>Request Inspector - {path}</h1>
            <p>Instance: {INSTANCE_ID}</p>
            <p>Total requests captured: {len(filtered_requests)}</p>
            
            {"".join([f'''
            <div class="request">
                <h3>{key}</h3>
                <pre>{json.dumps(value, indent=2)}</pre>
            </div>
            ''' for key, value in filtered_requests.items()])}
            
            {f"<p>No requests found for path: {path}</p>" if not filtered_requests else ""}
        </body>
        </html>
        """
        
        return func.HttpResponse(html_content, mimetype="text/html")
        
    except Exception as e:
        logging.error(f"Error in inspect: {e}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)

@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({
            "status": "healthy",
            "instance_id": INSTANCE_ID,
            "requests_captured": len(REQUEST_LOG),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }),
        headers={"Content-Type": "application/json"}
    )