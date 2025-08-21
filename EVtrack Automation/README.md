# EVTrack Automation API

## What This Program Does

EVTrack is a visitor management system used by organizations to track people entering their facilities. This program automates the manual work of managing visitors in EVTrack by providing a REST API that can perform all visitor operations automatically through web browser automation.

Instead of manually logging into EVTrack's website and clicking through forms to add visitors, update information, or generate badges, this program does it all programmatically. It can handle individual operations through API calls or process hundreds of visitors at once through Google Sheets integration.

The system uses browser automation to interact with EVTrack's web interface just like a human would, but much faster and without errors. It can create visitors, add their vehicles, assign access credentials, send invitations, and generate ID badges - all through simple HTTP requests.

## 1. Setup and Running

### Prerequisites
Before you can run this program, you need:

- Python 3.13 or newer installed on your computer
- Google Chrome browser installed
- An EVTrack account with login credentials
- Internet connection

### Step-by-Step Setup

**Step 1: Install Dependencies**
```bash
pip install -r requirements.txt
```

**Step 2: Configure Your Credentials**
```bash
# Copy the example environment file
cp .env.example .env
```

Edit the `.env` file with your actual EVTrack credentials:
```bash
# Replace with your actual EVTrack login details
EVTRACK_EMAIL=your-email@example.com
EVTRACK_PASSWORD=your-password

# Leave these as-is for local development
API_KEYS=evtrack
HEADLESS_MODE=false
STAGE=dev
```

**Step 3: Start the Program**
```bash
python run.py
```

**Step 4: Access the Interface**
Open your web browser and go to: `http://localhost:3000/docs`

**Step 5: Authenticate**
1. Click the green "Authorize" button at the top of the page
2. Enter the API key: `evtrack`
3. Click "Authorize"

You will now see a web interface (called Swagger UI) that lists all available actions you can perform.

### Understanding the Interface

The Swagger UI shows you all available operations organized into sections. Each operation has:
- A title describing what it does
- Input fields for the information it needs
- An "Execute" button to run the operation
- A response section that shows results

How to Use Any Action:
- Find the action you want in the list (for example, "Add Visitor")
- Click the "Try it out" button on the right (may appear; if not, proceed)
- Fill out the form that appears with your information
- Click "Execute" to run the action
- See the results in the response section below

How to Understand the UI:
- Required fields are marked with red asterisks (*)
- Optional fields can be left empty if you don't need them
- File uploads use "Choose File" buttons for photos
- Results appear in the "Response" section after clicking Execute

Actions: The system can perform 9 main actions

Step-by-Step Action Guide

1. Get Visitors Summary
What it does: Finds visitors by name, phone, or email and shows you their complete information.

How to use in Swagger UI:
- Go to `GET /visitors`
- Click "Try it out" if needed
- In the "search" box, enter a name, phone, or email
- Click "Execute"
- View the visitor's information in the response below

What happens behind the scenes:
- The program logs into EVTrack, searches the visitor database, finds matching visitors, opens their profiles, extracts information, and returns it.

2. Add Visitor
What it does: Creates a brand new visitor in the EVTrack system with all their details and photos.

How to use in Swagger UI:
- Go to `POST /visitors`
- Click "Try it out" if needed
- Fill out required fields: first_name, last_name, mobile_number
- Optionally fill in: company, email, address, etc.
- Optionally upload a photo using "Choose file" (max 10MB)
- Click "Execute"

What happens behind the scenes:
- The program opens EVTrack, navigates to Add Visitor, fills the form, uploads the photo, submits, and returns the new visitor ID.

3. Update Visitor - Change Existing Information
What it does: Finds an existing visitor and changes only the information you specify.

How to use in Swagger UI:
- Go to `POST /visitors/update`
- Click "Try it out" if needed
- Enter search term (current name or phone of the visitor)
- Fill out only the fields you want to change
- Click "Execute"

What happens behind the scenes:
- The program finds the visitor, opens their profile, edits the specified fields, saves changes, and confirms the update.

4. Add Vehicle to Visitor
What it does: Adds a vehicle to a visitor's profile so they can bring it on-site.

How to use in Swagger UI:
- Go to `POST /vehicles/add`
- Click "Try it out" if needed
- Enter visitor search criteria (name or phone)
- Fill vehicle details (license plate OR VIN required)
- Click "Execute"

What happens behind the scenes:
- The program finds the visitor, opens their vehicle section, fills vehicle details, saves, and confirms.

5. Update Vehicle for Visitor
What it does: Modifies existing vehicle information.

