import logging
import json
import azure.functions as func
from datetime import datetime
import os

app = func.FunctionApp()

# very simple in-memory store: { path: [request_record, ...] }
# Initialize with some debug info to help troubleshoot
REQUEST_LOG = {
    "_debug": [{
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "message": "REQUEST_LOG initialized",
        "app_startup": True
    }]
}

@app.route(
    route="test",
    methods=["GET", "POST"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
def test_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """Simple test endpoint to verify basic functionality"""
    logging.info("test_endpoint: START %s %s", req.method, req.url)
    
    # Force add a test entry to REQUEST_LOG
    test_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "method": req.method,
        "path": "test",
        "message": "Test endpoint was called successfully",
        "query": dict(req.params),
        "headers": dict(req.headers)
    }
    
    REQUEST_LOG.setdefault("test", []).append(test_entry)
    
    logging.info("test_endpoint: Added test entry. REQUEST_LOG keys: %s", list(REQUEST_LOG.keys()))
    logging.info("test_endpoint: REQUEST_LOG sizes: %s", {k: len(v) for k, v in REQUEST_LOG.items()})
    
    return func.HttpResponse(
        body=json.dumps({
            "message": "Test endpoint working!",
            "request_log_keys": list(REQUEST_LOG.keys()),
            "request_counts": {k: len(v) for k, v in REQUEST_LOG.items()},
            "test_entry": test_entry
        }, indent=2),
        mimetype="application/json",
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST",
            "Access-Control-Allow-Headers": "Content-Type, Accept"
        }
    )

