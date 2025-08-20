# EVTrack Automation API

## 🎯 Primary Goal

**API-driven automation for bulk seasonal visitor pre-registration with image/metadata uploads through Google Sheets integration.**

This system provides a comprehensive REST API that enables automated visitor management for the EVTrack security system, specifically designed for seasonal bulk operations through Google Workspace integration.

## 🚀 Quick Start

### For API Development/Testing (Local)
```bash
python run.py
# Visit: http://localhost:3000/docs
# API Key: evtrack
```

### For Production Use (AWS Lambda)
See [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for complete AWS deployment instructions.

## 📊 Core Features

### 🔗 REST API (Primary Focus)
- **9 endpoints** for complete visitor/vehicle/credential management
- **FastAPI with Swagger UI** for testing and documentation
- **Authentication via API keys** for secure access
- **JSON responses** for easy integration

### 📋 Google Sheets Integration
- **Bulk visitor creation** from spreadsheet data
- **Photo processing** from Google Drive links
- **Status tracking** and error reporting in sheets
- **Menu system** for non-technical users

### 🖼️ Photo & Document Management
- **Google Drive integration** for photo uploads
- **Batch processing** of visitor photos
- **Automatic metadata** extraction and validation

### 🔐 Security & Authentication
- **AWS Cognito** integration for production
- **API key authentication** for development
- **Secure credential** management

## 🛠️ How to Use the Swagger UI Interface

All actions are done through a web-based interface called "Swagger UI".

### Getting Started:
1. Start the program by running "python run.py" in your terminal
2. Open your web browser and go to: http://localhost:3000/docs
3. You'll see a webpage with sections for each action you can perform
4. **You must authenticate first:**
   - Click the green "Authorize" button at the top (or the Lock emoji at any action)
   - Enter the API key: `evtrack`
   - Click "Authorize"

### How to Use Any Action:
1. Find the action you want in the list (e.g., "Add Visitor")
2. Click "Try it out" button on the right (may appear automatically)
3. Fill out the form that appears with your information
4. Click "Execute" to run the action
5. See the results in the response section below

### How to Understand the UI:
- **Required fields** are marked with red asterisks (*)
- **Optional fields** can be left empty if you don't need them
- **File uploads** use "Choose File" buttons for photos (max 10MB)
- **Results** appear in the "Response" section after clicking Execute

## 📋 API Endpoints & Detailed Usage

| Endpoint | Method | Purpose |
|----------|---------|---------|
| `/visitors/search` | POST | Search for existing visitors |
| `/visitors/create` | POST | Create new visitor |
| `/visitors/update` | POST | Update visitor information |
| `/visitors/profile` | POST | Get detailed visitor profile |
| `/vehicles/add` | POST | Add vehicle to visitor |
| `/vehicles/update` | POST | Update vehicle information |
| `/credentials/add` | POST | Add access credentials |
| `/visitors/invite` | POST | Send visitor invitation |
| `/visitors/badge` | POST | Generate visitor badge |

### 1. Get Visitors Summary (Search)
**What it does:** Finds visitors by name, phone, or email and shows you their complete information.

**How to use in Swagger UI:**
1. Go to `GET /visitors/search` section
2. Click "Try it out" (if needed)
3. In the "search" box, enter: Name or Phone number
4. Click "Execute"
5. View the visitor's information in the response below

**What happens behind the scenes:**
The program logs into EvTrack → searches the visitor database → finds matching visitors → opens their profiles → extracts all their information → displays it for you.

### 2. Add Visitor
**What it does:** Creates a brand new visitor in the EvTrack system with all their details and photos.

**How to use in Swagger UI:**
1. Go to `POST /visitors` section
2. Click "Try it out" (if needed)
3. Fill out the form:
   - **Must fill:** First Name, Last Name, Mobile Number
   - **Optional:** Company, Email, Address, etc.
   - **Photo:** Click "Choose File" to upload (max 10MB)
4. Click "Execute"
5. Check that the visitor was created successfully

**What happens behind the scenes:**
The program opens EvTrack → goes to "Add Visitor" page → fills in all your information in the correct boxes → uploads the photo → saves the new visitor.

### 3. Update Visitor - Change Existing Information
**What it does:** Finds an existing visitor and changes only the information you specify. You don't need to re-enter everything. Just enter what you want to change.

**How to use in Swagger UI:**
1. Go to `POST /visitors/update` section
2. Click "Try it out" (if needed)
3. Enter search term (current name or phone of the visitor)
4. Fill out ONLY the fields you want to change:
   - Leave unchanged fields empty
5. Click "Execute"

**What happens behind the scenes:**
The program finds the visitor → opens their profile → goes to edit mode → changes only the fields you provided → keeps everything else the same → saves the updates.

### 4. Add Vehicle to Visitor
**What it does:** Adds a car, truck, or other vehicle to a visitor's profile so they can bring it on-site.

**How to use in Swagger UI:**
1. Go to `POST /vehicles/add` section
2. Click "Try it out" (if needed)
3. Enter search term (visitor's name or phone)
4. Fill vehicle details:
   - **Must have:** Either License Plate OR VIN number
   - **Optional:** Make, Model, Color, Year etc.
5. Click "Execute"

**What happens behind the scenes:**
The program finds the visitor → opens their profile → goes to "Add Vehicle" section → enters all the vehicle information → saves it to their profile.

### 5. Update Vehicle for Visitor
**What it does:** Changes existing vehicle information by finding the vehicle with its license plate or VIN.

**How to use in Swagger UI:**
1. Go to `POST /vehicles/update` section
2. Click "Try it out" (if needed)
3. Enter search term (license plate or VIN of the vehicle)
4. Fill out only the vehicle details you want to change
5. Click "Execute"

**What happens behind the scenes:**
The program goes to the vehicle management section → searches for the specific vehicle → finds it → updates the information you provided → saves changes.

### 6. Add Credentials to Visitor
**What it does:** Adds access credentials like RFID cards, key fobs, or access codes to a visitor's profile.

**How to use in Swagger UI:**
1. Go to `POST /credentials/add` section
2. Click "Try it out" (if needed)
3. Enter search term (visitor's name or phone)
4. Fill credential details:
   - **Must have:** Reader Type (like "RFID Card"), Card Number
   - **Optional:** PIN, expiry dates, usage limits etc.
5. Click "Execute"

**What happens behind the scenes:**
The program finds the visitor → opens their profile → goes to "Credentials" tab → clicks "Add" → fills in the credential information → saves the new access device.

### 7. Update Credentials for Visitor
**What it does:** Changes existing credential information like expiry dates, PINs, or card status.

**How to use in Swagger UI:**
1. Go to `POST /credentials/update` section
2. Click "Try it out" (if needed)
3. Enter search term (visitor's name or phone)
4. Enter credential search detail (card number or ID of the credential)
5. Fill out only the credential fields you want to change
6. Click "Execute"

**What happens behind the scenes:**
The program finds the visitor → goes to their credentials → finds the specific card/device → updates the information you provided → saves changes.

### 8. Invite Visitor
**What it does:** Sends a digital invitation to a visitor with QR codes or access codes for a specific time and location.

**How to use in Swagger UI:**
1. Go to `POST /visitors/invite` section
2. Click "Try it out" (if needed)
3. Enter search term (visitor's name or phone)
4. Fill invitation details:
   - **Must have:** Location, Credential Type (like "QR Code")
   - **Optional:** Visit reason, specific dates and times
5. Click "Execute"

**What happens behind the scenes:**
The program finds the visitor → opens their profile → goes to "Invite" section → fills in all the invitation details → generates the digital invitation with access codes.

### 9. Get Visitor Badge
**What it does:** Creates a downloadable ID badge (PDF) with the visitor's photo and information for printing.

**How to use in Swagger UI:**
1. Go to `POST /visitors/badge` section
2. Click "Try it out" (if needed)
3. Enter search (visitor's name, phone, or email)
4. Click "Execute"
5. Download the badge file from the response

**What happens behind the scenes:**
The program finds the visitor → gets their photo and information → creates a formatted ID badge → provides it as a downloadable file.

## 📁 Project Structure

```
EVtrack Automation/
├── api/                    # FastAPI application
│   ├── main.py            # Main API endpoints
│   └── openapi.yaml       # API documentation
├── automation/            # Core automation logic
│   ├── visitors.py        # Visitor management
│   ├── vehicles.py        # Vehicle operations
│   ├── credentials.py     # Credential management
│   └── badges.py          # Badge generation
├── google_apps_script/    # Google Workspace integration
│   ├── authentication.js  # API connection handling
│   ├── evtrack_api.js     # API wrapper functions
│   ├── sheets_integration.js # Bulk sheet processing
│   ├── drive_integration.js  # Photo/file handling
│   └── main_workflows.js  # User workflow orchestration
├── deployment/            # AWS Lambda deployment
│   ├── aws-lambda/        # Serverless configuration
│   └── scripts/           # Deployment automation
└── utils/                 # Shared utilities
    └── selenium_utils.py  # Browser automation
```

## 🔧 Setup and Requirements

### What you need:
- Python 3.13 or newer
- Chrome web browser
- Internet connection
- EvTrack account login details
- Google account (for Sheets integration)
- AWS account (for production deployment)

### First-time setup:
1. Install required programs: `pip install -r requirements.txt`
2. Set up your login details in a .env file
3. Start the program: `python run.py`
4. Open your browser to: http://localhost:3000/docs

### Authentication:
1. Click the green "Authorize" button in Swagger UI
2. Enter API key: `evtrack`
3. Click "Authorize" to unlock all features

## 📊 Google Sheets Integration

### What it does:
Connects your Google Sheets directly to EvTrack, allowing you to manage visitors from spreadsheets with automatic photo uploads from Google Drive.

### How Google Sheets Integration Works:
1. Create a Google Sheet with visitor data
2. Store photos in Google Drive and reference them in your sheet
3. Run the Google Apps Script to automatically execute any of the 9 actions in EvTrack

### Setup Process
1. **Deploy API to AWS Lambda** (see DEPLOYMENT_CHECKLIST.md)
2. **Create Google Apps Script project**
3. **Copy integration files** from `google_apps_script/` directory
4. **Configure API connection** with your Lambda URL
5. **Test bulk operations** with sample data

### Sheet Format
Your Google Sheet should include these columns:

| first_name | last_name | email | mobile | company | purpose | visit_date |
|------------|-----------|-------|---------|---------|---------|------------|
| John | Smith | john@example.com | +1-555-0101 | Tech Corp | Meeting | 2025-01-20 |

### Optional Columns
- `license_plate`, `vehicle_make`, `vehicle_model`, `vehicle_color`
- `notes`, `photo_url` (Google Drive link)

### Bulk Operations
- **Process New Visitors**: Create multiple visitors from sheet data
- **Update Existing Visitors**: Bulk update visitor information
- **Process Drive Photos**: Batch photo uploads from Google Drive links

### Google Apps Script Setup Requirements:
- Google Workspace account
- EvTrack Automation API running
- Google Apps Script project
- API authentication token

### For Photos (Add/Update Visitors):
The script will download the photo from Google Drive and send the data to the EvTrack API to create or update the visitor record.

## 🚀 Production Deployment

### AWS Lambda Deployment
**What it does:**
Hosts the EvTrack API in the cloud for 24/7 availability, scalability, and integration with Google Sheets. Lambda includes serverless functions that handle API requests.

**Deployment Features:**
- Chrome browser automation in a headless Lambda environment
- File upload handling for photos and documents
- Environment variable management for credentials
- CloudWatch logging for monitoring and debugging
- API Gateway integration for HTTP endpoints

### Deployment Process:
1. **Configure AWS credentials**
2. **Set environment variables** (EVTrack login, API keys)
3. **Run deployment script**: `./deployment/scripts/deploy.sh`
4. **Configure Google Apps Script** with Lambda URL
5. **Test integration** end-to-end

See [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for detailed instructions.

## 🔐 Security & Authentication

### Multi-Layer Security:

**API Key Authentication:**
- Tokens are used for Google Apps Script integration
- Stored securely in Google Apps Script PropertiesService
- Can be rotated as needed

**AWS Cognito Integration:**
- User pools for authentication
- Secure JWT tokens
- Multi-factor authentication support
- Role-based access control

**AWS IAM Protection:**
- Lambda execution roles
- Resource-level permissions
- API Gateway authorization
- CloudWatch access controls

### Authentication Flow:
The request flow works as follows:
**Google Sheets → Apps Script → API Key → Lambda → Cognito → EvTrack API**

## 🎯 Primary Use Cases

### 1. Seasonal Visitor Pre-Registration
```javascript
// Google Apps Script workflow
processVisitorSheet(); // Bulk create from spreadsheet
```

### 2. Photo & Document Processing
```javascript
// Google Apps Script workflow
processPhotosFromDrive(); // Batch process Drive photos
```

### 3. Individual API Operations
```bash
# REST API examples
POST /visitors/create
POST /vehicles/add
POST /visitors/badge
```

## 🔍 API Documentation

### Interactive Documentation
- **Local**: http://localhost:3000/docs
- **Production**: https://your-lambda-url.amazonaws.com/dev/docs

### Key Features
- **Try it out** functionality for all endpoints
- **Request/response examples** for each operation
- **Authentication testing** with API keys
- **Error handling** documentation

## ⚙️ Environment Configuration

### Core Settings (Required):
- **EvTrack login email**: `joshk@moshava.org`
- **EvTrack account password**: `Moshava25!`
- **API key**: `evtrack`
- **Headless mode setting**: Usually set to "true" for automated browser mode

### AWS Settings:
- **Cognito User Pool ID** (auto-generated during deployment)
- **Cognito Client ID** (auto-generated during deployment)

### Google Settings:
- **Google OAuth Client ID**
- **Google Service Account Key** (JSON format)

## 📦 Deployment Files

### Include these folders when deploying:
- `api/`
- `automation/`
- `models/`
- `utils/`
- `deployment/aws-lambda/`

### Do NOT include:
- `.git/`
- `__pycache__/`
- `.env`
- Any files ending in `.pyc`

### Lambda Configuration:
- **Entry point**: `lambda_handler.handler`
- **Runtime environment**: Python 3.13
- **Chrome AWS Lambda layer**: version 32

## 🛠️ Technical Stack

- **Backend**: Python 3.13, FastAPI, Selenium WebDriver
- **Cloud**: AWS Lambda, API Gateway, Cognito
- **Integration**: Google Apps Script, Google Sheets API, Google Drive API
- **Deployment**: Serverless Framework, Docker-based packaging
- **Security**: API key authentication, CORS enabled

## 📋 Integration Workflow

1. **API-First Design**: All functionality accessible via REST endpoints
2. **Google Sheets Automation**: Bulk seasonal registration workflows
3. **Photo Processing**: Google Drive integration for visitor photos
4. **Metadata Management**: Personnel and visitor data handling
5. **Production Ready**: AWS Lambda deployment with authentication

### Typical Seasonal Workflow:
1. **Prepare Google Sheet** with visitor data
2. **Upload photos to Google Drive** and add links to sheet
3. **Run bulk creation** via Google Apps Script menu
4. **Monitor processing** status in sheet
5. **Generate badges** and invitations as needed

### Core Components Working Together:
- **Google Sheets**: Visitor data, photo links, and status tracking
- **Google Drive**: Photo storage, file sharing, and access control
- **AWS Lambda**: API requests, authentication, and file handling
- **AWS Cognito**: User authentication, token management, and role-based control
- **CloudWatch**: Monitoring, logging, and alerting
- **EvTrack**: Web automation, data storage, and badge generation

## 📞 Support & Resources

- **API Documentation**: Available at `/docs` endpoint
- **Deployment Guide**: [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
- **Google Apps Script Guide**: [google_apps_script/README.md](google_apps_script/README.md)
- **Quick Start Guide**: [QUICK_START.md](QUICK_START.md)

---

**🎉 Ready to automate bulk seasonal visitor management with Google Sheets integration!**

## 📁 Project Structure

```
EVtrack Automation/
├── api/                    # FastAPI application
│   ├── main.py            # Main API endpoints
│   └── openapi.yaml       # API documentation
├── automation/            # Core automation logic
│   ├── visitors.py        # Visitor management
│   ├── vehicles.py        # Vehicle operations
│   ├── credentials.py     # Credential management
│   └── badges.py          # Badge generation
├── google_apps_script/    # Google Workspace integration
│   ├── authentication.js  # API connection handling
│   ├── evtrack_api.js     # API wrapper functions
│   ├── sheets_integration.js # Bulk sheet processing
│   ├── drive_integration.js  # Photo/file handling
│   └── main_workflows.js  # User workflow orchestration
├── deployment/            # AWS Lambda deployment
│   ├── aws-lambda/        # Serverless configuration
│   └── scripts/           # Deployment automation
└── utils/                 # Shared utilities
    └── selenium_utils.py  # Browser automation
```

## 🔧 Development Setup

### Prerequisites
- Python 3.13+
- Chrome browser
- Google account (for Sheets integration)
- AWS account (for production deployment)

### Local Development
```bash
# Clone and setup
git clone <repository>
cd "EVtrack Automation"

# Install dependencies
pip install -r requirements.txt

# Run locally
python run.py

# Access API docs
open http://localhost:3000/docs
```

### Authentication
1. Click the green "Authorize" button in Swagger UI
2. Enter API key: `evtrack`
3. Click "Authorize"

## 📊 Google Sheets Integration

### Setup Process
1. **Deploy API to AWS Lambda** (see DEPLOYMENT_CHECKLIST.md)
2. **Create Google Apps Script project**
3. **Copy integration files** from `google_apps_script/` directory
4. **Configure API connection** with your Lambda URL
5. **Test bulk operations** with sample data

### Sheet Format
Your Google Sheet should include these columns:

| first_name | last_name | email | mobile | company | purpose | visit_date |
|------------|-----------|-------|---------|---------|---------|------------|
| John | Smith | john@example.com | +1-555-0101 | Tech Corp | Meeting | 2025-01-20 |

### Optional Columns
- `license_plate`, `vehicle_make`, `vehicle_model`, `vehicle_color`
- `notes`, `photo_url` (Google Drive link)

### Bulk Operations
- **Process New Visitors**: Create multiple visitors from sheet data
- **Update Existing Visitors**: Bulk update visitor information
- **Process Drive Photos**: Batch photo uploads from Google Drive links

## 🎯 Primary Use Cases

### 1. Seasonal Visitor Pre-Registration
```javascript
// Google Apps Script workflow
processVisitorSheet(); // Bulk create from spreadsheet
```

### 2. Photo & Document Processing
```javascript
// Google Apps Script workflow
processPhotosFromDrive(); // Batch process Drive photos
```

### 3. Individual API Operations
```bash
# REST API examples
POST /visitors/create
POST /vehicles/add
POST /visitors/badge
```

## 🚀 Production Deployment

### AWS Lambda Deployment
1. **Configure AWS credentials**
2. **Set environment variables** (EVTrack login, API keys)
3. **Run deployment script**: `./deployment/scripts/deploy.sh`
4. **Configure Google Apps Script** with Lambda URL
5. **Test integration** end-to-end

See [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for detailed instructions.

## 🔍 API Documentation

### Interactive Documentation
- **Local**: http://localhost:3000/docs
- **Production**: https://your-lambda-url.amazonaws.com/dev/docs

### Key Features
- **Try it out** functionality for all endpoints
- **Request/response examples** for each operation
- **Authentication testing** with API keys
- **Error handling** documentation

## 📋 Integration Workflow


1. **API-First Design**: All functionality accessible via REST endpoints
2. **Google Sheets Automation**: Bulk seasonal registration workflows
3. **Photo Processing**: Google Drive integration for visitor photos
4. **Metadata Management**: Personnel and visitor data handling
5. **Production Ready**: AWS Lambda deployment with authentication

### Typical Seasonal Workflow:
1. **Prepare Google Sheet** with visitor data
2. **Upload photos to Google Drive** and add links to sheet
3. **Run bulk creation** via Google Apps Script menu
4. **Monitor processing** status in sheet
5. **Generate badges** and invitations as needed

## 🛠️ Technical Stack

- **Backend**: Python 3.13, FastAPI, Selenium WebDriver
- **Cloud**: AWS Lambda, API Gateway, Cognito
- **Integration**: Google Apps Script, Google Sheets API, Google Drive API
- **Deployment**: Serverless Framework, Docker-based packaging
- **Security**: API key authentication, CORS enabled

## 📞 Support & Resources

- **API Documentation**: Available at `/docs` endpoint
- **Deployment Guide**: [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
- **Google Apps Script Guide**: [google_apps_script/README.md](google_apps_script/README.md)
- **Quick Start Guide**: [QUICK_START.md](QUICK_START.md)

---

**🎉 Ready to automate bulk seasonal visitor management with Google Sheets integration!**
