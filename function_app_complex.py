import logging
import json
import azure.functions as func
from datetime import datetime
import os
import uuid
import requests
from datetime import datetime, timezone
import urllib.parse
import hashlib
import hmac
import base64

# Generate a unique instance ID
INSTANCE_ID = str(uuid.uuid4())[:8]
INSTANCE_START_TIME = datetime.utcnow().isoformat() + "Z"

# Azure Storage configuration using REST API
STORAGE_CONNECTION_STRING = os.environ.get('AzureWebJobsStorage')
CONTAINER_NAME = 'mock-api-data'
BLOB_NAME = 'request-log.json'

# Parse storage connection string
def parse_connection_string(conn_str):
    """Parse Azure Storage connection string"""
    if not conn_str:
        return None
    
    parts = {}
    for part in conn_str.split(';'):
        if '=' in part:
            key, value = part.split('=', 1)
            parts[key] = value
    
    return {
        'account_name': parts.get('AccountName'),
        'account_key': parts.get('AccountKey'),
        'endpoint_suffix': parts.get('EndpointSuffix', 'core.windows.net')
    }

# Parse connection and check availability
storage_config = parse_connection_string(STORAGE_CONNECTION_STRING)
AZURE_STORAGE_AVAILABLE = storage_config is not None and all([
    storage_config.get('account_name'),
    storage_config.get('account_key')
])

# Initialize REQUEST_LOG
REQUEST_LOG = {}

def create_auth_header(account_name, account_key, method, url_path, headers):
    """Create Azure Storage authentication header"""
    string_to_sign = f"{method}\n\n\n{headers.get('Content-Length', '')}\n\n{headers.get('Content-Type', '')}\n\n\n\n\n\n\n"
    string_to_sign += f"x-ms-date:{headers['x-ms-date']}\n"
    string_to_sign += f"x-ms-version:{headers['x-ms-version']}\n"
    string_to_sign += f"/{account_name}{url_path}"
    
    key_bytes = base64.b64decode(account_key)
    signature = base64.b64encode(hmac.new(key_bytes, string_to_sign.encode('utf-8'), hashlib.sha256).digest()).decode('utf-8')
    return f"SharedKey {account_name}:{signature}"

def make_storage_request(method, url_path, data=None):
    """Make authenticated request to Azure Storage REST API"""
    if not AZURE_STORAGE_AVAILABLE:
        return None
        
    account_name = storage_config['account_name']
    account_key = storage_config['account_key']
    endpoint_suffix = storage_config['endpoint_suffix']
    
    url = f"https://{account_name}.blob.{endpoint_suffix}{url_path}"
    
    headers = {
        'x-ms-date': datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT'),
        'x-ms-version': '2020-10-02'
    }
    
    if data:
        headers['Content-Type'] = 'application/octet-stream'
        headers['Content-Length'] = str(len(data))
    
    headers['Authorization'] = create_auth_header(account_name, account_key, method, url_path, headers)
    
    try:
        response = requests.request(method, url, data=data, headers=headers)
        return response
    except Exception as e:
        logging.error(f"Storage request failed: {e}")
        return None

def load_request_log():
    """Load REQUEST_LOG from Azure Storage"""
    try:
        if not AZURE_STORAGE_AVAILABLE:
            return {}
        
        url_path = f"/{CONTAINER_NAME}/{BLOB_NAME}"
        response = make_storage_request('GET', url_path)
        
        if response is None:
            return {}
            
        if response.status_code == 200:
            data = json.loads(response.text)
            logging.info(f"✅ Loaded REQUEST_LOG with {len(data)} keys")
            return data
        elif response.status_code == 404:
            logging.info("🆕 No existing data found")
            return {}
        else:
            logging.warning(f"⚠️ Unexpected response: {response.status_code}")
            return {}
            
    except Exception as e:
        logging.error(f"❌ Error loading data: {e}")
        return {}

