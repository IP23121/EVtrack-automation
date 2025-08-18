
(INFO: THE DEPLOYMENT AND GOOGLE_APPS_SCRIPT FOLDER ARE NOT FUNCTIONAL YET. (work in progress))

# EVTrack Automation API

A FastAPI application that automates EVTrack visitor management through Google Workspace integration. Build Google Sheets workflows that automatically create visitors, add vehicles, generate badges, and process photos from Google Drive.

## 🎯 Project Overview

**What it does:**
- Automates EVTrack visitor management tasks
- Integrates with Google Sheets for bulk visitor processing
- Processes visitor photos from Google Drive
- Provides API endpoints for programmatic access
- Includes complete Google Apps Script integration

**Current Status:**
- ✅ FastAPI server with Swagger UI documentation
- ✅ Google Apps Script integration (5 complete files)
- ✅ Local development environment configured
- ⏳ Ready for AWS Lambda deployment

## 🚀 Quick Start

### Local Development
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the API server
python run.py

# 3. Access the API
# - API: http://localhost:3000
# - Swagger UI: http://localhost:3000/docs
# - Health check: http://localhost:3000/health
```

### Test the API
```bash
curl -H "X-API-Key: evtrack" http://localhost:3000/health
```


## 🔧 Configuration

### Environment Variables (`.env`)
```properties
# EVTrack Credentials (Required)
EVTRACK_EMAIL=joshk@moshava.org
EVTRACK_PASSWORD=Moshava25!

# API Security (Required)
API_KEYS=evtrack

# Application Settings
HEADLESS_MODE=false - FOR NOW(Will be changed to "true" when project is finished)
STAGE=dev
```

### Google Apps Script Setup
1. Go to [script.google.com](https://script.google.com)
2. Create new project
3. Copy files from `google_apps_script/` directory
4. Update API_BASE_URL to your deployed URL

## 📊 API Endpoints

### Core Endpoints
- `GET /health` - API health check
- `GET /docs` - Interactive Swagger UI documentation

### Visitor Management
- `POST /visitors` - Create new visitor
- `POST /visitors/search` - Search existing visitors
- `POST /visitors/update` - Update visitor information
- `GET /visitors/profile` - Get detailed visitor profile

### Vehicle Management
- `POST /vehicles/add` - Add vehicle to visitor
- `POST /vehicles/update` - Update vehicle information

### Automation Features
- `POST /visitors/invite` - Send visitor invitation
- `POST /visitors/badge` - Generate visitor badge
- `POST /credentials/add` - Add access credentials

### Google Workspace Integration
- `POST /sheets/visitors/create` - Bulk create visitors from Google Sheets
- `POST /sheets/visitors/update` - Bulk update visitors from Google Sheets
- `POST /drive/photos/process` - Process visitor photos from Google Drive

**Authentication:** Include `X-API-Key: evtrack` header in all requests.

## 🔗 Google Apps Script Integration

Complete Google Workspace automation with 5 JavaScript files:

### Core Functions
```javascript
// Create visitors from current Google Sheet
createVisitorsFromCurrentSheet()

// Update visitors with new data
updateVisitorsFromCurrentSheet()

// Process photos from Google Drive
processVisitorPhotosFromDrive(driveUrls, visitorEmail)

// Generate visitor badges
generateVisitorBadge(visitorEmail)
```

### Example Workflow
```javascript
function weeklyVisitorProcessing() {
  // 1. Get data from Google Sheet
  const sheet = SpreadsheetApp.getActiveSheet();
  const data = sheet.getDataRange().getValues();
  
  // 2. Create visitors in EVTrack
  const result = processVisitorsFromSheet(data);
  
  // 3. Process photos from Drive (if photo_url column exists)
  if (hasPhotoColumn(data)) {
    batchProcessDriveFiles(data, 'photo_url', 'email');
  }
  
  console.log(`Processed ${result.successCount} visitors`);
}
```

## 🌐 Deployment

### AWS Lambda (Production)
Ready for deployment with Anthony's help:
- Serverless configuration: `deployment/aws-lambda/serverless.yml`
- Lambda handler: `deployment/aws-lambda/lambda_handler.py`
- All dependencies configured for Lambda environment

### Environment Variables for AWS
```
EVTRACK_EMAIL=joshk@moshava.org
EVTRACK_PASSWORD=Moshava25!
API_KEYS=evtrack
HEADLESS_MODE=true
STAGE=dev
```

## 🧪 Testing

### API Testing
```bash
# Health check
curl -H "X-API-Key: evtrack" http://localhost:3000/health

# Create visitor
curl -X POST -H "X-API-Key: evtrack" -H "Content-Type: application/json" \
  -d '{"first_name":"John","last_name":"Doe","email":"john@example.com"}' \
  http://localhost:3000/visitors
```

### Google Apps Script Testing
```javascript
// Test basic API connection
testBasicFunctions();

// Test with sample data
createSampleVisitorSheet();
```

## 📚 Documentation

- **Swagger UI**: Available at `/docs` when server is running
- **Google Apps Script Guide**: See `google_apps_script/README.md`
- **API Reference**: Auto-generated from FastAPI schema

## 🔐 Security

- API key authentication (`evtrack`)
- Environment variable configuration
- No hardcoded credentials
- Ready for AWS Cognito integration (future enhancement)

## 🛠 Development

### Adding New Endpoints
1. Add route to `api/main.py`
2. Create automation function in `automation/`
3. Add data models to `models/`
4. Update Google Apps Script wrapper

### Local Development
```bash
# Install in development mode
pip install -r requirements.txt

# Run with auto-reload
python run.py

# Access development tools
# - API: http://localhost:3000
# - Docs: http://localhost:3000/docs
# - Redoc: http://localhost:3000/redoc
```

## 🆘 Support

**For Google Apps Script issues:**
1. Check `google_apps_script/README.md`
2. Run `testBasicFunctions()` to verify setup
3. Ensure API is running locally

**For API issues:**
1. Check server logs
2. Verify environment variables in `.env`
3. Test endpoints via Swagger UI at `/docs`

---

Ready for deployment with AWS Lambda! 