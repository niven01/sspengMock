import logging
import json
import azure.functions as func
from datetime import datetime
import os
import uuid
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError, AzureError

app = func.FunctionApp()

# Generate a unique instance ID to track function app instances
INSTANCE_ID = str(uuid.uuid4())[:8]
INSTANCE_START_TIME = datetime.utcnow().isoformat() + "Z"

# Azure Storage configuration using SDK
STORAGE_CONNECTION_STRING = os.environ.get('AzureWebJobsStorage')
CONTAINER_NAME = 'mock-api-data'
BLOB_NAME = 'request-log.json'

# Initialize Azure Storage client
try:
    if STORAGE_CONNECTION_STRING and not STORAGE_CONNECTION_STRING.startswith('UseDevelopmentStorage=true'):
        blob_service_client = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
        AZURE_STORAGE_AVAILABLE = True
        logging.info("✅ Azure Storage client initialized successfully")
    else:
        blob_service_client = None
        AZURE_STORAGE_AVAILABLE = False
        logging.warning("❌ Azure Storage not available - no connection string or using development storage")
except Exception as e:
    logging.error(f"❌ Failed to initialize Azure Storage client: {e}")
    blob_service_client = None
    AZURE_STORAGE_AVAILABLE = False

def load_request_log():
    """Load REQUEST_LOG from Azure Blob Storage using SDK"""
    logging.info("📥 Starting load_request_log from Azure Storage...")
    
    try:
        if not AZURE_STORAGE_AVAILABLE or not blob_service_client:
            logging.warning("❌ Azure Storage not available, returning empty dict")
            return {}
        
        # Get blob client
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=BLOB_NAME)
        
        try:
            # Download blob content
            blob_data = blob_client.download_blob().readall()
            data = json.loads(blob_data.decode('utf-8'))
            logging.info(f"✅ Loaded REQUEST_LOG from Azure Storage with {len(data)} keys")
            return data
        except ResourceNotFoundError:
            logging.info("🆕 No existing blob found, starting fresh")
            return {}
        except Exception as e:
            logging.error(f"❌ Error downloading blob: {e}")
            return {}
            
    except Exception as e:
        logging.error(f"❌ Error loading from Azure Storage: {e}")
        return {}

def save_request_log():
    """Save REQUEST_LOG to Azure Blob Storage using SDK"""
    logging.info("💾 Starting save_request_log to Azure Storage...")
    try:
        if not AZURE_STORAGE_AVAILABLE or not blob_service_client:
            logging.warning("❌ Azure Storage not available for save")
            return
        
        # Get container client and create container if it doesn't exist
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)
        try:
            container_client.create_container()
            logging.info("✅ Container created successfully")
        except Exception as e:
            if "ContainerAlreadyExists" in str(e):
                logging.info("✅ Container already exists")
            else:
                logging.warning(f"⚠️ Container creation issue: {e}")
        
        # Upload data
        json_data = json.dumps(REQUEST_LOG, default=str, indent=2)
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=BLOB_NAME)
        
        blob_client.upload_blob(json_data.encode('utf-8'), overwrite=True)
        logging.info(f"✅ Saved REQUEST_LOG to Azure Storage ({len(json_data)} bytes)")
            
    except Exception as e:
        logging.error(f"❌ Failed to save to Azure Storage: {e}")
        logging.exception("Full save error traceback:")