How to use in Swagger UI:
- Go to `POST /vehicles/update`
- Click "Try it out" if needed
- Enter vehicle search criteria (license plate or VIN)
- Fill in only the fields to change
- Click "Execute"

What happens behind the scenes:
- The program locates the vehicle, edits the details, saves, and confirms.

6. Add Credentials to Visitor
What it does: Assigns access devices like RFID cards or codes to a visitor.

How to use in Swagger UI:
- Go to `POST /credentials/add`
- Click "Try it out" if needed
- Enter visitor search criteria (name or phone)
- Fill credential details (reader_type, card_number)
- Click "Execute"

What happens behind the scenes:
- The program finds the visitor, navigates to credentials, adds the device, and confirms assignment.

7. Update Credentials for Visitor
What it does: Changes existing credential information.

How to use in Swagger UI:
- Go to `POST /credentials/update`
- Click "Try it out" if needed
- Enter visitor search criteria (name or phone)
- Enter credential identifier (card number or credential ID)
- Fill fields to change
- Click "Execute"

What happens behind the scenes:
- The program finds the credential, updates fields, saves, and confirms.

8. Invite Visitor
What it does: Sends a digital invitation with QR codes or access information for a specific visit.

How to use in Swagger UI:
- Go to `POST /visitors/invite`
- Click "Try it out" if needed
- Enter visitor search criteria (name or phone)
- Fill invitation details (location, credential_type, dates/times)
- Click "Execute"

What happens behind the scenes:
- The program creates the invitation in EVTrack, generates codes/QR, sends notification, and returns confirmation.

9. Get Visitor Badge
What it does: Creates a downloadable ID badge (PDF) with the visitor's photo and information.

How to use in Swagger UI:
- Go to `POST /visitors/badge`
- Click "Try it out" if needed
- Enter visitor search criteria (name, phone, or email)
- Click "Execute"
- Download the badge file from the response

What happens behind the scenes:
- The program generates the badge in EVTrack, formats it as PDF, and returns the file.

## 3. How Each Operation Works (The Process)

### The Browser Automation Process

All operations follow a similar pattern using browser automation:

1. **Initialize Browser:** The system starts a Chrome browser instance (visible or headless depending on configuration)
2. **Navigate to EVTrack:** Opens the EVTrack web application
3. **Authenticate:** Logs in using the credentials from your .env file
4. **Navigate to Appropriate Section:** Goes to the correct page (visitors, vehicles, credentials, etc.)
5. **Perform Action:** Fills in forms, uploads files, clicks buttons, etc.
6. **Extract Results:** Captures success messages, error messages, or data
7. **Clean Up:** Closes browser and returns results

### Detailed Process for Each Operation

**Search Process:**
1. Navigate to EVTrack visitor search page
2. Enter search term in the search field
3. Submit search and wait for results
4. Extract visitor information from search results
5. If multiple matches found, return all matches
6. If single match found, open full profile and extract detailed information

**Create Visitor Process:**
1. Navigate to "Add New Visitor" page
2. Fill in personal information fields (name, phone, email, etc.)
3. Upload photo if provided (handles file upload)
4. Set any additional options or flags
5. Submit the form
6. Wait for confirmation page and extract visitor ID
7. Handle any validation errors and retry if needed

**Update Visitor Process:**
1. First search for the visitor using provided criteria
2. Open the visitor's profile page
3. Click "Edit" or similar action
4. Update only the fields that were provided in the request
5. Keep existing values for fields not being updated
6. Submit changes
7. Confirm update was successful

**Vehicle Operations Process:**
1. Find the visitor (search process)
2. Navigate to vehicle section of their profile
3. For adding: Click "Add Vehicle" and fill in vehicle form
4. For updating: Find specific vehicle by license/VIN, then edit
5. Handle file uploads if vehicle photos are provided
6. Submit vehicle information
7. Confirm vehicle was saved to profile

**Credentials Process:**
1. Find the visitor (search process)
2. Navigate to credentials/access section
3. For adding: Click "Add Credential" and fill in credential form
4. For updating: Find specific credential and edit details
5. Set access levels, expiry dates, PINs as specified
6. Submit credential information
7. Confirm credential was assigned