@app.route(
    route="debug",
    methods=["GET"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
def debug_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """Debug endpoint to show raw REQUEST_LOG data"""
    logging.info("debug_endpoint: START")
    
    return func.HttpResponse(
        body=json.dumps({
            "raw_request_log": REQUEST_LOG,
            "keys": list(REQUEST_LOG.keys()),
            "data_types": {k: type(v).__name__ for k, v in REQUEST_LOG.items()},
            "lengths": {k: len(v) if isinstance(v, (list, dict, str)) else "N/A" for k, v in REQUEST_LOG.items()}
        }, indent=2, default=str),
        mimetype="application/json",
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Headers": "Content-Type, Accept"
        }
    )

@app.route(
    route="MockApiFunction",
    methods=["GET", "POST", "PUT", "DELETE"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
def main_mock_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("=" * 60)
    logging.info("main_mock_endpoint: FUNCTION CALLED!")
    logging.info("main_mock_endpoint: Method=%s URL=%s", req.method, req.url)
    logging.info("main_mock_endpoint: Headers=%s", dict(req.headers))
    logging.info("main_mock_endpoint: Query=%s", dict(req.params))
    logging.info("main_mock_endpoint: Route params=%s", req.route_params)
    logging.info("main_mock_endpoint: Current REQUEST_LOG keys before processing: %s", list(REQUEST_LOG.keys()))
    logging.info("=" * 60)
    
    try:
        # Use the route as the path for main endpoint
        path = "MockApiFunction"
        
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
            logging.info("main_mock_endpoint: parsed JSON body")
        except ValueError:
            try:
                record["body"] = req.get_body().decode("utf-8")
                logging.info("main_mock_endpoint: parsed text body")
            except Exception:
                logging.warning("main_mock_endpoint: could not read body")
                record["body"] = None

        REQUEST_LOG.setdefault(path, []).append(record)
        logging.info(
            "main_mock_endpoint: stored request for '%s' (total=%d)",
            path,
            len(REQUEST_LOG[path]),
        )
        logging.info("main_mock_endpoint: REQUEST_LOG now contains keys: %s", list(REQUEST_LOG.keys()))
        logging.info("main_mock_endpoint: REQUEST_LOG sizes: %s", {k: len(v) for k, v in REQUEST_LOG.items()})
        
        # Force log the actual record that was stored
        logging.info("main_mock_endpoint: STORED RECORD: %s", json.dumps(record, default=str))

        response_body = {
            "message": "Mock endpoint captured your request.",
            "path": path,
            "request_id": len(REQUEST_LOG[path]) - 1,
            "captured_request": record,
        }

        logging.info(
            "main_mock_endpoint: returning 200 for path '%s', request_id=%d",
            path,
            response_body["request_id"],
        )

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
        # log full stack trace and return a safe 500
        logging.exception("main_mock_endpoint: FAILED with unhandled exception: %s", e)
        return func.HttpResponse(
            body=json.dumps({"error": "internal server error"}),
            mimetype="application/json",
            status_code=500,
        )

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
        logging.info("mock_endpoint: REQUEST_LOG now contains keys: %s", list(REQUEST_LOG.keys()))
        logging.info("mock_endpoint: REQUEST_LOG sizes: %s", {k: len(v) for k, v in REQUEST_LOG.items()})
        logging.debug("mock_endpoint: record=%s", json.dumps(record))

        response_body = {
            "message": "Mock endpoint captured your request.",
            "path": path,
            "request_id": len(REQUEST_LOG[path]) - 1,
            "captured_request": record,
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
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Accept"
            }
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
    route="inspect",
    methods=["GET"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
def inspect_all_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """Inspect endpoint without path parameter to show all captured requests"""
    logging.info("inspect_all_endpoint: START %s %s", req.method, req.url)
    logging.info("inspect_all_endpoint: Current REQUEST_LOG: %s", {k: len(v) for k, v in REQUEST_LOG.items()})
    
    try:
        # Check if this is a request for the HTML interface
        accept_header = req.headers.get("accept", "").lower()
        user_agent = req.headers.get("user-agent", "").lower()
        
        # More flexible content negotiation for Azure Functions
        is_browser_request = (
            "text/html" in accept_header or 
            "mozilla" in user_agent or 
            "chrome" in user_agent or 
            "safari" in user_agent or
            "edge" in user_agent
        )
        
        # Explicit JSON request check
        is_json_request = (
            "application/json" in accept_header or
            req.params.get("format") == "json"
        )
        
        if is_browser_request and not is_json_request:
            # Return HTML interface showing all paths
            all_paths = list(REQUEST_LOG.keys())
            paths_html = ""
            if all_paths:
                paths_html = "<ul>" + "".join([f'<li><a href="/api/inspect/{path}" style="color: white; text-decoration: underline;">{path} ({len(REQUEST_LOG[path])} requests)</a></li>' for path in all_paths]) + "</ul>"
            else:
                paths_html = "<p>No requests captured yet.</p>"
            
            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Inspector - All Paths</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, #8B5A96, #6A4C93);
            color: white;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(139, 90, 150, 0.3);
        }}
        ul {{
            background: rgba(248, 249, 250, 0.1);
            padding: 20px;
            border-radius: 8px;
            list-style: none;
        }}
        li {{
            padding: 10px;
            margin: 5px 0;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🕵️ API Spy Dashboard - All Paths</h1>
            <p>Overview of all captured request paths</p>
        </div>
        
        <div>
            <h2>Captured Request Paths:</h2>
            {paths_html}
        </div>
        
        <div style="margin-top: 30px; background: rgba(0,0,0,0.3); padding: 15px; border-radius: 8px;">
            <strong>Debug Info:</strong><br>
            Total paths: {len(all_paths)}<br>
            All REQUEST_LOG keys: {list(REQUEST_LOG.keys())}<br>
            Total requests: {sum(len(v) for v in REQUEST_LOG.values())}
        </div>
    </div>
</body>
</html>
"""
            return func.HttpResponse(
                body=html_content,
                mimetype="text/html",
                status_code=200,
            )
        
        # Return JSON data for API requests - show all paths
        all_data = {path: {"path": path, "requests": requests} for path, requests in REQUEST_LOG.items()}
        
        return func.HttpResponse(
            body=json.dumps({"all_paths": all_data, "total_requests": sum(len(v) if isinstance(v, list) else 0 for v in REQUEST_LOG.values())}, indent=2),
            mimetype="application/json",
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Accept",
                "Cache-Control": "no-cache"
            }
        )

    except Exception as e:
        logging.exception("inspect_all_endpoint: FAILED with unhandled exception: %s", e)
        return func.HttpResponse(
            body=json.dumps({"error": "internal server error", "details": str(e)}),
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
    logging.info("inspect_endpoint: Headers: %s", dict(req.headers))
    logging.info("inspect_endpoint: Query params: %s", dict(req.params))
    
    try:
        path = req.route_params.get("path", "")
        logging.info("inspect_endpoint: path='%s'", path)
        logging.info("inspect_endpoint: Current REQUEST_LOG keys: %s", list(REQUEST_LOG.keys()))
        logging.info("inspect_endpoint: REQUEST_LOG contents: %s", {k: len(v) for k, v in REQUEST_LOG.items()})
        
        # Check if this is a request for the HTML interface
        accept_header = req.headers.get("accept", "").lower()
        user_agent = req.headers.get("user-agent", "").lower()
        
        # More flexible content negotiation for Azure Functions
        is_browser_request = (
            "text/html" in accept_header or 
            "mozilla" in user_agent or 
            "chrome" in user_agent or 
            "safari" in user_agent or
            "edge" in user_agent
        )
        
        # Explicit JSON request check
        is_json_request = (
            "application/json" in accept_header or
            req.params.get("format") == "json"
        )
        
        if is_browser_request and not is_json_request:
            # Return HTML interface
            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Inspector - {path}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, #8B5A96, #6A4C93);
            color: white;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(139, 90, 150, 0.3);
        }}
        .path-info {{
            background: rgba(106, 76, 147, 0.9);
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
        }}
        .request-card {{
            background: white;
            border-radius: 8px;
            margin-bottom: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .request-header {{
            background: linear-gradient(135deg, #9B59B6, #8E44AD);
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        .request-header:hover {{
            background: linear-gradient(135deg, #A569BD, #9B59B6);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(155, 89, 182, 0.4);
        }}
        .method {{
            font-weight: bold;
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 0.85em;
            margin-right: 10px;
        }}
        .method-get {{ background: #27ae60; }}
        .method-post {{ background: #e74c3c; }}
        .method-put {{ background: #f39c12; }}
        .method-delete {{ background: #8e44ad; }}
        .method-patch {{ background: #16a085; }}
        .request-summary {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .request-body {{
            padding: 0;
            display: none;
        }}
        .request-body.expanded {{
            display: block;
        }}
        .section-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            padding: 20px;
        }}
        .section {{
            background: rgba(248, 249, 250, 0.95);
            border-radius: 8px;
            padding: 15px;
            border-left: 4px solid #9B59B6;
            backdrop-filter: blur(5px);
        }}
        .section-title {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 1.1em;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .section-body {{
            grid-column: 1 / -1;
        }}
        .key-value-grid {{
            display: grid;
            gap: 8px;
        }}
        .key-value-item {{
            display: grid;
            grid-template-columns: 200px 1fr;
            gap: 10px;
            padding: 8px 0;
            border-bottom: 1px solid #e9ecef;
        }}
        .key-value-item:last-child {{
            border-bottom: none;
        }}
        .key {{
            font-weight: 600;
            color: #495057;
            word-break: break-word;
        }}
        .value {{
            font-family: 'Consolas', 'Monaco', monospace;
            background: white;
            padding: 4px 8px;
            border-radius: 3px;
            border: 1px solid #dee2e6;
            word-break: break-all;
        }}
        .json-body {{
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 15px;
            font-family: 'Consolas', 'Monaco', monospace;
            white-space: pre-wrap;
            overflow-x: auto;
            max-height: 300px;
            overflow-y: auto;
        }}
        .empty-data {{
            color: #6c757d;
            font-style: italic;
            text-align: center;
            padding: 20px;
        }}
        .no-requests {{
            text-align: center;
            color: #7f8c8d;
            padding: 40px;
            background: white;
            border-radius: 8px;
        }}
        .auto-refresh {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #9B59B6, #8E44AD);
            color: white;
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 0.8em;
            z-index: 1000;
            cursor: pointer;
            user-select: none;
        }}
        .auto-refresh.paused {{
            background: #e74c3c;
        }}
        .auto-refresh:hover {{
            opacity: 0.8;
        }}
        .toggle-icon {{
            transition: transform 0.3s ease;
        }}
        .toggle-icon.expanded {{
            transform: rotate(180deg);
        }}
        .highlight {{
            background: #fff3cd !important;
            border-color: #ffeaa7 !important;
        }}
        .important-headers {{
            background: #e8f5e8 !important;
        }}
        @media (max-width: 768px) {{
            .section-grid {{
                grid-template-columns: 1fr;
            }}
            .key-value-item {{
                grid-template-columns: 1fr;
                gap: 5px;
            }}
            .container {{
                padding: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="auto-refresh" id="auto-refresh-btn" onclick="toggleAutoRefresh()">🔄 Auto-refreshing every 2s</div>
    
    <div class="container">
        <div class="header">
            <h1>🔍 API Inspector</h1>
            <p>Real-time monitoring of captured requests</p>
        </div>
        
        <div class="path-info">
            <strong>Monitoring Path:</strong> <code>{path if path else '(all paths)'}</code>
        </div>
        
        <div id="requests-container">
            <div class="no-requests">
                Loading requests...
            </div>
        </div>
        
        <!-- Debug Information Panel -->
        <div id="debug-panel" style="position: fixed; bottom: 20px; left: 20px; background: rgba(0,0,0,0.8); color: white; padding: 10px; border-radius: 8px; font-family: monospace; font-size: 12px; max-width: 400px; max-height: 200px; overflow-y: auto; z-index: 1000;">
            <div style="font-weight: bold; margin-bottom: 5px;">🔍 Debug Info</div>
            <div id="debug-content">Initializing...</div>
        </div>
    </div>

    <script>
        const path = '{path}';
        const container = document.getElementById('requests-container');
        const debugPanel = document.getElementById('debug-content');
        let expandedRequests = new Set(); // Track which requests are expanded
        let autoRefreshEnabled = true;
        let refreshInterval;
        let requestCounter = 0; // Counter to assign stable IDs to requests
        let lastRequestsHash = ''; // To detect if data actually changed
        
        function debugLog(message) {{
            const timestamp = new Date().toLocaleTimeString();
            console.log(`[${{timestamp}}] ${{message}}`);
            debugPanel.innerHTML += `<div>[${{timestamp}}] ${{message}}</div>`;
            debugPanel.scrollTop = debugPanel.scrollHeight;
        }}
        
        debugLog(`Initialized for path: '${{path}}'`);
        
        function formatJson(obj) {{
            if (obj === null || obj === undefined) {{
                return '<div class="empty-data">No data</div>';
            }}
            if (typeof obj === 'string' && obj === '') {{
                return '<div class="empty-data">Empty</div>';
            }}
            if (typeof obj === 'object' && Object.keys(obj).length === 0) {{
                return '<div class="empty-data">No data</div>';
            }}
            return JSON.stringify(obj, null, 2);
        }}
        
        function getMethodClass(method) {{
            const methodLower = method.toLowerCase();
            return `method method-${{methodLower}}`;
        }}
        
        function isImportantHeader(key) {{
            const important = ['content-type', 'authorization', 'user-agent', 'host', 'content-length'];
            return important.includes(key.toLowerCase());
        }}
        
        function renderKeyValueGrid(data, isHeaders = false) {{
            if (!data || Object.keys(data).length === 0) {{
                return '<div class="empty-data">No data available</div>';
            }}
            
            return Object.entries(data).map(([key, value]) => {{
                const itemClass = isHeaders && isImportantHeader(key) ? 'key-value-item important-headers' : 'key-value-item';
                return `
                    <div class="${{itemClass}}">
                        <div class="key">${{key}}</div>
                        <div class="value">${{typeof value === 'string' ? value : JSON.stringify(value)}}</div>
                    </div>
                `;
            }}).join('');
        }}
        
        function generateRequestHash(requests) {{
            // Create a hash of the requests to detect changes
            return JSON.stringify(requests.map(r => ({{
                timestamp: r.timestamp,
                method: r.method,
                bodyLength: JSON.stringify(r.body).length
            }})));
        }}
        
        function renderRequests(data) {{
            const requests = data.requests || [];
            
            if (requests.length === 0) {{
                container.innerHTML = '<div class="no-requests">No requests captured yet for this path.</div>';
                requestCounter = 0;
                return;
            }}
            
            // Check if the data actually changed
            const currentHash = generateRequestHash(requests);
            if (currentHash === lastRequestsHash) {{
                // Data hasn't changed, don't re-render
                return;
            }}
            lastRequestsHash = currentHash;
            
            // Reset counter if we have fewer requests (cleared or reset)
            if (requests.length < requestCounter) {{
                requestCounter = 0;
                expandedRequests.clear();
            }}
            
            const html = requests.map((req, index) => {{
                const timestamp = new Date(req.timestamp).toLocaleString();
                const hasBody = req.body && (typeof req.body === 'object' ? Object.keys(req.body).length > 0 : req.body !== '');
                const bodyClass = hasBody ? 'highlight' : '';
                
                // Use the index from the end as a stable ID (newest requests get higher IDs)
                const requestId = `req-${{requests.length - 1 - index}}`;
                const isExpanded = expandedRequests.has(requestId);
                const expandedClass = isExpanded ? 'expanded' : '';
                const toggleIcon = isExpanded ? '▲' : '▼';
                
                return `
                    <div class="request-card">
                        <div class="request-header" onclick="toggleRequest('${{requestId}}')">
                            <div class="request-summary">
                                <span class="${{getMethodClass(req.method)}}">${{req.method}}</span>
                                <strong>${{req.path || 'Unknown'}}</strong>
                                ${{hasBody ? '<span style="background: #f39c12; padding: 2px 6px; border-radius: 3px; font-size: 0.7em;">HAS BODY</span>' : ''}}
                            </div>
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span>${{timestamp}}</span>
                                <span class="toggle-icon ${{expandedClass}}" id="toggle-${{requestId}}">${{toggleIcon}}</span>
                            </div>
                        </div>
                        <div class="request-body ${{expandedClass}}" id="body-${{requestId}}">
                            <div class="section-grid">
                                <div class="section">
                                    <div class="section-title">
                                        📋 Query Parameters
                                    </div>
                                    <div class="key-value-grid">
                                        ${{renderKeyValueGrid(req.query)}}
                                    </div>
                                </div>
                                <div class="section">
                                    <div class="section-title">
                                        🔧 Important Headers
                                    </div>
                                    <div class="key-value-grid">
                                        ${{renderKeyValueGrid(
                                            Object.fromEntries(
                                                Object.entries(req.headers || {{}}).filter(([key]) => isImportantHeader(key))
                                            ), true
                                        )}}
                                    </div>
                                </div>
                                <div class="section section-body ${{bodyClass}}">
                                    <div class="section-title">
                                        📦 Request Body ${{hasBody ? '(Contains Data)' : '(Empty)'}}
                                    </div>
                                    <div class="json-body">
${{formatJson(req.body)}}
                                    </div>
                                </div>
                                <div class="section">
                                    <div class="section-title">
                                        📡 All Headers
                                    </div>
                                    <div class="key-value-grid">
                                        ${{renderKeyValueGrid(req.headers, true)}}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }}).join(''); // Don't reverse - keep original order with newest first
            
            container.innerHTML = html;
            requestCounter = requests.length;
        }}
        
        function toggleRequest(requestId) {{
            const body = document.getElementById(`body-${{requestId}}`);
            const toggle = document.getElementById(`toggle-${{requestId}}`);
            
            if (expandedRequests.has(requestId)) {{
                expandedRequests.delete(requestId);
                body.classList.remove('expanded');
                toggle.classList.remove('expanded');
                toggle.textContent = '▼';
            }} else {{
                expandedRequests.add(requestId);
                body.classList.add('expanded');
                toggle.classList.add('expanded');
                toggle.textContent = '▲';
            }}
        }}
        
        function toggleAutoRefresh() {{
            const btn = document.getElementById('auto-refresh-btn');
            autoRefreshEnabled = !autoRefreshEnabled;
            
            if (autoRefreshEnabled) {{
                btn.textContent = '🔄 Auto-refreshing every 2s';
                btn.classList.remove('paused');
                startAutoRefresh();
            }} else {{
                btn.textContent = '⏸️ Auto-refresh paused (click to resume)';
                btn.classList.add('paused');
                clearInterval(refreshInterval);
            }}
        }}
        
        function fetchData() {{
            if (!autoRefreshEnabled) return;
            
            debugLog('Starting fetch request...');
            
            // Build URL more robustly for Azure Functions
            let url = window.location.pathname;
            if (!url.endsWith('/')) {{
                url = window.location.href;
            }}
            
            // Add explicit JSON format parameter for Azure Functions
            const separator = url.includes('?') ? '&' : '?';
            const fetchUrl = url + separator + 'format=json';
            
            debugLog(`Fetch URL: ${{fetchUrl}}`);
            
            fetch(fetchUrl, {{
                headers: {{
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }}
            }})
            .then(response => {{
                debugLog(`Response status: ${{response.status}} ${{response.statusText}}`);
                debugLog(`Response headers: ${{JSON.stringify(Object.fromEntries(response.headers.entries()))}}`);
                if (!response.ok) {{
                    throw new Error(`HTTP ${{response.status}}: ${{response.statusText}}`);
                }}
                return response.text(); // Get as text first for debugging
            }})
            .then(text => {{
                debugLog(`Raw response: ${{text.substring(0, 200)}}...`);
                try {{
                    const data = JSON.parse(text);
                    debugLog(`Parsed JSON successfully. Requests count: ${{(data.requests || []).length}}`);
                    renderRequests(data);
                }} catch (e) {{
                    debugLog(`JSON parse error: ${{e.message}}`);
                    container.innerHTML = `<div class="no-requests">Error parsing JSON response. Check debug panel.</div>`;
                }}
            }})
            .catch(error => {{
                debugLog(`Fetch error: ${{error.message}}`);
                console.error('Error fetching data:', error);
                container.innerHTML = `<div class="no-requests">Error loading requests: ${{error.message}}<br>Check debug panel for details.</div>`;
            }});
        }}
        
        function startAutoRefresh() {{
            refreshInterval = setInterval(fetchData, 2000);
        }}
        
        // Make functions available globally
        window.toggleRequest = toggleRequest;
        window.toggleAutoRefresh = toggleAutoRefresh;
        
        // Initial load
        fetchData();
        
        // Start auto-refresh
        startAutoRefresh();
    </script>
</body>
</html>
"""
            return func.HttpResponse(
                body=html_content,
                mimetype="text/html",
                status_code=200,
            )
        
        # Return JSON data for API requests
        data = REQUEST_LOG.get(path, [])
        
        logging.info("inspect_endpoint: Raw data for path '%s': %s", path, data)
        
        # Temporarily remove filtering to see all data
        if not isinstance(data, list):
            logging.info("inspect_endpoint: Data is not a list, using empty list")
            data = []
            
        logging.info(
            "inspect_endpoint: returning %d records for path '%s'",
            len(data),
            path,
        )

        response_body = json.dumps({"path": path, "requests": data})
        
        return func.HttpResponse(
            body=response_body,
            mimetype="application/json",
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Accept",
                "Cache-Control": "no-cache"
            }
        )

    except Exception as e:
        logging.exception("inspect_endpoint: FAILED with unhandled exception: %s", e)
        return func.HttpResponse(
            body=json.dumps({"error": "internal server error"}),
            mimetype="application/json",
            status_code=500,
        )

@app.route(
    route="health",
    methods=["GET"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Simple health check endpoint to verify function app is working"""
    logging.info("health_check: START")
    logging.info("health_check: Current REQUEST_LOG: %s", REQUEST_LOG)
    
    health_info = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "request_log_keys": list(REQUEST_LOG.keys()),
        "request_log_full": REQUEST_LOG,
        "total_requests": sum(len(v) if isinstance(v, list) else 0 for v in REQUEST_LOG.values()),
        "version": "1.0",
        "function_url": str(req.url),
        "function_method": req.method,
        "available_routes": [
            "/api/test",
            "/api/MockApiFunction", 
            "/api/mock/{path}",
            "/api/inspect",
            "/api/inspect/{path}",
            "/api/health"
        ]
    }
    
    return func.HttpResponse(
        body=json.dumps(health_info, indent=2),
        mimetype="application/json",
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Headers": "Content-Type, Accept"
        }
    )