def cleanup_old_requests():
    """Remove requests older than 1 hour from all endpoints"""
    try:
        from datetime import datetime, timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        cutoff_iso = cutoff_time.isoformat() + "Z"
        
        total_removed = 0
        
        for path in list(REQUEST_LOG.keys()):
            if path == "_debug":
                continue
                
            if isinstance(REQUEST_LOG[path], list):
                original_count = len(REQUEST_LOG[path])
                REQUEST_LOG[path] = [
                    req for req in REQUEST_LOG[path]
                    if isinstance(req, dict) and req.get('timestamp', '') > cutoff_iso
                ]
                removed_count = original_count - len(REQUEST_LOG[path])
                total_removed += removed_count
                
                if removed_count > 0:
                    logging.info(f"🧹 Cleaned up {removed_count} old requests from {path}")
                    
                # Remove empty endpoints
                if len(REQUEST_LOG[path]) == 0:
                    del REQUEST_LOG[path]
                    logging.info(f"🗑️ Removed empty endpoint: {path}")
        
        if total_removed > 0:
            logging.info(f"✨ Total cleanup: removed {total_removed} requests older than 1 hour")
            save_request_log()  # Save after cleanup
            
    except Exception as e:
        logging.error(f"❌ Error during cleanup: {e}")

# Load existing data and add debug info
REQUEST_LOG = load_request_log()
REQUEST_LOG.setdefault("_debug", []).append({
    "timestamp": INSTANCE_START_TIME,
    "message": f"Instance started (ID: {INSTANCE_ID}) - Azure Storage enabled",
    "instance_id": INSTANCE_ID,
    "website_instance_id": os.environ.get('WEBSITE_INSTANCE_ID', 'Not set'),
    "storage_enabled": STORAGE_CONNECTION_STRING is not None and AZURE_STORAGE_AVAILABLE,
    "container_name": CONTAINER_NAME,
    "note": "Using Azure Blob Storage for persistence across instances"
})

@app.route(route="MockApiFunction", methods=["GET", "POST", "PUT", "DELETE"], auth_level=func.AuthLevel.ANONYMOUS)
def main_mock_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("=" * 60)
    logging.info("main_mock_endpoint: FUNCTION CALLED!")
    logging.info("main_mock_endpoint: Method=%s URL=%s", req.method, req.url)
    logging.info("=" * 60)
    
    try:
        # Cleanup old requests before processing new ones
        cleanup_old_requests()
        
        # Use the route as the path for main endpoint
        path = "MockApiFunction"
        
        record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "method": req.method,
            "path": path,
            "query": dict(req.params),
            "headers": dict(req.headers),
            "body": None,
            "instance_id": INSTANCE_ID,
            "instance_start": INSTANCE_START_TIME
        }

        # try JSON first, then raw text
        try:
            record["body"] = req.get_json()
            logging.info("main_mock_endpoint: parsed JSON body")
        except ValueError:
            try:
                record["body"] = req.get_body().decode("utf-8")
                logging.info("main_mock_endpoint: parsed text body")
            except Exception:
                logging.warning("main_mock_endpoint: could not read body")
                record["body"] = None

        REQUEST_LOG.setdefault(path, []).append(record)
        save_request_log()  # Persist to Azure Storage
        logging.info("main_mock_endpoint: stored request for '%s' (total=%d)", path, len(REQUEST_LOG[path]))
        
        response_body = {
            "message": "Mock endpoint captured your request.",
            "path": path,
            "request_id": len(REQUEST_LOG[path]) - 1,
            "captured_request": record,
        }

        return func.HttpResponse(
            body=json.dumps(response_body),
            mimetype="application/json",
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Accept"
            }
        )

    except Exception as e:
        logging.exception("main_mock_endpoint: FAILED with unhandled exception: %s", e)
        return func.HttpResponse(
            body=json.dumps({"error": "internal server error"}),
            mimetype="application/json",
            status_code=500,
        )

