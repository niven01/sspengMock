# 🕵️ API Dashboard

A sophisticated Azure Functions-based mock API server with real-time request monitoring and an elegant web interface for intercepting and analyzing API traffic.

## ✨ Features

- **🎯 Mock API Endpoints**: Capture and respond to any HTTP request
- **🕵️ Real-time Monitoring**: Live web dashboard showing captured requests
- **📊 Request Analytics**: Detailed view of headers, body, query parameters
- **🎨 Beautiful UI**: Purple-themed responsive interface with animations
- **⏸️ Pause Controls**: Toggle auto-refresh for detailed inspection
- **💾 In-memory Storage**: Persistent request history during runtime

## 🚀 Quick Start

### Prerequisites
- Azure Functions Core Tools
- Python 3.9+
- Azure subscription (for deployment)

### Local Development

1. **Clone and navigate to the project**:
   ```bash
   git clone <repository-url>
   cd sspengMock
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the Azure Functions runtime**:
   ```bash
   func start
   ```

4. **Access the API**:
   - Mock API: `http://sspengmock-e6ghe2fthbdqhaeb.uksouth-01.azurewebsites.net/api/MockApiFunction`
   - Web Dashboard: `http://sspengmock-e6ghe2fthbdqhaeb.uksouth-01.azurewebsites.net/api/inspect/MockApiFunction`

## 📡 API Endpoints

### 🎯 Mock Endpoints

#### Main Mock Endpoint
```
POST|GET|PUT|DELETE /api/MockApiFunction
```
Captures requests to the main mock endpoint.

**Example Request**:
```bash
curl -X POST http://sspengmock-e6ghe2fthbdqhaeb.uksouth-01.azurewebsites.net/api/MockApiFunction \
  -H "Content-Type: application/json" \
  -d '{"user": "john", "action": "login"}'
```

**Response**:
```json
{
  "message": "Mock endpoint captured your request.",
  "path": "MockApiFunction",
  "request_id": 0,
  "captured_request": {
    "timestamp": "2025-11-27T15:30:00.000Z",
    "method": "POST",
    "path": "MockApiFunction",
    "query": {},
    "headers": {
      "content-type": "application/json",
      "user-agent": "curl/7.68.0"
    },
    "body": {
      "user": "john",
      "action": "login"
    }
  }
}
```

#### Dynamic Mock Endpoint
```
GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS /api/mock/{path}
```
Captures requests to any dynamic path for flexible testing.

**Example**:
```bash
# Mock a user API
curl -X GET http://sspengmock-e6ghe2fthbdqhaeb.uksouth-01.azurewebsites.net/api/mock/users/123

# Mock a products API  
curl -X POST http://sspengmock-e6ghe2fthbdqhaeb.uksouth-01.azurewebsites.net/api/mock/products \
  -d '{"name": "Widget", "price": 29.99}'
```

### 🔍 Inspection Endpoints

#### Web Dashboard
```
GET /api/inspect/{path}
```
Access the beautiful web interface for real-time request monitoring.

**URLs**:
- `http://sspengmock-e6ghe2fthbdqhaeb.uksouth-01.azurewebsites.net/api/inspect/MockApiFunction` - Monitor main endpoint
- `http://sspengmock-e6ghe2fthbdqhaeb.uksouth-01.azurewebsites.net/api/inspect/users` - Monitor `/api/mock/users` requests
- `http://sspengmock-e6ghe2fthbdqhaeb.uksouth-01.azurewebsites.net/api/inspect/products` - Monitor `/api/mock/products` requests

#### JSON API
```
GET /api/inspect/{path}
Accept: application/json
```
Retrieve captured requests as JSON data.

**Response**:
```json
{
  "path": "MockApiFunction",
  "requests": [
    {
      "timestamp": "2025-11-27T15:30:00.000Z",
      "method": "POST",
      "path": "MockApiFunction",
      "query": {"param1": "value1"},
      "headers": {"content-type": "application/json"},
      "body": {"key": "value"}
    }
  ]
}
```

## 🎨 Web Dashboard Features

