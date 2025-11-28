# 🕵️ API Monitor

A professional Azure Functions-based API monitoring and mocking platform with a sleek Beeceptor-style interface for intercepting, analyzing, and managing HTTP requests in real-time.

## ✨ Key Features

### 🎯 **Smart API Mocking**
- **Universal endpoint capture**: Intercept any HTTP request (GET, POST, PUT, DELETE, PATCH)
- **Automatic persistence**: Azure Blob Storage with cross-instance data sharing
- **Real-time processing**: Instant request capture with detailed metadata
- **JSON-first design**: Intelligent content parsing and formatting

### 🖥️ **Professional Web Interface**
- **Beeceptor-inspired design**: Clean, modern UI matching industry standards
- **Logo integration**: Branded interface with custom logo support
- **Responsive layout**: Works perfectly on desktop and mobile
- **Live statistics bar**: Request counts, active endpoints, and system status

### 🔧 **Advanced Management**
- **Auto-cleanup**: Requests older than 1 hour automatically removed
- **Manual clearing**: One-click clear all functionality with confirmation
- **Collapsible views**: Expandable request cards with state persistence
- **Auto-refresh control**: 2-second refresh with pause/resume capability

### 📊 **Rich Request Analytics**
- **Beautifully formatted JSON**: 4-space indentation with proper line breaks
- **HTTP method badges**: Color-coded method indicators (GET=green, POST=blue, etc.)
- **Detailed inspection**: Headers, query parameters, and request body
- **Instance tracking**: Multi-instance deployment visibility

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

## 🚀 Live Demo

**Try it now**: https://sspengmock-e6ghe2fthbdqhaeb.uksouth-01.azurewebsites.net/api/inspect/MockApiFunction

### Quick Test
```bash
# Send a test request
curl -X POST https://sspengmock-e6ghe2fthbdqhaeb.uksouth-01.azurewebsites.net/api/MockApiFunction \
  -H "Content-Type: application/json" \
  -d '{"test": "hello world", "timestamp": "'$(date)'"}'  

# View in the web interface
open https://sspengmock-e6ghe2fthbdqhaeb.uksouth-01.azurewebsites.net/api/inspect/MockApiFunction
```

## 📡 API Endpoints

### 🎯 Mock Endpoint

#### Primary Mock API
```
POST|GET|PUT|DELETE /api/MockApiFunction
```
**Features**:
- ✅ Captures all request details (headers, body, query params)
- ✅ Automatic cleanup (removes requests older than 1 hour)
- ✅ Cross-instance persistence via Azure Storage
- ✅ JSON response with captured request details

**Live URL**: `https://sspengmock-e6ghe2fthbdqhaeb.uksouth-01.azurewebsites.net/api/MockApiFunction`

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

### 🔍 Web Interface

#### Interactive Dashboard
```
GET /api/inspect/{path}
```
**Features**:
- 🎨 **Beeceptor-style UI** with professional design
- 🏢 **Logo integration** with branded header
- 📊 **Live statistics** showing request counts and system status  
- 🔄 **Auto-refresh** with 2-second intervals and pause control
- 📱 **Responsive design** optimized for all devices
- 🗂️ **Collapsible cards** with persistent expand/collapse state
- 🗑️ **Clear all button** with confirmation and visual feedback

**Live Dashboard**: https://sspengmock-e6ghe2fthbdqhaeb.uksouth-01.azurewebsites.net/api/inspect/MockApiFunction

#### JSON API Access
```
GET /api/inspect/{path}?format=json
```
Programmatic access to captured request data.

#### Clear Requests
```
POST /api/clear/{path}
```
Manually clear all requests for a specific endpoint.

#### System Health
```
GET /api/health
```
System status, storage connectivity, and instance information.

#### Logo Serving
```
GET /api/logo.png
```
Serves the integrated logo for the web interface.

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

## 🎨 Professional Interface Features

### 📊 **Modern Dashboard Design**
- **Clean navbar** with logo and brand identity
- **Statistics bar** showing total requests, active endpoints, instance ID, and storage status
- **Professional color scheme** with subtle shadows and modern typography
- **Responsive grid layout** that adapts to any screen size

### 🔧 **Interactive Controls**
- **Auto-refresh toggle**: 🔄 Active (2s refresh) ↔ ⏸️ Paused
- **Clear all button**: 🗑️ One-click clearing with confirmation dialog
- **Visual feedback**: Loading states, success confirmations, error handling
- **State persistence**: Remembers expanded cards across page refreshes

### 📋 **Request Cards**
- **HTTP method badges**: Color-coded (GET=green, POST=blue, PUT=orange, DELETE=red)
- **Collapsible design**: Click headers to expand/collapse details
- **Formatted timestamps**: Clean time display (HH:MM:SS)
- **Instance tracking**: Shows which function instance processed each request

### 💎 **Data Presentation**
- **Beautiful JSON formatting**: 4-space indentation with proper line breaks
- **Syntax highlighting**: Clear visual distinction for different data types
- **Organized sections**: Query Parameters, Request Headers, Request Body
- **Empty state handling**: Friendly messages when no data is available

### 🔄 **Smart Data Management**
- **Automatic cleanup**: Removes requests older than 1 hour
- **Azure Storage persistence**: Data survives function restarts and deployments  
- **Cross-instance sharing**: Multiple function instances share the same data
- **Real-time updates**: Fresh data loaded on every page refresh

## 🔧 Configuration & Setup

### 🚀 **Quick Local Setup**