@app.route(route="inspect/{path:alpha}", methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
def inspect_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    path = req.route_params.get('path', '')
    
    try:
        # Always load fresh data from Azure Storage for inspect requests
        logging.info(f"inspect_endpoint: Loading fresh data from storage for path: {path}")
        fresh_data = load_request_log()
        
        # Check if this is a request for the HTML interface
        accept_header = req.headers.get("accept", "").lower()
        format_param = req.params.get("format", "").lower()
        
        is_json_request = format_param == "json" or (not format_param and "application/json" in accept_header and "text/html" not in accept_header)
        is_browser_request = not is_json_request
        
        if is_browser_request:
            # Return HTML interface with Beeceptor-like design
            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Monitor - {path}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f8fafc;
            color: #334155;
            line-height: 1.6;
        }}
        .navbar {{
            background: white;
            border-bottom: 1px solid #e2e8f0;
            padding: 1rem 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .logo-section {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .logo {{
            width: 40px;
            height: 40px;
            border-radius: 8px;
            object-fit: contain;
        }}
        .brand {{
            font-size: 1.5rem;
            font-weight: 700;
            color: #1e293b;
        }}
        .controls {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}
        .auto-refresh-btn {{
            background: #10b981;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.875rem;
            font-weight: 500;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .auto-refresh-btn:hover {{ background: #059669; }}
        .auto-refresh-btn.paused {{ background: #ef4444; }}
        .auto-refresh-btn.paused:hover {{ background: #dc2626; }}
        .help-btn {{
            background: #3b82f6;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.875rem;
            font-weight: 500;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .help-btn:hover {{ background: #2563eb; }}
        .clear-btn {{
            background: #ef4444;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.875rem;
            font-weight: 500;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .clear-btn:hover {{ background: #dc2626; }}
        .clear-btn:disabled {{ 
            background: #9ca3af;
            cursor: not-allowed;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
        .page-header {{
            margin-bottom: 2rem;
        }}
        .page-title {{
            font-size: 2rem;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 0.5rem;
        }}
        .page-subtitle {{
            color: #64748b;
            font-size: 1rem;
        }}
        .stats-bar {{
            background: white;
            border-radius: 8px;
            padding: 1rem 1.5rem;
            margin-bottom: 2rem;
            border: 1px solid #e2e8f0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .stat {{
            text-align: center;
        }}
        .stat-value {{
            font-size: 1.5rem;
            font-weight: 700;
            color: #1e293b;
        }}
        .stat-label {{
            font-size: 0.875rem;
            color: #64748b;
            margin-top: 4px;
        }}
        .request-list {{
            space-y: 1rem;
        }}
        .request-item {{
            background: white;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
            overflow: hidden;
            transition: all 0.2s;
            margin-bottom: 1rem;
        }}
        .request-item:hover {{ box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        .request-header {{
            padding: 1rem 1.5rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: space-between;
            transition: background 0.2s;
        }}
        .request-header:hover {{ background: #f8fafc; }}
        .request-summary {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}
        .http-method {{
            font-weight: 700;
            font-size: 0.75rem;
            padding: 4px 8px;
            border-radius: 4px;
            color: white;
            text-transform: uppercase;
        }}
        .method-get {{ background: #10b981; }}
        .method-post {{ background: #3b82f6; }}
        .method-put {{ background: #f59e0b; }}
        .method-patch {{ background: #8b5cf6; }}
        .method-delete {{ background: #ef4444; }}
        .request-info {{
            display: flex;
            flex-direction: column;
        }}
        .request-title {{
            font-weight: 600;
            color: #1e293b;
        }}
        .request-meta {{
            font-size: 0.875rem;
            color: #64748b;
            margin-top: 2px;
        }}
        .request-time {{
            font-size: 0.875rem;
            color: #64748b;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .expand-icon {{
            transition: transform 0.2s;
            color: #64748b;
        }}
        .expand-icon.expanded {{ transform: rotate(180deg); }}
        .request-details {{
            border-top: 1px solid #f1f5f9;
            background: #f8fafc;
            overflow: hidden;
            transition: all 0.3s ease;
        }}
        .request-details:not(.expanded) {{
            max-height: 0;
            opacity: 0;
        }}
        .request-details.expanded {{
            max-height: 2000px;
            opacity: 1;
        }}
        .details-content {{
            padding: 1.5rem;
        }}
        .detail-section {{
            margin-bottom: 1.5rem;
        }}
        .detail-section:last-child {{ margin-bottom: 0; }}
        .detail-title {{
            font-weight: 600;
            color: #374151;
            margin-bottom: 0.5rem;
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .detail-content {{
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            padding: 0;
            font-family: 'SF Mono', Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
            font-size: 0.875rem;
            overflow-x: auto;
        }}
        .detail-content pre {{
            margin: 0;
            padding: 1rem;
            background: transparent;
            border: none;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .empty-state {{
            text-align: center;
            padding: 3rem;
            background: white;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        }}
        .empty-icon {{
            font-size: 3rem;
            margin-bottom: 1rem;
            color: #94a3b8;
        }}
        .empty-title {{
            font-size: 1.25rem;
            font-weight: 600;
            color: #374151;
            margin-bottom: 0.5rem;
        }}
        .empty-description {{
            color: #6b7280;
        }}
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
            animation: fadeIn 0.2s;
        }}
        .modal.show {{ display: flex; align-items: center; justify-content: center; }}
        .modal-content {{
            background: white;
            border-radius: 12px;
            padding: 2rem;
            max-width: 600px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04);
            animation: slideIn 0.3s;
        }}
        .modal-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
        }}
        .modal-title {{
            font-size: 1.5rem;
            font-weight: 700;
            color: #1e293b;
        }}
        .close-btn {{
            background: none;
            border: none;
            font-size: 1.5rem;
            color: #64748b;
            cursor: pointer;
            padding: 0;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 4px;
            transition: all 0.2s;
        }}
        .close-btn:hover {{ background: #f1f5f9; color: #1e293b; }}
        .endpoint-section {{
            margin-bottom: 1.5rem;
        }}
        .endpoint-title {{
            font-size: 1.125rem;
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .endpoint-method {{
            font-size: 0.75rem;
            padding: 2px 6px;
            border-radius: 3px;
            color: white;
            font-weight: 700;
        }}
        .endpoint-url {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 0.75rem;
            font-family: monospace;
            font-size: 0.875rem;
            color: #475569;
            margin: 0.5rem 0;
            word-break: break-all;
        }}
        .endpoint-description {{
            color: #64748b;
            font-size: 0.875rem;
            line-height: 1.5;
        }}
        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
        @keyframes slideIn {{ from {{ transform: translateY(-20px); opacity: 0; }} to {{ transform: translateY(0); opacity: 1; }} }}
        @media (max-width: 768px) {{
            .navbar {{ padding: 1rem; }}
            .container {{ padding: 1rem; }}
            .stats-bar {{ flex-direction: column; gap: 1rem; }}
            .request-summary {{ flex-direction: column; align-items: flex-start; gap: 0.5rem; }}
        }}
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="logo-section">
            <img src="/api/logo.png" alt="Logo" class="logo" onerror="this.style.display='none'">
            <div class="brand">API Monitor</div>
        </div>
        <div class="controls">
            <button class="help-btn" onclick="toggleHelp()">
                <span>❓</span>
                <span>Help</span>
            </button>
            <button class="auto-refresh-btn" id="autoRefreshBtn" onclick="toggleAutoRefresh()">
                <span id="refreshIcon">🔄</span>
                <span id="refreshText">Auto-refresh: 2s</span>
            </button>
        </div>
    </nav>
    
    <div class="container">
        <div class="page-header">
            <h1 class="page-title">Endpoint: /{path}</h1>
            <p class="page-subtitle">Monitor incoming HTTP requests in real-time</p>
        </div>
        
        <div class="stats-bar">
            <div class="stat">
                <div class="stat-value">{len(fresh_data.get(path, []))}</div>
                <div class="stat-label">Total Requests</div>
            </div>
            <div class="stat">
                <div class="stat-value">{len(fresh_data)}</div>
                <div class="stat-label">Active Endpoints</div>
            </div>
            <div class="stat">
                <div class="stat-value">{INSTANCE_ID}</div>
                <div class="stat-label">Instance ID</div>
            </div>
            <div class="stat">
                <div class="stat-value">{'✅' if AZURE_STORAGE_AVAILABLE else '❌'}</div>
                <div class="stat-label">Storage</div>
            </div>
        </div>
        
        <!-- Help Modal -->
        <div class="modal" id="helpModal" onclick="if(event.target === this) toggleHelp()">
            <div class="modal-content">
                <div class="modal-header">
                    <h2 class="modal-title">📚 API Endpoints & Help<br><small style="font-size: 0.75rem; font-weight: 400; color: #64748b;">💡 Tip: Pause auto-refresh to keep this modal open while reading</small></h2>
                    <button class="close-btn" onclick="toggleHelp()">×</button>
                </div>
                
                <div class="endpoint-section">
                    <div class="endpoint-title">
                        <span class="endpoint-method method-post">POST</span>
                        <span class="endpoint-method method-get">GET</span>
                        Mock API Endpoint
                    </div>
                    <div class="endpoint-url">/api/MockApiFunction</div>
                    <p class="endpoint-description">
                        Send any HTTP request (GET, POST, PUT, DELETE) to this endpoint. All requests are captured and stored for 1 hour. View captured requests in the dashboard above.
                    </p>
                </div>
                
                <div class="endpoint-section">
                    <div class="endpoint-title">
                        <span class="endpoint-method method-get">GET</span>
                        Inspect Dashboard
                    </div>
                    <div class="endpoint-url">/api/inspect/{{path}}?code=YOUR_KEY</div>
                    <p class="endpoint-description">
                        🔒 Protected endpoint. View captured requests in a beautiful web interface. Replace {{path}} with your endpoint name (e.g., MockApiFunction). Requires authentication key.
                    </p>
                </div>
                
                <div class="endpoint-section">
                    <div class="endpoint-title">
                        <span class="endpoint-method method-get">GET</span>
                        Health Check
                    </div>
                    <div class="endpoint-url">/api/health?code=YOUR_KEY</div>
                    <p class="endpoint-description">
                        🔒 Protected endpoint. Check system status, Azure Storage connectivity, and instance information. Requires authentication key.
                    </p>
                </div>
                
                <div class="endpoint-section">
                    <div class="endpoint-title">
                        <span class="endpoint-method method-get">GET</span>
                        Logo Asset
                    </div>
                    <div class="endpoint-url">/api/logo.png</div>
                    <p class="endpoint-description">
                        Serves the application logo image. No authentication required.
                    </p>
                </div>
                
                <div style="margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid #e2e8f0;">
                    <h3 style="font-size: 1rem; font-weight: 600; color: #1e293b; margin-bottom: 0.5rem;">ℹ️ Features</h3>
                    <ul style="color: #64748b; font-size: 0.875rem; line-height: 1.8; padding-left: 1.5rem;">
                        <li>⏱️ Auto-cleanup: Requests older than 1 hour are automatically removed</li>
                        <li>☁️ Azure Storage: Persistent data across function restarts</li>
                        <li>🔄 Auto-refresh: Dashboard updates every 2 seconds (can be paused)</li>
                        <li>📱 Responsive: Works on desktop and mobile devices</li>
                        <li>🔒 Secure: Protected endpoints require authentication keys</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <div class="request-list">
"""
            
            # Get data for the specified path from fresh storage data
            data = fresh_data.get(path, [])
            
            if not data:
                html_content += f"""
                <div class="empty-state">
                    <div class="empty-icon">📄</div>
                    <h3 class="empty-title">No requests yet</h3>
                    <p class="empty-description">Send a request to /{path} to see it appear here</p>
                    <div style="margin-top: 1rem; font-size: 0.875rem; color: #6b7280;">
                        Available endpoints: {', '.join(list(fresh_data.keys())) if fresh_data.keys() else 'None'}
                    </div>
                </div>
                """
            else:
                for i, req in enumerate(reversed(data)):  # Show newest first
                    timestamp = req.get('timestamp', 'Unknown')
                    method = req.get('method', 'Unknown')
                    instance_id = req.get('instance_id', 'Unknown')
                    
                    # Format timestamp
                    try:
                        from datetime import datetime as dt
                        dt_obj = dt.fromisoformat(timestamp.replace('Z', '+00:00'))
                        formatted_time = dt_obj.strftime('%H:%M:%S')
                        formatted_date = dt_obj.strftime('%Y-%m-%d')
                    except:
                        formatted_time = timestamp
                        formatted_date = 'Unknown'
                    
                    html_content += f"""
                    <div class="request-item">
                        <div class="request-header" onclick="toggleRequest({i})">
                            <div class="request-summary">
                                <span class="http-method method-{method.lower()}">{method}</span>
                                <div class="request-info">
                                    <div class="request-title">Request #{len(data) - i}</div>
                                    <div class="request-meta">Instance: {instance_id}</div>
                                </div>
                            </div>
                            <div class="request-time">
                                <span>{formatted_time}</span>
                                <span class="expand-icon" id="icon-{i}">▼</span>
                            </div>
                        </div>
                        <div class="request-details" id="details-{i}">
                            <div class="details-content">
                                <div class="detail-section">
                                    <div class="detail-title">Query Parameters</div>
                                    <div class="detail-content"><pre>{json.dumps(req.get('query', {}), indent=4, separators=(',', ': ')) if req.get('query') else 'No query parameters'}</pre></div>
                                </div>
                                
                                <div class="detail-section">
                                    <div class="detail-title">Request Headers</div>
                                    <div class="detail-content"><pre>{json.dumps(req.get('headers', {}), indent=4, separators=(',', ': ')) if req.get('headers') else 'No headers'}</pre></div>
                                </div>
                                
                                <div class="detail-section">
                                    <div class="detail-title">Request Body</div>
                                    <div class="detail-content"><pre>{json.dumps(req.get('body'), indent=4, separators=(',', ': ')) if req.get('body') else 'No body content'}</pre></div>
                                </div>
                            </div>
                        </div>
                    </div>
                    """
            
            html_content += f"""
        </div>
    </div>
    
    <script>
        // Path variable for API calls
        const currentPath = '{path}';
        console.log('Current path set to:', currentPath);
        
        // Get function key from URL query parameter
        const urlParams = new URLSearchParams(window.location.search);
        const functionKey = urlParams.get('code') || '';
        console.log('Function key present:', !!functionKey);
        
        let autoRefreshEnabled = true;
        let refreshInterval;
        let expandedStates = new Set();
        
        function toggleRequest(index) {{
            const details = document.getElementById(`details-${{index}}`);
            const icon = document.getElementById(`icon-${{index}}`);
            
            if (details.classList.contains('expanded')) {{
                details.classList.remove('expanded');
                icon.classList.remove('expanded');
                icon.textContent = '▼';
                expandedStates.delete(index);
            }} else {{
                details.classList.add('expanded');
                icon.classList.add('expanded');
                icon.textContent = '▲';
                expandedStates.add(index);
            }}
            
            // Store in localStorage
            localStorage.setItem('expandedStates', JSON.stringify([...expandedStates]));
        }}
        
        function restoreExpandedStates() {{
            try {{
                const stored = localStorage.getItem('expandedStates');
                if (stored) {{
                    const states = JSON.parse(stored);
                    states.forEach(index => {{
                        const details = document.getElementById(`details-${{index}}`);
                        const icon = document.getElementById(`icon-${{index}}`);
                        if (details && icon) {{
                            details.classList.add('expanded');
                            icon.classList.add('expanded');
                            icon.textContent = '▲';
                            expandedStates.add(index);
                        }}
                    }});
                }}
            }} catch (e) {{
                // Ignore localStorage errors
            }}
        }}
        
        function toggleHelp() {{
            const modal = document.getElementById('helpModal');
            const isShowing = modal.classList.contains('show');
            modal.classList.toggle('show');
            
            // Store modal state in localStorage
            if (isShowing) {{
                localStorage.removeItem('helpModalOpen');
            }} else {{
                localStorage.setItem('helpModalOpen', 'true');
            }}
        }}
        
        function restoreHelpModal() {{
            const wasOpen = localStorage.getItem('helpModalOpen');
            if (wasOpen === 'true') {{
                const modal = document.getElementById('helpModal');
                modal.classList.add('show');
            }}
        }}
        
        function toggleAutoRefresh() {{
            const btn = document.getElementById('autoRefreshBtn');
            const icon = document.getElementById('refreshIcon');
            const text = document.getElementById('refreshText');
            
            autoRefreshEnabled = !autoRefreshEnabled;
            
            if (autoRefreshEnabled) {{
                btn.classList.remove('paused');
                icon.textContent = '🔄';
                text.textContent = 'Auto-refresh: 2s';
                startAutoRefresh();
            }} else {{
                btn.classList.add('paused');
                icon.textContent = '⏸️';
                text.textContent = 'Paused';
                clearInterval(refreshInterval);
            }}
        }}
        
        function startAutoRefresh() {{
            if (refreshInterval) clearInterval(refreshInterval);
            refreshInterval = setInterval(() => {{
                if (autoRefreshEnabled) {{
                    // Preserve the code parameter when reloading
                    const currentUrl = new URL(window.location.href);
                    window.location.href = currentUrl.href;
                }}
            }}, 2000);
        }}
        
        async function clearRequests() {{
            console.log('clearRequests function called');
            
            if (!confirm('Are you sure you want to clear all requests for this endpoint?')) {{
                console.log('User cancelled clear operation');
                return;
            }}
            
            const clearBtn = document.querySelector('.clear-btn');
            if (!clearBtn) {{
                console.error('Clear button not found');
                return;
            }}
            
            console.log('Starting clear operation...');
            const originalText = clearBtn.innerHTML;
            clearBtn.disabled = true;
            clearBtn.innerHTML = '<span>⏳</span><span>Clearing...</span>';
            
            try {{
                // Build URL with function key if available
                let url = `/api/clear/${{currentPath}}`;
                if (functionKey) {{
                    url += `?code=${{functionKey}}`;
                }}
                console.log('Fetching:', url);
                
                const response = await fetch(url, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }}
                }});
                
                console.log('Response status:', response.status);
                console.log('Response ok:', response.ok);
                
                if (response.ok) {{
                    const result = await response.json();
                    console.log('Result:', result);
                    
                    if (result.success) {{
                        clearBtn.innerHTML = '<span>✅</span><span>Cleared!</span>';
                        console.log('Clear successful, clearing localStorage and reloading page in 1 second...');
                        
                        // Clear localStorage to reset expanded states
                        try {{
                            localStorage.removeItem('expandedStates');
                        }} catch (e) {{
                            console.log('Could not clear localStorage');
                        }}
                        
                        setTimeout(() => {{
                            window.location.reload(true); // Force reload from server
                        }}, 1000);
                    }} else {{
                        throw new Error(result.message || 'Clear operation failed');
                    }}
                }} else {{
                    const errorText = await response.text();
                    console.error('HTTP error response:', errorText);
                    throw new Error(`HTTP error! status: ${{response.status}} - ${{errorText}}`);
                }}
            }} catch (error) {{
                console.error('Error clearing requests:', error);
                clearBtn.innerHTML = '<span>❌</span><span>Error</span>';
                setTimeout(() => {{
                    clearBtn.disabled = false;
                    clearBtn.innerHTML = originalText;
                }}, 2000);
            }}
        }}
        
        // Initialize on page load
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('DOM loaded, initializing...');
            
            // Check if clear button exists and attach event
            const clearBtn = document.querySelector('.clear-btn');
            if (clearBtn) {{
                console.log('Clear button found, onclick should work');
            }} else {{
                console.error('Clear button NOT found');
            }}
            
            // Check if auto-refresh button exists
            const refreshBtn = document.getElementById('autoRefreshBtn');
            if (refreshBtn) {{
                console.log('Auto-refresh button found');
            }} else {{
                console.error('Auto-refresh button NOT found');
            }}
            
            restoreExpandedStates();
            restoreHelpModal();
            startAutoRefresh();
        }});
    </script>
</body>
</html>
"""
            return func.HttpResponse(
                html_content, 
                mimetype="text/html",
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
        
        # Return JSON data for API requests using fresh data
        data = fresh_data.get(path, [])
        
        return func.HttpResponse(
            body=json.dumps({"path": path, "requests": data}),
            mimetype="application/json",
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET",
                "Access-Control-Allow-Headers": "Content-Type, Accept",
                "Cache-Control": "no-cache"
            }
        )
        
    except Exception as e:
        logging.error(f"Error in inspect: {e}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)

@app.route(route="logo.png", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def serve_logo(req: func.HttpRequest) -> func.HttpResponse:
    """Serve the logo file"""
    try:
        import os
        # Look in the parent directory (root of the project)
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logo.png')
        if not os.path.exists(logo_path):
            # Fallback to current directory
            logo_path = os.path.join(os.path.dirname(__file__), 'logo.png')
        
        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as f:
                logo_data = f.read()
            return func.HttpResponse(logo_data, mimetype="image/png")
        else:
            return func.HttpResponse("Logo not found", status_code=404)
    except Exception as e:
        return func.HttpResponse(f"Error serving logo: {str(e)}", status_code=500)

@app.route(route="clear/{path}", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def clear_requests(req: func.HttpRequest) -> func.HttpResponse:
    """Clear all requests for a specific path"""
    path = req.route_params.get('path', '')
    
    try:
        # Load fresh data
        fresh_data = load_request_log()
        
        if path in fresh_data:
            removed_count = len(fresh_data[path]) if isinstance(fresh_data[path], list) else 0
            del fresh_data[path]
            
            # Update global REQUEST_LOG and save
            REQUEST_LOG.clear()
            REQUEST_LOG.update(fresh_data)
            save_request_log()
            
            logging.info(f"🗑️ Cleared {removed_count} requests from {path}")
            return func.HttpResponse(
                json.dumps({"message": f"Cleared {removed_count} requests from {path}", "success": True}),
                mimetype="application/json",
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "POST",
                    "Access-Control-Allow-Headers": "Content-Type"
                }
            )
        else:
            return func.HttpResponse(
                json.dumps({"message": f"No data found for path {path}", "success": False}),
                mimetype="application/json",
                status_code=404,
                headers={"Access-Control-Allow-Origin": "*"}
            )
            
    except Exception as e:
        logging.error(f"Error clearing requests: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e), "success": False}),
            mimetype="application/json",
            status_code=500,
            headers={"Access-Control-Allow-Origin": "*"}
        )

@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    # Test Azure Storage connectivity
    storage_test_result = False
    storage_error = None
    account_name = None
    
    try:
        if AZURE_STORAGE_AVAILABLE and blob_service_client:
            # Try to list containers as a connectivity test
            account_name = blob_service_client.account_name
            container_client = blob_service_client.get_container_client(CONTAINER_NAME)
            container_client.get_container_properties()
            storage_test_result = True
    except ResourceNotFoundError:
        # Container doesn't exist, but connection works
        storage_test_result = True
    except Exception as e:
        storage_error = str(e)
        logging.warning(f"Error testing storage connectivity: {e}")

    return func.HttpResponse(
        json.dumps({
            "status": "healthy",
            "instance_id": INSTANCE_ID,
            "instance_start_time": INSTANCE_START_TIME,
            "azure_storage_available": AZURE_STORAGE_AVAILABLE,
            "storage_connectivity_test": storage_test_result,
            "storage_error": storage_error,
            "storage_account": account_name,
            "container_name": CONTAINER_NAME,
            "blob_name": BLOB_NAME,
            "requests_captured": sum(len(v) if isinstance(v, list) else 0 for v in REQUEST_LOG.values()),
            "request_log_keys": list(REQUEST_LOG.keys()),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "available_endpoints": [
                "/api/MockApiFunction",
                "/api/inspect/MockApiFunction", 
                "/api/health"
            ]
        }),
        headers={"Content-Type": "application/json"}
    )