def save_request_log(request_log):
    """Save REQUEST_LOG to Azure Storage"""
    try:
        if not AZURE_STORAGE_AVAILABLE:
            return
        
        # Create container first
        container_url_path = f"/{CONTAINER_NAME}?restype=container"
        make_storage_request('PUT', container_url_path)
        
        # Upload data
        json_data = json.dumps(request_log, default=str, indent=2)
        url_path = f"/{CONTAINER_NAME}/{BLOB_NAME}"
        response = make_storage_request('PUT', url_path, json_data.encode('utf-8'))
        
        if response and response.status_code == 201:
            logging.info(f"✅ Saved data ({len(json_data)} bytes)")
        else:
            logging.error(f"❌ Save failed")
                
    except Exception as e:
        logging.error(f"❌ Save error: {e}")

# Load existing data on startup
REQUEST_LOG = load_request_log()

def main(req: func.HttpRequest) -> func.HttpResponse:
    """Main entry point for MockApiFunction"""
    logging.info(f"MockApiFunction: {req.method} request to {req.url}")
    
    try:
        # Handle OPTIONS request for CORS
        if req.method == 'OPTIONS':
            return func.HttpResponse(
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Accept, Authorization"
                }
            )
            
        # Handle GET request to web interface
        accept_header = req.headers.get("accept", "").lower()
        if "text/html" in accept_header and req.method == "GET":
            html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Mock API Dashboard</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            text-align: center;
        }}
        .header {{
            background: linear-gradient(135deg, #8B5A96, #6A4C93);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(139, 90, 150, 0.3);
        }}
        .status {{
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        .refresh {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #8E44AD;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 20px;
            cursor: pointer;
        }}
    </style>
</head>
<body>
    <button class="refresh" onclick="location.reload()">🔄 Refresh</button>
    
    <div class="container">
        <div class="header">
            <h1>🎯 Mock API Dashboard</h1>
            <p>MockApiFunction endpoint is running!</p>
        </div>
        
        <div class="status">
            <h3>📊 Status</h3>
            <p>Instance ID: {INSTANCE_ID}</p>
            <p>Started: {INSTANCE_START_TIME}</p>
            <p>Total Requests Captured: {len(REQUEST_LOG.get("MockApiFunction", []))}</p>
            <p>Storage: {"✅ Connected" if AZURE_STORAGE_AVAILABLE else "❌ Not Available"}</p>
        </div>
        
        <div class="status">
            <h3>🔧 Usage</h3>
            <p>Send POST requests to this URL to capture them.</p>
            <p>Endpoint: <code>{req.url}</code></p>
        </div>
    </div>
</body>
</html>"""
            return func.HttpResponse(html, mimetype="text/html", status_code=200)
        
        # Handle API requests (POST, PUT, etc.)
        record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "method": req.method,
            "path": "MockApiFunction",
            "query": dict(req.params),
            "headers": dict(req.headers),
            "body": None,
            "instance_id": INSTANCE_ID
        }
        
        # Try to parse the body
        try:
            record["body"] = req.get_json()
        except ValueError:
            try:
                body_text = req.get_body().decode("utf-8")
                record["body"] = body_text if body_text else None
            except Exception:
                record["body"] = None
        
        # Store the request
        REQUEST_LOG.setdefault("MockApiFunction", []).append(record)
        
        # Save to storage
        save_request_log(REQUEST_LOG)
        
        logging.info(f"✅ Captured {req.method} request (total: {len(REQUEST_LOG['MockApiFunction'])})")
        
        response_body = {
            "status": "success",
            "message": "✅ Request captured successfully!",
            "request_id": len(REQUEST_LOG["MockApiFunction"]) - 1,
            "captured": {
                "method": record["method"],
                "timestamp": record["timestamp"],
                "has_body": record["body"] is not None,
                "query_params_count": len(record["query"])
            }
        }
        
        return func.HttpResponse(
            body=json.dumps(response_body, indent=2),
            mimetype="application/json",
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Accept, Authorization"
            }
        )
        
    except Exception as e:
        logging.exception(f"❌ MockApiFunction error: {e}")
        return func.HttpResponse(
            body=json.dumps({"error": "Internal server error", "details": str(e)}),
            mimetype="application/json",
            status_code=500,
            headers={"Access-Control-Allow-Origin": "*"}
        )