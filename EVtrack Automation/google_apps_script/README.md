# Google Apps Script Integration for EVTrack API

This directory contains Google Apps Script files that provide a complete integration layer between Google Workspace (Sheets, Drive) and the EVTrack automation API.

## 📁 Files Overview

### Core Integration Files
- **`authentication.js`** - API authentication and request handling
- **`evtrack_api.js`** - Main EVTrack API wrapper functions
- **`sheets_integration.js`** - Google Sheets data processing functions
- **`drive_integration.js`** - Google Drive file handling functions
- **`examples.js`** - Comprehensive usage examples and test functions

## 🚀 Quick Setup

### 1. Create a New Google Apps Script Project
1. Go to [script.google.com](https://script.google.com)
2. Create a new project
3. Replace the default `Code.gs` file content with the files from this directory

### 2. Add All Script Files
Copy and paste each file into your Google Apps Script project:

1. **`authentication.js`** → Replace default `Code.gs` and rename to `authentication.gs`
2. **`evtrack_api.js`** → Create new script file `evtrack_api.gs`
3. **`sheets_integration.js`** → Create new script file `sheets_integration.gs`
4. **`drive_integration.js`** → Create new script file `drive_integration.gs`
5. **`examples.js`** → Create new script file `examples.gs`

### 3. Configure Authentication
In `authentication.js`, update these variables:
```javascript
const CONFIG = {
  API_BASE_URL: 'https://2db811a0e2c19fa6c766a0fec3c063a1.serveo.net',  // Your public tunnel URL
  API_KEY: 'evtrack',  // Your simplified API key
  GOOGLE_OAUTH_CLIENT_ID: 'your-google-client-id.apps.googleusercontent.com'  // For future OAuth setup
};
```

**Note**: 
- Use your actual tunnel URL (from serveo.net or ngrok)
- For production deployment, change to your deployed AWS domain

### 4. Test the Setup
**Before running:** Make sure your API is running locally (`python run.py`)

In the Google Apps Script editor:
1. Select `testBasicFunctions` from the function dropdown
2. Click the ▶️ **Run** button
3. Check the **Execution transcript** for results

```javascript
testBasicFunctions();  // You can also type and run this directly
```

**Expected output:**
```
🧪 Testing basic EVTrack API functions...
✅ API connection successful
✅ EVTrack login successful
✅ Basic function tests completed!
```

## 🛠 Main Functions

### Visitor Management
- `searchVisitors(searchTerm)` - Search for visitors
- `createVisitor(visitorData)` - Create new visitor
- `updateVisitor(searchTerm, updateData)` - Update existing visitor
- `getVisitorProfile(searchTerm)` - Get detailed visitor profile

### Vehicle Management
- `addVehicle(searchTerm, vehicleData)` - Add vehicle to visitor
- `updateVehicle(searchTerm, vehicleData)` - Update vehicle information

### Credentials & Access
- `addCredential(searchTerm, credentialData)` - Add access credential
- `inviteVisitor(searchTerm, invitationData)` - Send visitor invitation

### Badge Generation
- `generateVisitorBadge(searchTerm)` - Generate visitor badge

### Google Sheets Integration
- `processVisitorsFromSheet(sheetData)` - Bulk create visitors from sheet
- `updateVisitorsFromSheet(sheetData, searchColumn)` - Bulk update visitors
- `getVisitorsForSheet(searchTerms)` - Export visitor data to sheet format

### Google Drive Integration
- `processVisitorPhotosFromDrive(driveUrls, visitorSearchTerm)` - Process photos from Drive
- `batchProcessDriveFiles(sheetData, urlColumn, nameColumn)` - Batch process Drive files

## 📊 Google Sheets Examples

### Example 1: Create Visitors from Sheet
```javascript
function createVisitorsFromCurrentSheet() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const data = sheet.getDataRange().getValues();
  
  const result = processVisitorsFromSheet(data);
  console.log(`Created ${result.successCount} visitors`);
}
```

### Example 2: Update Visitors from Sheet
```javascript
function updateVisitorsFromCurrentSheet() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const data = sheet.getDataRange().getValues();
  
  const result = updateVisitorsFromSheet(data, 'email');
  console.log(`Updated ${result.successCount} visitors`);
}
```

### Required Sheet Format
Your Google Sheet should have these columns (headers in row 1):

| first_name | last_name | email | mobile | company | purpose | visit_date | visit_time |
|------------|-----------|-------|---------|---------|---------|------------|------------|
| John | Smith | john@example.com | +1-555-0101 | Tech Corp | Meeting | 2025-01-20 | 09:00 |

### Optional Columns
- `license_plate` - Vehicle license plate
- `vehicle_make` - Vehicle make
- `vehicle_model` - Vehicle model
- `vehicle_color` - Vehicle color
- `notes` - Additional notes
- `photo_url` - Google Drive photo URL

## 🖼 Google Drive Integration

### Processing Photos from Drive
```javascript
function processPhotos() {
  const driveUrls = [
    'https://drive.google.com/file/d/1ABC123.../view',
    'https://drive.google.com/file/d/1XYZ789.../view'
  ];
  
  const result = processVisitorPhotosFromDrive(driveUrls, 'john@example.com');
  console.log(`Processed ${result.readyCount} photos`);
}
```

### Batch Process from Sheet
If your sheet has a `photo_url` column with Google Drive links:
```javascript
function batchProcessPhotos() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const data = sheet.getDataRange().getValues();
  
  const result = batchProcessDriveFiles(data, 'photo_url', 'email');
  console.log(`Processed ${result.successCount} files`);
}
```

## 🔧 Advanced Usage

### Custom Data Validation
```javascript
function validateAndCreateVisitors() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const data = sheet.getDataRange().getValues();
  
  // Validate sheet structure first
  const validation = validateSheetStructure(data, ['first_name', 'last_name', 'email']);
  
  if (!validation.valid) {
    console.error('Validation failed:', validation.error);
    return;
  }
  
  // Process if valid
  const result = processVisitorsFromSheet(data);
  console.log('Processing complete:', result);
}
```

### Error Handling and Logging
```javascript
function robustVisitorCreation() {
  try {
    const result = createVisitor({
      first_name: 'Jane',
      last_name: 'Doe',
      email: 'jane@example.com'
    });
    
    if (result.success) {
      console.log('✅ Success:', result.message);
    } else {
      console.error('❌ Failed:', result.error);
    }
  } catch (error) {
    console.error('🚨 Exception:', error);
  }
}
```

## 🎯 Best Practices

### 1. Always Test API Connection First
```javascript
const connectionTest = testAPIConnection();
if (!connectionTest.success) {
  console.error('API connection failed');
  return;
}
```

### 2. Handle Rate Limiting
Add delays between bulk operations:
```javascript
// In your loops
Utilities.sleep(500); // 500ms delay
```

### 3. Validate Data Before Processing
```javascript
if (!visitor_data.first_name || !visitor_data.last_name) {
  console.error('Missing required fields');
  return;
}
```

### 4. Log Results for Debugging
```javascript
result.results.forEach(res => {
  console.log(`Row ${res.row}: ${res.success ? '✅' : '❌'} ${res.message}`);
});
```

## 🐛 Troubleshooting

### Common Issues

**1. "API connection failed" or "DNS error"**
- **Problem**: Google Apps Script can't reach `localhost:3000` (your local server)
- **Solution 1**: Use ngrok to expose your local API:
  ```bash
  brew install ngrok
  ngrok http 3000
  # Update API_BASE_URL to use the ngrok URL (e.g., https://abc123.ngrok.io)
  ```
- **Solution 2**: Deploy to AWS for permanent access
- **Check**: Verify your local API is running (`python run.py`)

**2. "Invalid API key"**
- Check your `API_BASE_URL` and `API_KEY` in `authentication.js`
- Verify your API key is active and has proper permissions

**2. "Invalid Google Drive URL format"**
- Ensure Drive URLs are in format: `https://drive.google.com/file/d/FILE_ID/view`
- Check file sharing permissions (must be accessible to your account)

**3. "Missing required fields"**
- Verify your sheet has the required columns: `first_name`, `last_name`
- Check for empty cells in required columns

**4. "Authentication failed"**
- Verify your EVTrack credentials are configured in the API
- Check if the API service is running and accessible

### Debugging Steps

1. **Test individual functions first:**
   ```javascript
   testBasicFunctions();
   ```

2. **Check the execution log:**
   - Go to Execution transcript in Apps Script editor
   - Look for specific error messages

3. **Test with small data sets:**
   - Start with 1-2 rows before processing large sheets
   - Use the `createSampleVisitorSheet()` function for testing

## 📝 Example Workflows

### Workflow 1: Weekly Visitor Registration
```javascript
function weeklyVisitorProcessing() {
  // 1. Get data from "Weekly Visitors" sheet
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Weekly Visitors');
  const data = sheet.getDataRange().getValues();
  
  // 2. Validate and process
  const validation = validateSheetStructure(data, ['first_name', 'last_name', 'email']);
  if (!validation.valid) {
    console.error('Sheet validation failed:', validation.error);
    return;
  }
  
  // 3. Create visitors
  const result = processVisitorsFromSheet(data);
  
  // 4. Generate invitations
  if (result.successCount > 0) {
    console.log(`Created ${result.successCount} visitors, generating invitations...`);
    // Add invitation logic here
  }
  
  // 5. Log summary
  console.log(`Weekly processing complete: ${result.successCount} success, ${result.failureCount} failures`);
}
```

### Workflow 2: Photo Badge Generation
```javascript
function generateBadgesWithPhotos() {
  // 1. Get visitor data with photo URLs
  const sheet = SpreadsheetApp.getActiveSheet();
  const data = sheet.getDataRange().getValues();
  
  // 2. Process photos from Drive
  const photoResult = batchProcessDriveFiles(data, 'photo_url', 'email');
  
  // 3. Generate badges for successful photo uploads
  photoResult.results.forEach(result => {
    if (result.success) {
      const badgeResult = generateVisitorBadge(result.searchTerm);
      console.log(`Badge for ${result.searchTerm}: ${badgeResult.success ? 'Generated' : 'Failed'}`);
    }
  });
}
```

## 🔗 API Integration

This Google Apps Script integration works with the EVTrack API endpoints:

- **Visitor Operations**: `/visitors`, `/visitors/update`, `/visitors/profile`
- **Vehicle Operations**: `/vehicles/add`, `/vehicles/update`
- **Credential Operations**: `/credentials/add`
- **Invitation Operations**: `/visitors/invite`
- **Badge Operations**: `/visitors/badge`
- **Sheets Integration**: `/sheets/visitors/create`, `/sheets/visitors/update`
- **Drive Integration**: `/drive/photos/process`, `/drive/files/batch`

## 🔐 Security Notes

- Store your API key securely in the script properties or use environment variables
- Be cautious with file sharing permissions on Google Drive
- Regularly review and rotate your API keys
- Only grant necessary permissions to your Google Apps Script project

## 🆘 Support

For additional help:
1. Check the `examples.js` file for comprehensive usage examples
2. Run `testBasicFunctions()` to verify your setup
3. Review the execution transcript for detailed error messages
4. Ensure your API service is running and accessible

---

**🎉 You're now ready to automate EVTrack workflows with Google Workspace!**