### 📊 Request Cards
- **Collapsible design**: Click to expand/collapse request details
- **Method badges**: Color-coded HTTP methods (GET, POST, PUT, DELETE, PATCH)
- **Body indicators**: "HAS BODY" badge for requests with payloads
- **Timestamps**: Local time formatting for easy reading

### 🎯 Organized Data Display
- **Query Parameters**: Clean key-value grid layout
- **Important Headers**: Highlighted essential headers (content-type, authorization, etc.)
- **Request Body**: Formatted JSON with syntax highlighting
- **All Headers**: Complete header information in expandable sections

### ⏸️ Interactive Controls
- **Auto-refresh toggle**: Pause monitoring for detailed inspection
- **State preservation**: Expanded cards stay open during refreshes
- **Responsive design**: Works on desktop and mobile devices

### 🎨 Purple Theme
- **Gradient backgrounds**: Modern glass morphism effects
- **Smooth animations**: Hover effects and transitions
- **Professional styling**: Clean, readable typography

## 🔧 Configuration

### Environment Variables
Create a `local.settings.json` file:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python"
  }
}
```

### Host Configuration
The `host.json` file configures the Azure Functions runtime:

```json
{
  "version": "2.0"
}
```

## 📝 Use Cases

### 🧪 API Testing
Perfect for testing client applications against mock endpoints:

```javascript
// Test your frontend against the mock API
fetch('http://sspengmock-e6ghe2fthbdqhaeb.uksouth-01.azurewebsites.net/api/mock/users', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({name: 'Test User'})
})
```

### 🕵️ Request Inspection
Monitor what your applications are actually sending:

1. Send requests to mock endpoints
2. Open the web dashboard
3. Inspect headers, body, and parameters in real-time
4. Pause auto-refresh to examine details

### 🔄 Integration Testing
Test webhooks and callbacks:

```bash
# Configure your service to send webhooks to:
http://your-domain.com/api/mock/webhooks/stripe

# Then monitor at:
http://your-domain.com/api/inspect/webhooks/stripe
```

## 🚀 Deployment

### Azure Functions Deployment

1. **Create Azure Function App**:
   ```bash
   az functionapp create \
     --resource-group myResourceGroup \
     --consumption-plan-location westus \
     --name myMockApi \
     --storage-account mystorageaccount \
     --runtime python \
     --runtime-version 3.9
   ```

2. **Deploy the function**:
   ```bash
   func azure functionapp publish myMockApi
   ```

3. **Access your deployed API**:
   - Mock API: `https://myMockApi.azurewebsites.net/api/MockApiFunction`
   - Dashboard: `https://myMockApi.azurewebsites.net/api/inspect/MockApiFunction`

## 📊 Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│                 │    │                  │    │                 │
│   Client App    ├────► Mock API Endpoint ├────► In-Memory Store │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                │                        │
                       ┌────────▼────────┐    ┌─────────▼─────────┐
                       │                 │    │                 │
                       │  Web Dashboard  ◄────┤ Inspect Endpoint │
                       │                 │    │                 │
                       └─────────────────┘    └───────────────────┘
```

## 🛠️ Development

### Adding New Features

1. **New Mock Endpoints**: Add routes in `function_app.py`
2. **Custom Response Logic**: Modify the mock endpoint functions
3. **Enhanced UI**: Update the HTML template in `inspect_endpoint`
4. **Data Storage**: Extend the `REQUEST_LOG` structure

### Code Structure

```
sspengMock/
├── function_app.py          # Main Azure Function code
├── host.json               # Azure Functions configuration
├── local.settings.json     # Local environment settings
├── requirements.txt        # Python dependencies
└── README.md              # This documentation
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Troubleshooting

### Common Issues

**Function not loading**:
- Ensure Python 3.9+ is installed
- Check `requirements.txt` dependencies
- Verify `function_app.py` is in the root directory

**Dashboard not showing requests**:
- Check browser developer console for errors
- Ensure requests are being sent to the correct mock endpoints
- Verify auto-refresh is enabled (green button)

**CORS issues**:
- Add CORS headers in the function response if needed for browser access

### Getting Help

- Check Azure Functions documentation
- Review function logs in the Azure portal
- Enable verbose logging in `local.settings.json`

---

Made with 💜 by the API Spy Dashboard team 🕵️‍♂️