1. **Clone the repository**:
   ```bash
   git clone https://github.com/niven01/sspengMock.git
   cd sspengMock
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure local settings** (`local.settings.json`):
   ```json
   {
     "IsEncrypted": false,
     "Values": {
       "AzureWebJobsStorage": "UseDevelopmentStorage=true",
       "FUNCTIONS_WORKER_RUNTIME": "python"
     }
   }
   ```

4. **Start locally**:
   ```bash
   func start
   ```

5. **Access your local instance**:
   - API: `http://localhost:7071/api/MockApiFunction`
   - Dashboard: `http://localhost:7071/api/inspect/MockApiFunction`

### ☁️ **Azure Storage Configuration**

For production deployment, configure Azure Blob Storage:

```json
{
  "Values": {
    "AzureWebJobsStorage": "DefaultEndpointsProtocol=https;AccountName=yourstorageaccount;AccountKey=yourkey;EndpointSuffix=core.windows.net"
  }
}
```

**Storage Features**:
- 🗂️ **Container**: `mock-api-data`
- 📄 **Blob**: `request-log.json`  
- 🔄 **Auto-cleanup**: Requests older than 1 hour removed
- 🌍 **Multi-instance**: Shared across all function instances

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

### 🌍 **Azure Functions Deployment**

#### **Method 1: Azure Functions Core Tools**
```bash
# Deploy directly from local machine
func azure functionapp publish sspengMock --python
```

#### **Method 2: GitHub Actions CI/CD**
The repository includes automated deployment via GitHub Actions:

```yaml
# .github/workflows/main_sspengmock.yml
name: Build and deploy Python project to Azure Function App

on:
  push:
    branches: [ main ]
  workflow_dispatch:

env:
  PYTHON_VERSION: "3.13"
```

**Features**:
- ✅ **Automatic deployment** on push to main branch
- ✅ **Manual deployment** via workflow dispatch
- ✅ **Logo inclusion** in deployment package
- ✅ **Environment-specific** Python version handling

#### **Method 3: Azure CLI**
```bash
# Create Function App
az functionapp create \
  --resource-group myResourceGroup \
  --consumption-plan-location uksouth \
  --name sspengMock \
  --storage-account mystorageaccount \
  --runtime python \
  --runtime-version 3.13

# Deploy code
func azure functionapp publish sspengMock
```

### 🌐 **Production URLs**
After deployment, your API will be available at:
- **Mock API**: `https://yourapp.azurewebsites.net/api/MockApiFunction`
- **Dashboard**: `https://yourapp.azurewebsites.net/api/inspect/MockApiFunction`
- **Health Check**: `https://yourapp.azurewebsites.net/api/health`

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

## 🛠️ Development & Contributing

### 📁 **Project Structure**
```
sspengMock/
├── function_app.py              # Main Azure Functions application
├── host.json                   # Azure Functions runtime configuration  
├── requirements.txt            # Python dependencies (azure-functions, azure-storage-blob)
├── logo.png                    # Logo asset for web interface
├── local.settings.json         # Local development settings
├── .github/workflows/          # GitHub Actions CI/CD pipeline
│   └── main_sspengmock.yml    # Automated deployment configuration
└── README.md                   # This documentation
```

### 🔧 **Adding New Features**

1. **New Mock Endpoints**: Add routes in `function_app.py`
2. **UI Enhancements**: Update HTML template in `inspect_endpoint` function  
3. **Storage Extensions**: Modify Azure Blob Storage structure
4. **Auto-cleanup Logic**: Adjust `cleanup_old_requests()` function

### 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes with proper logging
4. Test locally with `func start`
5. Submit a pull request with clear description

## 🆘 Troubleshooting

### 🔧 **Common Issues**

**Function not starting locally**:
```bash
# Check Python version (3.12+ recommended)
python --version

# Verify dependencies
pip install -r requirements.txt

# Check function configuration
func start --verbose
```

**Dashboard not loading requests**:
- ✅ Verify requests are sent to `/api/MockApiFunction`
- ✅ Check browser console for JavaScript errors
- ✅ Ensure auto-refresh is enabled (🔄 green button)
- ✅ Try manual page refresh

**Clear button not working**:
- ✅ Check browser console for fetch errors
- ✅ Verify network connectivity to `/api/clear/{path}`
- ✅ Ensure confirmation dialog is accepted

**Azure Storage errors**:
```bash
# Check storage configuration
curl https://yourapp.azurewebsites.net/api/health

# Verify connection string in Application Settings
az functionapp config appsettings list --name sspengMock --resource-group myResourceGroup
```

### 📊 **Debugging Features**

The interface includes comprehensive logging:
- 🖥️ **Browser Console**: JavaScript execution logs
- ☁️ **Azure Logs**: Function execution traces
- 🩺 **Health Endpoint**: System status and connectivity tests
- 📱 **Visual Feedback**: Button states and loading indicators

### 🔗 **Support Resources**

- 📚 [Azure Functions Documentation](https://docs.microsoft.com/azure/azure-functions/)
- 🐍 [Python Azure Functions Guide](https://docs.microsoft.com/azure/azure-functions/functions-reference-python)
- ☁️ [Azure Blob Storage SDK](https://docs.microsoft.com/python/api/azure-storage-blob/)
- 🌐 [GitHub Repository Issues](https://github.com/niven01/sspengMock/issues)

---

## 📄 License

MIT License - feel free to use this project for your API testing and monitoring needs.

## 🏷️ Version

**Current Version**: Professional API Monitor with Beeceptor-style Interface  
**Last Updated**: November 2025  
**Features**: Auto-cleanup, Azure Storage, Professional UI, Logo Integration

---

*Made with 💜 for API developers who need reliable request monitoring and testing tools* 🚀