**Invitation Process:**
1. Find the visitor (search process)
2. Navigate to invitation section
3. Fill in invitation details (location, dates, access type)
4. Generate invitation with QR codes or access codes
5. Send invitation (email/SMS based on visitor's contact info)
6. Confirm invitation was created and sent

**Badge Generation Process:**
1. Find the visitor (search process)
2. Navigate to badge generation section
3. Select badge template and format
4. Include visitor photo and information
5. Generate PDF badge file
6. Return downloadable badge file

### Error Handling and Retries

Each operation includes error handling:

- **Login Failures:** Automatically retry authentication if session expires
- **Page Load Issues:** Wait for elements to load, retry if pages don't respond
- **Form Validation Errors:** Capture error messages and return meaningful feedback
- **Network Issues:** Retry requests that fail due to connectivity
- **Element Not Found:** Wait for dynamic content to load before proceeding
- **File Upload Problems:** Validate file sizes and formats before uploading

### Performance Optimization

- **Session Reuse:** Maintains login session across multiple operations
- **Smart Waiting:** Uses intelligent waits instead of fixed delays
- **Parallel Processing:** Can handle multiple requests simultaneously
- **Caching:** Stores frequently accessed data to reduce redundant operations
- **Resource Management:** Properly closes browsers and cleans up resources

## 4. Integration

### Google Sheets Integration

The system integrates with Google Sheets to enable bulk processing of visitor data:

**Google Apps Script Client:**
- Connects to the EVTrack API from Google Sheets
- Processes rows of visitor data in bulk
- Updates sheets with processing status and results
- Handles photo uploads from Google Drive links

**Typical Integration Workflow:**
1. Create a Google Sheet with visitor information columns
2. Add photo links from Google Drive
3. Run the Google Apps Script menu function
4. Monitor progress as each row is processed
5. Review results and error messages in the sheet

**Bulk Operations Supported:**
- Create multiple visitors from sheet data
- Add vehicles for multiple visitors
- Assign credentials in bulk
- Generate badges for entire groups
- Process photos from Google Drive folders

### REST API Integration

The system provides a complete REST API that can be integrated with other systems:

**API Features:**
- Standard HTTP methods (GET, POST, PUT, DELETE)
- JSON request and response format
- OpenAPI/Swagger documentation
- Authentication via API keys
- Error handling with meaningful status codes
- File upload support for photos and documents

**Integration Examples:**

**JavaScript Integration:**
```javascript
// Example: Create a visitor from a web form
const response = await fetch('http://localhost:3000/visitors', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'evtrack'
  },
  body: JSON.stringify({
    first_name: 'John',
    last_name: 'Doe',
    mobile_number: '555-1234',
    email: 'john@example.com'
  })
});
```

**Python Integration:**
```python
import requests

# Example: Search for a visitor
response = requests.get(
    'http://localhost:3000/visitors?search=john doe',
    headers={'X-API-Key': 'evtrack'}
)
visitor_data = response.json()
```

**cURL Integration:**
```bash
# Example: Add a vehicle
curl -X POST "http://localhost:3000/vehicles/add" \
  -H "X-API-Key: evtrack" \
  -H "Content-Type: application/json" \
  -d '{
    "visitor_search": "John Doe",
    "license_plate": "ABC123",
    "make": "Toyota",
    "model": "Camry"
  }'
```

### Production Deployment Integration

**AWS Lambda Deployment:**
The system can be deployed to AWS Lambda for production use

**Deployment Process:**
1. Configure AWS credentials and permissions
2. Set up environment variables in AWS
3. Deploy using Serverless Framework
4. Configure API Gateway with custom domain
5. Set up Cognito user pools for authentication
6. Update Google Apps Script with production URLs

**Security Features:**
- API key authentication for development
- JWT token authentication for production
- CORS configuration for web integration
- Rate limiting and throttling
- Encrypted environment variables
- IAM roles with minimal permissions

**Monitoring and Logging:**
- All API requests logged to CloudWatch
- Error tracking and alerting
- Performance metrics and dashboards
- Usage analytics and reporting
- Health checks and uptime monitoring

### Integration Architecture

The system follows a modular architecture that supports various integration patterns:

**Core Components:**
- **API Layer:** FastAPI application with Swagger documentation
- **Automation Layer:** Selenium-based browser automation
- **Integration Layer:** Google Apps Script and external API connectors
- **Deployment Layer:** AWS Lambda and serverless infrastructure

**Data Flow:**
1. **Requests** come in via HTTP API calls
2. **Authentication** validates API keys or JWT tokens
3. **Processing** routes requests to appropriate automation modules
4. **Browser Automation** performs actions in EVTrack web interface
5. **Results** are captured and formatted as JSON responses
6. **Integration** systems receive structured data for further processing

This architecture enables the system to be used standalone via the Swagger UI, integrated into Google Sheets workflows, or embedded into larger applications via the REST API.
