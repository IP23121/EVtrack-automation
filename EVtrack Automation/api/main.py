from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request, Header, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from selenium.webdriver.common.by import By
from utils.selenium_utils import start_driver
from utils.lambda_selenium import start_driver_lambda, cleanup_temp_files
from automation.login import EvTrackLogin
from automation.visitors import VisitorAutomation
from automation.vehicles import VehicleAutomation
from automation.credentials import CredentialAutomation
from automation.invitation import InvitationAutomation
from automation.badges import BadgeAutomation
from models.visitor import VisitorData, VehicleData, CredentialData
import logging
import os
import time
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Check for .env file and provide helpful error message
env_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if not os.path.exists(env_file_path):
    print("\nWARNING: No .env file found!")
    print("Please copy .env.example to .env and configure your credentials:")
    print(f"   cp '{os.path.dirname(os.path.dirname(__file__))}/.env.example' '{env_file_path}'")
    print("Then edit .env with your EVTrack email and password\n")

# Time validation function
def validate_time_format(time_string):
    """
    Validate that time string is in HH:MM format with valid hours (00-23) and minutes (00-59)
    Returns the validated time string or raises HTTPException if invalid
    """
    if not time_string or not time_string.strip():
        return ""  # Empty is allowed
    
    time_string = time_string.strip()
    
    # Check exact format: HH:MM with exactly 5 characters
    if len(time_string) != 5:
        raise HTTPException(status_code=400, detail=f"Invalid time format '{time_string}'. Must be exactly HH:MM format (5 characters)")
    
    # Check regex pattern
    pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
    if not re.match(pattern, time_string):
        raise HTTPException(status_code=400, detail=f"Invalid time format '{time_string}'. Must be HH:MM format with valid hours (00-23) and minutes (00-59)")
    
    # Additional validation to ensure colon is in correct position
    if time_string[2] != ':':
        raise HTTPException(status_code=400, detail=f"Invalid time format '{time_string}'. Colon must be in position 3 (HH:MM)")
    
    # Parse and validate hours and minutes
    try:
        hours, minutes = time_string.split(':')
        hours_int = int(hours)
        minutes_int = int(minutes)
        
        if hours_int < 0 or hours_int > 23:
            raise HTTPException(status_code=400, detail=f"Invalid hours '{hours}'. Must be between 00 and 23")
        
        if minutes_int < 0 or minutes_int > 59:
            raise HTTPException(status_code=400, detail=f"Invalid minutes '{minutes}'. Must be between 00 and 59")
            
        # Return validated time string with proper zero-padding
        return f"{hours_int:02d}:{minutes_int:02d}"
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid time format '{time_string}'. Hours and minutes must be numeric")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="EvTrack Automation API", 
    version="2.0.0",
    description="Enhanced EVTrack automation API with Cognito and Google OAuth authentication",
    docs_url=None,  # Disable default docs
    redoc_url=None  # Disable default redoc
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get credentials from environment variables
EVTRACK_EMAIL = os.getenv("EVTRACK_EMAIL")
EVTRACK_PASSWORD = os.getenv("EVTRACK_PASSWORD")
VALID_API_KEYS = os.getenv("API_KEYS", "").split(",") if os.getenv("API_KEYS") else []

# Simple authentication function that supports X-API-Key header and Bearer token
async def verify_auth(
    request: Request,
    x_api_key: str = Header(None, alias="X-API-Key"),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))
):
    """Simple authentication supporting X-API-Key header and Bearer token"""
    
    # Try X-API-Key header first (for Google Apps Script)
    if x_api_key and x_api_key in VALID_API_KEYS:
        return {
            "auth_type": "api_key_header",
            "user_data": None,
            "user_id": "api_user",
            "username": "api_user"
        }
    
    # Try Bearer token (for Cognito/OAuth)
    if credentials:
        token = credentials.credentials
        
        # Try Cognito JWT first if configured
        cognito_user_pool_id = os.getenv('COGNITO_USER_POOL_ID')
        cognito_client_id = os.getenv('COGNITO_CLIENT_ID')
        
        if cognito_user_pool_id and cognito_client_id:
            # TODO: Add proper Cognito JWT verification when auth module is available
            logger.info("Cognito configured but JWT verification not implemented yet")
            pass
        
        # Fallback to API key in Bearer token
        if token in VALID_API_KEYS:
            return {
                "auth_type": "api_key_bearer",
                "user_data": None,
                "user_id": "api_user",
                "username": "api_user"
            }
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Use X-API-Key header or Authorization: Bearer <token>"
    )

# Set headless mode for browser (False to see the browser)
HEADLESS_MODE = os.environ.get('HEADLESS_MODE', 'False').lower() == 'true'

def get_driver(headless=None):
    """
    Get the appropriate WebDriver based on environment
    
    Args:
        headless (bool): Override headless mode. If None, uses HEADLESS_MODE
        
    Returns:
        WebDriver: Configured driver instance
    """
    if headless is None:
        headless = HEADLESS_MODE
    
    # Check if we're in AWS Lambda
    is_lambda = os.environ.get('AWS_LAMBDA_FUNCTION_NAME') is not None
    
    if is_lambda:
        return start_driver_lambda(headless=True)  # Always headless in Lambda
    else:
        return start_driver(headless=headless)

def validate_and_clean_time_fields(data_dict):
    """
    Validate and clean all time fields in a data dictionary
    Modifies the dictionary in place and returns it
    """
    time_fields = ['activateTime', 'expiryTime', 'active_time', 'expiry_time']
    
    for field in time_fields:
        if field in data_dict:
            try:
                data_dict[field] = validate_time_format(data_dict[field])
                logger.info(f"Validated time field {field}: '{data_dict[field]}'")
            except HTTPException as e:
                logger.error(f"Time validation failed for field {field}: {e.detail}")
                raise e
    
    return data_dict

@app.get("/docs", response_class=HTMLResponse)
async def custom_swagger_ui():
    """Custom Swagger UI with Uppy Dashboard file upload functionality that matches the HTML site exactly"""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <title>EvTrack Automation API - Swagger UI</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css" />
    <!-- Uppy CSS for file uploads -->
    <link href="https://releases.transloadit.com/uppy/v3.25.0/uppy.min.css" rel="stylesheet">
    <style>
        html {
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }
        *, *:before, *:after {
            box-sizing: inherit;
        }
        body {
            margin:0;
            background: #fafafa;
            font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        
        /* Custom styling to match EvTrack theme */
        .swagger-ui .topbar {
            background-color: #1a1a1a;
            border-bottom: 1px solid #333;
        }
        
        .swagger-ui .topbar .download-url-wrapper {
            display: none;
        }
        
        .swagger-ui .info .title {
            color: #2c5530;
            font-size: 2.5rem;
            font-weight: 700;
        }
        
        .swagger-ui .info .description {
            font-size: 1.1rem;
            line-height: 1.6;
            color: #333;
        }
        
        /* Style operation blocks */
        .swagger-ui .opblock {
            border: 1px solid #e1e8ed;
            border-radius: 8px;
            margin-bottom: 16px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        .swagger-ui .opblock.opblock-get .opblock-summary {
            background: rgba(76, 175, 80, 0.1);
            border-color: #4CAF50;
        }
        
        .swagger-ui .opblock.opblock-post .opblock-summary {
            background: rgba(33, 150, 243, 0.1);
            border-color: #2196F3;
        }
        
        /* Hide examples that don't match our requirements */
        .swagger-ui .model-example {
            display: none;
        }
        
        /* Clean up the request body examples */
        .swagger-ui .models {
            display: none;
        }
        
        /* Custom header */
        .custom-header {
            background: linear-gradient(135deg, #2c5530 0%, #4a7c59 100%);
            color: white;
            padding: 20px;
            text-align: center;
            margin-bottom: 20px;
        }
        
        .custom-header h1 {
            margin: 0;
            font-size: 2rem;
            font-weight: 700;
        }
        
        .custom-header p {
            margin: 8px 0 0 0;
            opacity: 0.9;
            font-size: 1.1rem;
        }

        /* Enhanced file upload styling to match HTML site exactly */
        .file-upload-container {
            border: 2px dashed #d1d5db;
            border-radius: 8px;
            padding: 20px;
            margin: 10px 0;
            background: #f9fafb;
            position: relative;
        }

        .file-upload-container.drag-over {
            border-color: #2196F3;
            background: rgba(33, 150, 243, 0.05);
        }

        .uppy-dashboard-container {
            min-height: 150px;
            border-radius: 6px;
        }

        .file-upload-status {
            display: none;
            margin-top: 10px;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 14px;
        }

        .file-upload-status.success {
            display: block;
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }

        .file-upload-status.error {
            display: block;
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }

        .uppy-Dashboard-dropFilesHereHint {
            font-size: 16px !important;
            color: #6b7280 !important;
        }

        .uppy-Dashboard-browse {
            color: #2196F3 !important;
            font-weight: 600 !important;
        }

        .uppy-DashboardTab-name {
            font-size: 14px !important;
            font-weight: 500 !important;
        }

        /* Custom file input styling for photo, signature, id_document */
        .swagger-ui input[type="file"][name="photo"],
        .swagger-ui input[type="file"][name="signature"], 
        .swagger-ui input[type="file"][name="id_document"] {
            display: none !important;
        }

        .swagger-ui .file[data-param-name="photo"] .file-upload-input,
        .swagger-ui .file[data-param-name="signature"] .file-upload-input,
        .swagger-ui .file[data-param-name="id_document"] .file-upload-input {
            display: none !important;
        }

        /* Enhanced dropdown styling for country codes */
        .swagger-ui select[name="country_code"],
        .swagger-ui select[name="alt_country_code"] {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            background-color: white;
            font-size: 14px;
        }

        .swagger-ui select[name="country_code"]:focus,
        .swagger-ui select[name="alt_country_code"]:focus {
            outline: none;
            border-color: #2196F3;
            box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.1);
        }

        /* Phone input styling */
        .swagger-ui input[name="mobile"],
        .swagger-ui input[name="alt_number"] {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            font-size: 14px;
        }

        /* Orange highlighting for required vehicle fields in Add Vehicle action - Using multiple targeting methods */
        .swagger-ui input[name="vin"].vehicle-required-field,
        .swagger-ui input[name="number_plate"].vehicle-required-field {
            border: 2px solid #ff6b35 !important;
            background-color: rgba(255, 107, 53, 0.1) !important;
            box-shadow: 0 0 0 1px rgba(255, 107, 53, 0.2) !important;
        }

        /* Green highlighting when field has valid content */
        .swagger-ui input[name="vin"].vehicle-valid-field,
        .swagger-ui input[name="number_plate"].vehicle-valid-field {
            border: 2px solid #4CAF50 !important;
            background-color: rgba(76, 175, 80, 0.1) !important;
            box-shadow: 0 0 0 1px rgba(76, 175, 80, 0.2) !important;
        }

        /* Fallback CSS selectors for different swagger UI structures */
        .swagger-ui .opblock input[name="vin"]:not(.vehicle-valid-field),
        .swagger-ui .opblock input[name="number_plate"]:not(.vehicle-valid-field) {
            border: 2px solid #ff6b35 !important;
            background-color: rgba(255, 107, 53, 0.1) !important;
            box-shadow: 0 0 0 1px rgba(255, 107, 53, 0.2) !important;
        }

        /* Orange star indicator for required vehicle fields */
        .vehicle-required-indicator {
            color: #ff6b35 !important;
            font-weight: bold !important;
            margin-left: 4px !important;
            font-size: 16px !important;
        }

        /* Simple CSS to add orange star to VIN and Number Plate labels in Add Vehicle */
        .swagger-ui .opblock .parameter__name:after {
            content: "";
        }
        
        .swagger-ui .opblock .parameter__name[data-name="vin"]:after,
        .swagger-ui .opblock .parameter__name[data-name="number_plate"]:after {
            content: " ";
            color: #ff6b35;
            font-weight: bold;
            margin-left: 4px;
        }

        /* Additional CSS targeting for table-based layouts */
        .swagger-ui table tr td:first-child:has(+ td input[name="vin"]):after,
        .swagger-ui table tr td:first-child:has(+ td input[name="number_plate"]):after {
            content: " ";
            color: #ff6b35;
            font-weight: bold;
            margin-left: 4px;
        }

        /* Force orange highlighting on VIN and Number Plate inputs in Add Vehicle */
        .swagger-ui input[name="vin"],
        .swagger-ui input[name="number_plate"] {
            border: 2px solid #ff6b35 !important;
            background-color: rgba(255, 107, 53, 0.1) !important;
            box-shadow: 0 0 0 1px rgba(255, 107, 53, 0.2) !important;
        }
    </style>
</head>
<body>
    <div class="custom-header">
        <h1>EvTrack Automation API</h1>
        <p>Swagger UI for EvTrack Automation</p>
    </div>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-standalone-preset.js"></script>
    <!-- Uppy JavaScript for file uploads -->
    <script src="https://releases.transloadit.com/uppy/v3.25.0/uppy.min.js"></script>
    <script>
        // Global variables for Uppy instances
        window.uppyInstances = {};
        
        function initializeUppyForFileInput(fileParam, container) {
            const fieldName = fileParam.getAttribute('data-param-name');
            if (!fieldName || window.uppyInstances[fieldName]) return;

            console.log('Initializing Uppy for field:', fieldName);

            // Create Uppy container
            const uppyContainer = document.createElement('div');
            uppyContainer.id = `uppy-${fieldName}`;
            uppyContainer.className = 'uppy-dashboard-container';
            
            // Create file upload container wrapper
            const uploadContainer = document.createElement('div');
            uploadContainer.className = 'file-upload-container';
            uploadContainer.appendChild(uppyContainer);
            
            // Create status message div
            const statusDiv = document.createElement('div');
            statusDiv.className = 'file-upload-status';
            statusDiv.id = `upload-status-${fieldName}`;
            uploadContainer.appendChild(statusDiv);

            // Replace the file input with our Uppy container
            fileParam.style.display = 'none';
            fileParam.parentNode.insertBefore(uploadContainer, fileParam.nextSibling);

            // Determine accepted file types based on field name
            let acceptedTypes = ['image/*'];
            if (fieldName === 'id_document') {
                acceptedTypes = ['image/*', 'application/pdf'];
            }

            // Initialize Uppy with Dashboard
            const uppy = new Uppy.Uppy({
                id: fieldName,
                autoProceed: false,
                allowMultipleUploads: false,
                restrictions: {
                    maxNumberOfFiles: 1,
                    allowedFileTypes: acceptedTypes,
                    maxFileSize: 10 * 1024 * 1024 // 10MB
                },
                meta: {
                    fieldName: fieldName
                }
            });

            uppy.use(Uppy.Dashboard, {
                target: `#uppy-${fieldName}`,
                inline: true,
                width: '100%',
                height: 150,
                hideUploadButton: true,
                hideRetryButton: true,
                hidePauseResumeButton: true,
                hideCancelButton: false,
                showProgressDetails: true,
                note: fieldName === 'photo' ? 'Images only, up to 10MB' :
                      fieldName === 'signature' ? 'Images only, up to 10MB' :
                      fieldName === 'id_document' ? 'Images and PDFs, up to 10MB' : 'Up to 10MB',
                proudlyDisplayPoweredByUppy: false,
                locale: {
                    strings: {
                        dropHereOr: 'Drop files here, %{browse} or import from:',
                        browse: 'browse files'
                    }
                }
            });

            uppy.use(Uppy.Webcam, {
                target: Uppy.Dashboard,
                modes: ['picture'],
                mirror: false,
                showVideoSourceDropdown: true,
                showRecordingLength: false
            });

            // Handle file addition
            uppy.on('file-added', (file) => {
                console.log('File added to Uppy:', file.name, 'for field:', fieldName);
                
                // Convert file to format expected by original file input
                const dt = new DataTransfer();
                
                // Create a File object from Uppy file data
                file.data.arrayBuffer().then(buffer => {
                    const fileBlob = new File([buffer], file.name, { type: file.type });
                    dt.items.add(fileBlob);
                    
                    // Set to original file input for form submission
                    fileParam.files = dt.files;
                    
                    console.log('File set to original input for:', fieldName);
                    
                    // Show success status
                    statusDiv.className = 'file-upload-status success';
                    statusDiv.textContent = `File ${file.name} ready for upload`;
                }).catch(err => {
                    console.error('Error processing file:', err);
                    statusDiv.className = 'file-upload-status error';
                    statusDiv.textContent = ` Error processing ${file.name}`;
                });
            });

            // Handle file removal
            uppy.on('file-removed', (file) => {
                console.log('File removed from Uppy:', file.name, 'for field:', fieldName);
                
                // Clear the original file input
                fileParam.value = '';
                
                // Hide status
                statusDiv.className = 'file-upload-status';
                statusDiv.textContent = '';
            });

            // Handle errors
            uppy.on('restriction-failed', (file, error) => {
                console.error('Uppy restriction failed:', error);
                statusDiv.className = 'file-upload-status error';
                statusDiv.textContent = ` ${error.message}`;
            });

            // Store the Uppy instance
            window.uppyInstances[fieldName] = uppy;
            
            console.log('Uppy initialized successfully for:', fieldName);
        }

        function hideFileInput(fieldName) {
            const interval = setInterval(() => {
                const fileInput = document.querySelector(`input[type="file"][name="${fieldName}"]`);
                if (fileInput) {
                    fileInput.style.display = 'none';
                    fileInput.style.visibility = 'hidden';
                    const wrapper = fileInput.closest('.file');
                    if (wrapper) {
                        wrapper.style.display = 'none';
                    }
                    clearInterval(interval);
                }
            }, 100);
        }

        function hideAllFileInputs() {
            hideFileInput('photo');
            hideFileInput('signature');
            hideFileInput('id_document');
        }

        function setupCountryCodeDropdowns() {
            const mobileCountryCode = document.querySelector('select[name="country_code"]');
            const altCountryCode = document.querySelector('select[name="alt_country_code"]');
            const mobileInput = document.querySelector('input[name="mobile"]');
            const altNumberInput = document.querySelector('input[name="alt_number"]');
            
            if (mobileCountryCode && mobileInput) {
                mobileCountryCode.addEventListener('change', function() {
                    const selectedValue = this.value;
                    const countryCode = selectedValue.split(' +')[1];
                    
                    if (countryCode) {
                        // Update the mobile input with the country code
                        const currentNumber = mobileInput.value.replace(/^\\+?\\d+\\s?/, ''); // Remove existing country code
                        mobileInput.value = `+${countryCode} ${currentNumber}`.trim();
                        mobileInput.placeholder = `+${countryCode} 123456789`;
                        
                        console.log('Mobile country code selected:', selectedValue, 'Code:', countryCode);
                    }
                });
                
                // Set initial placeholder
                mobileInput.placeholder = 'Select country code first';
            }
            
            if (altCountryCode && altNumberInput) {
                altCountryCode.addEventListener('change', function() {
                    const selectedValue = this.value;
                    const countryCode = selectedValue.split(' +')[1];
                    
                    if (countryCode) {
                        // Update the alt number input with the country code
                        const currentNumber = altNumberInput.value.replace(/^\\+?\\d+\\s?/, ''); // Remove existing country code
                        altNumberInput.value = `+${countryCode} ${currentNumber}`.trim();
                        altNumberInput.placeholder = `+${countryCode} 123456789`;
                        
                        console.log('Alt country code selected:', selectedValue, 'Code:', countryCode);
                    }
                });
                
                // Set initial placeholder
                altNumberInput.placeholder = 'Select country code first';
            }
            
            // Add validation to ensure country code is selected before allowing phone input
            if (mobileInput) {
                mobileInput.addEventListener('focus', function() {
                    if (!mobileCountryCode || !mobileCountryCode.value) {
                        alert('Please select a country code first');
                        if (mobileCountryCode) mobileCountryCode.focus();
                    }
                });
            }
            
            if (altNumberInput) {
                altNumberInput.addEventListener('focus', function() {
                    if (!altCountryCode || !altCountryCode.value) {
                        alert('Please select a country code first for the alternate number');
                        if (altCountryCode) altCountryCode.focus();
                    }
                });
            }
        }

        function setupVehicleFieldHighlighting() {
            // Function to add orange star to VIN and Number Plate labels in Add Vehicle operation
            function addStarsToVehicleFields() {
                // Look for labels and spans that contain VIN or number_plate text
                const allElements = document.querySelectorAll('label, span, div, td, th');
                
                allElements.forEach(element => {
                    const text = element.textContent.toLowerCase().trim();
                    
                    // Check if this is a VIN field label and we haven't added a star yet
                    if (text === 'vin' && !element.innerHTML.includes('')) {
                        element.innerHTML = element.innerHTML + ' <span style="color: #ff6b35; font-weight: bold; margin-left: 4px;"></span>';
                        console.log('Added star to VIN field');
                    }
                    
                    // Check if this is a Number Plate field label and we haven't added a star yet
                    if ((text === 'number_plate' || text === 'numberplate') && !element.innerHTML.includes('')) {
                        element.innerHTML = element.innerHTML + ' <span style="color: #ff6b35; font-weight: bold; margin-left: 4px;"></span>';
                        console.log('Added star to Number Plate field');
                    }
                });
                
                // Also try to find input fields directly and add stars to their labels
                const vinInput = document.querySelector('input[name="vin"]');
                const plateInput = document.querySelector('input[name="number_plate"]');
                
                if (vinInput) {
                    const vinLabel = vinInput.closest('tr')?.querySelector('td:first-child') || 
                                    vinInput.parentElement?.querySelector('label') ||
                                    vinInput.previousElementSibling;
                    if (vinLabel && !vinLabel.innerHTML.includes('')) {
                        vinLabel.innerHTML = vinLabel.innerHTML + ' <span style="color: #ff6b35; font-weight: bold; margin-left: 4px;"></span>';
                        console.log('Added star to VIN input label');
                    }
                }
                
                if (plateInput) {
                    const plateLabel = plateInput.closest('tr')?.querySelector('td:first-child') || 
                                      plateInput.parentElement?.querySelector('label') ||
                                      plateInput.previousElementSibling;
                    if (plateLabel && !plateLabel.innerHTML.includes('')) {
                        plateLabel.innerHTML = plateLabel.innerHTML + ' <span style="color: #ff6b35; font-weight: bold; margin-left: 4px;"></span>';
                        console.log('Added star to Number Plate input label');
                    }
                }
            }
            
            // Run multiple times to catch all cases as Swagger UI loads dynamically
            setTimeout(addStarsToVehicleFields, 500);
            setTimeout(addStarsToVehicleFields, 1000);
            setTimeout(addStarsToVehicleFields, 2000);
            setTimeout(addStarsToVehicleFields, 3000);
            setTimeout(addStarsToVehicleFields, 5000);
        }



        window.onload = function() {
            const ui = SwaggerUIBundle({
                url: '/docs/openapi.yaml',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                defaultModelsExpandDepth: -1,
                defaultModelExpandDepth: 1,
                docExpansion: "list",
                filter: false,
                showExtensions: false,
                showCommonExtensions: false,
                tryItOutEnabled: true,
                requestInterceptor: function(request) {
                    // Ensure all text fields start empty by removing example values
                    if (request.body && typeof request.body === 'string') {
                        try {
                            const bodyObj = JSON.parse(request.body);
                            // Clear any "string" default values but keep actual user input
                            for (const key in bodyObj) {
                                if (bodyObj[key] === "string" || bodyObj[key] === "example") {
                                    delete bodyObj[key];
                                }
                            }
                            request.body = JSON.stringify(bodyObj);
                        } catch (e) {
                            // If not JSON, leave as is
                        }
                    }

                    return request;
                },
                onComplete: function() {
                    // Custom JavaScript to ensure proper form behavior including Uppy setup and phone inputs
                    setTimeout(function() {
                        // Clear all default text values in input fields
                        const inputs = document.querySelectorAll('input[type="text"], input[type="date"], input[type="email"]');
                        inputs.forEach(function(input) {
                            if (input.value === 'string' || input.value === 'example' || input.placeholder === 'string') {
                                input.value = '';
                                input.placeholder = '';
                            }
                        });
                        
                        // Ensure location field is required and properly highlighted
                        const locationSelect = document.querySelector('select[name="locationId"]');
                        if (locationSelect) {
                            locationSelect.setAttribute('required', 'true');
                            const parentDiv = locationSelect.closest('div');
                            if (parentDiv) {
                                const label = parentDiv.querySelector('label') || parentDiv.previousElementSibling;
                                if (label && !label.innerHTML.includes('*')) {
                                    label.innerHTML += ' <span style="color: red;">*</span>';
                                }
                            }
                        }

                        // Setup country code dropdowns
                        setupCountryCodeDropdowns();

                        // Setup vehicle field indicators for Add Vehicle action
                        setupVehicleFieldHighlighting();



                        // Initialize Uppy for file upload fields
                        const fileInputs = document.querySelectorAll('input[type="file"][name="photo"], input[type="file"][name="signature"], input[type="file"][name="id_document"]');
                        fileInputs.forEach(fileInput => {
                            const container = fileInput.closest('.swagger-ui');
                            if (container) {
                                initializeUppyForFileInput(fileInput, container);
                            }
                        });

                        // Set up observer for dynamically added elements
                        const observer = new MutationObserver(function(mutations) {
                            mutations.forEach(function(mutation) {
                                if (mutation.type === 'childList') {
                                    // Check for new file inputs
                                    const newFileInputs = mutation.target.querySelectorAll ? 
                                        mutation.target.querySelectorAll('input[type="file"][name="photo"], input[type="file"][name="signature"], input[type="file"][name="id_document"]') : [];
                                    
                                    newFileInputs.forEach(fileInput => {
                                        if (!fileInput.dataset.uppyInitialized) {
                                            fileInput.dataset.uppyInitialized = 'true';
                                            const container = fileInput.closest('.swagger-ui');
                                            if (container) {
                                                setTimeout(() => initializeUppyForFileInput(fileInput, container), 100);
                                            }
                                        }
                                    });

                                    // Check for new country code dropdowns
                                    const newCountrySelects = mutation.target.querySelectorAll ? 
                                        mutation.target.querySelectorAll('select[name="country_code"], select[name="alt_country_code"]') : [];
                                    
                                    if (newCountrySelects.length > 0) {
                                        setupCountryCodeDropdowns();
                                    }

                                    // Check for new vehicle input fields
                                    const newVehicleInputs = mutation.target.querySelectorAll ? 
                                        mutation.target.querySelectorAll('input[name="vin"], input[name="number_plate"]') : [];
                                    
                                    if (newVehicleInputs.length > 0) {
                                        setupVehicleFieldHighlighting();
                                    }
                                }
                            });
                        });

                        observer.observe(document.body, {
                            childList: true,
                            subtree: true
                        });
                        
                    }, 1500); // Increased delay to ensure Swagger UI is fully loaded
                }
            });
        };
    </script>
</body>
</html>
    """)


@app.get("/favicon.ico")
async def favicon():
    """Handle favicon requests to prevent 404 errors"""
    return HTMLResponse(content="", status_code=204)

@app.get("/docs/openapi.yaml", response_class=HTMLResponse)
async def get_openapi_yaml():
    """Serve the OpenAPI spec in YAML format"""
    try:
        with open("api/openapi.yaml", "r") as f:
            yaml_content = f.read()
        return HTMLResponse(content=yaml_content, media_type="text/yaml")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="OpenAPI spec not found")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        # Store the websocket connection in the app state
        app.state.active_websocket = websocket
        
        while True:
            # Keep the connection alive and wait for progress updates
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        # Clear the websocket when disconnected
        app.state.active_websocket = None

@app.get("/visitors")
async def get_visitors(search: str = None, auth_data: dict = Depends(verify_auth)):
    driver = None
    try:
        # Check if credentials are available
        if not EVTRACK_EMAIL or not EVTRACK_PASSWORD:
            raise HTTPException(status_code=500, detail="Missing credentials. Please check your .env file.")
            
        driver = get_driver()
        login = EvTrackLogin(driver)
        
        # First ensure we're logged in
        try:
            logger.info("Attempting to log in...")
            await login.login(EVTRACK_EMAIL, EVTRACK_PASSWORD)
            logger.info("Login successful")
        except Exception as login_error:
            logger.error(f"Login failed: {str(login_error)}")
            raise HTTPException(status_code=401, detail=f"Login failed: {str(login_error)}")
        
        # Initialize visitor automation with websocket if available
        visitor_automation = VisitorAutomation(driver)
        if hasattr(app.state, 'active_websocket'):
            visitor_automation.set_websocket(app.state.active_websocket)
        
        # Get visitor summary
        logger.info("Getting visitor summary...")
        visitors = await visitor_automation.get_visitor_summary(search)
        
        # The get_visitor_summary already returns complete details, so just return them
        logger.info(f"Retrieved {len(visitors)} visitors with complete details")
        return {"visitors": visitors}
        
    except Exception as e:
        logger.error(f"Failed to search visitors: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}")

@app.post("/visitors")
async def create_visitor(request: Request, auth_data: dict = Depends(verify_auth)):
    driver = None
    try:
        # Get form data from request
        form_data = await request.form()
        visitor_data = {}
        
        logger.info(f"Form data keys: {list(form_data.keys())}")
        
        # Convert form data to dictionary, handling file uploads with enhanced Uppy support
        for key, value in form_data.items():
            logger.info(f"Processing form field: {key} = {type(value)} - {getattr(value, 'filename', 'N/A')}")
            
            if key in ['photo', 'signature', 'id_document']:
                # Handle file uploads from both standard form uploads and Uppy Dashboard
                if hasattr(value, 'file') and value.filename and value.filename.strip():
                    file_data = await value.read()
                    
                    # Only process if we actually have file data
                    if file_data and len(file_data) > 0:
                        upload_key = f'{key}_upload'
                        visitor_data[upload_key] = {
                            'filename': value.filename,
                            'content_type': value.content_type or 'application/octet-stream',
                            'file_data': file_data
                        }
                        logger.info(f"Created {upload_key} with {len(file_data)} bytes for {value.filename}")
                    else:
                        logger.warning(f"{key} field has filename but no file data")
                
                else:
                    logger.info(f"{key} field found but no valid file upload: hasattr(file)={hasattr(value, 'file')}, filename={getattr(value, 'filename', 'None')}")
            else:
                # Special handling for checkboxes
                if key in ['first_nations', 'disability']:
                    visitor_data[key] = 'true' if value == 'true' else 'false'
                else:
                    visitor_data[key] = value
        
        logger.info(f"Final visitor_data keys: {list(visitor_data.keys())}")
        
        # Process country codes and phone numbers
        country_code = visitor_data.get('country_code')
        mobile = visitor_data.get('mobile')
        alt_country_code = visitor_data.get('alt_country_code') 
        alt_number = visitor_data.get('alt_number')
        
        # Handle mobile number with country code
        if country_code and mobile:
            # Extract country code from dropdown selection (e.g., "United States +1" -> "+1")
            code_part = country_code.split(' +')[-1] if ' +' in country_code else ''
            if code_part:
                # If mobile doesn't already have the country code, add it
                mobile_clean = str(mobile).strip()
                if not mobile_clean.startswith('+'):
                    visitor_data['mobile'] = f"+{code_part} {mobile_clean}"
                    logger.info(f"Updated mobile with country code: {visitor_data['mobile']}")
                else:
                    visitor_data['mobile'] = mobile_clean
                    logger.info(f"Mobile already has country code: {visitor_data['mobile']}")
        elif mobile:
            # Just use the mobile number as-is if no country code selected
            visitor_data['mobile'] = str(mobile).strip()
            logger.info(f"Mobile number without country code selection: {visitor_data['mobile']}")
        
        # Handle alternate number with country code
        if alt_country_code and alt_number:
            # Extract country code from dropdown selection
            alt_code_part = alt_country_code.split(' +')[-1] if ' +' in alt_country_code else ''
            if alt_code_part:
                # If alt_number doesn't already have the country code, add it
                alt_number_clean = str(alt_number).strip()
                if not alt_number_clean.startswith('+'):
                    visitor_data['alt_number'] = f"+{alt_code_part} {alt_number_clean}"
                    logger.info(f"Updated alt_number with country code: {visitor_data['alt_number']}")
                else:
                    visitor_data['alt_number'] = alt_number_clean
                    logger.info(f"Alt number already has country code: {visitor_data['alt_number']}")
        elif alt_number:
            # Just use the alt number as-is if no country code selected
            visitor_data['alt_number'] = str(alt_number).strip()
            logger.info(f"Alt number without country code selection: {visitor_data['alt_number']}")
        
        # Remove the separate country code fields since we've merged them into the phone numbers
        visitor_data.pop('country_code', None)
        visitor_data.pop('alt_country_code', None)
        
        # Log file upload details
        for upload_type in ['photo_upload', 'signature_upload', 'id_document_upload']:
            if upload_type in visitor_data:
                logger.info(f"{upload_type} details: filename={visitor_data[upload_type]['filename']}, size={len(visitor_data[upload_type]['file_data'])} bytes")
        
        if not EVTRACK_EMAIL or not EVTRACK_PASSWORD:
            raise HTTPException(status_code=500, detail="Missing credentials")
            
        driver = start_driver(headless=HEADLESS_MODE)
        login = EvTrackLogin(driver)
        await login.login(EVTRACK_EMAIL, EVTRACK_PASSWORD)
        
        visitor_automation = VisitorAutomation(driver)
        if hasattr(app.state, 'active_websocket'):
            visitor_automation.set_websocket(app.state.active_websocket)
        
        # Create/update visitor using the automation
        result = await visitor_automation.create_update_visitor(visitor_data)
        
        return {"success": True, "visitor_id": result.get("visitor_id"), "message": "Visitor created successfully"}
        
    except Exception as e:
        logger.error(f"Failed to create visitor: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}")

@app.post("/visitors/update")
async def update_visitor(request: Request, auth_data: dict = Depends(verify_auth)):
    driver = None
    try:
        # Get form data from request
        form_data = await request.form()
        
        # Extract search term and visitor data
        search_term = form_data.get('search_term')
        if not search_term:
            raise HTTPException(status_code=400, detail="Search term is required to find the visitor to update")
        
        logger.info(f"Update request - Search term: {search_term}")
        logger.info(f"Form data keys: {list(form_data.keys())}")
        
        # Create visitor data dictionary with only non-empty fields
        visitor_data = {}
        
        # Field mapping for form data to visitor attributes
        field_mapping = {
            'initials': 'initials',
            'first_name': 'first_name',
            'last_name': 'last_name',
            'id_number': 'id_number',
            'company': 'company',
            'mobile': 'mobile',
            'email': 'email',
            'address': 'address',
            'nationality': 'nationality',
            'comments': 'comments',
            'reason_for_visit': 'reason_for_visit',
            'first_nations': 'first_nations',
            'disability': 'disability',
            'date_of_birth': 'date_of_birth',
            'country_of_issue': 'country_of_issue',
            'alt_number': 'alt_number',
            'gender': 'gender'
        }
        
        # Only include fields that have actual values
        for form_key, attr_name in field_mapping.items():
            value = form_data.get(form_key)
            if value and str(value).strip():  # Only set if value exists and is not just whitespace
                # Special handling for checkboxes - only process if change flag is set
                if form_key in ['first_nations', 'disability']:
                    change_flag = form_data.get(f'{form_key}_change')
                    if change_flag == 'true':  # Only update if user explicitly wants to change it
                        visitor_data[attr_name] = 'true' if value == 'true' else 'false'
                        logger.info(f"Updated checkbox {form_key} -> {attr_name}: {visitor_data[attr_name]} (change requested)")
                    else:
                        logger.info(f"Skipping checkbox {form_key} - no change requested")
                else:
                    visitor_data[attr_name] = str(value).strip()
                    logger.info(f"Added field {form_key} -> {attr_name}: {visitor_data[attr_name]}")
            else:
                # For checkboxes, only process unchecking if change flag is set
                if form_key in ['first_nations', 'disability']:
                    change_flag = form_data.get(f'{form_key}_change')
                    if change_flag == 'true':  # Only update if user explicitly wants to change it
                        visitor_data[attr_name] = 'false'  # Explicitly set to false when unchecked and change requested
                        logger.info(f"Updated checkbox {form_key} -> {attr_name}: false (unchecked, change requested)")
                    else:
                        logger.info(f"Skipping checkbox {form_key} - no change requested")
                else:
                    logger.info(f"Skipping empty field {form_key}: '{value}'")
        
        # Process country codes and phone numbers for update
        country_code = form_data.get('country_code')
        mobile = form_data.get('mobile')
        alt_country_code = form_data.get('alt_country_code') 
        alt_number = form_data.get('alt_number')
        
        # Handle mobile number with country code
        if country_code and mobile:
            # Extract country code from dropdown selection (e.g., "United States +1" -> "+1")
            code_part = country_code.split(' +')[-1] if ' +' in str(country_code) else ''
            if code_part:
                # If mobile doesn't already have the country code, add it
                mobile_clean = str(mobile).strip()
                if not mobile_clean.startswith('+'):
                    visitor_data['mobile'] = f"+{code_part} {mobile_clean}"
                    logger.info(f"Updated mobile with country code: {visitor_data['mobile']}")
                else:
                    visitor_data['mobile'] = mobile_clean
                    logger.info(f"Mobile already has country code: {visitor_data['mobile']}")
        elif mobile and str(mobile).strip():
            # Just use the mobile number as-is if no country code selected
            visitor_data['mobile'] = str(mobile).strip()
            logger.info(f"Mobile number without country code selection: {visitor_data['mobile']}")
        
        # Handle alternate number with country code
        if alt_country_code and alt_number:
            # Extract country code from dropdown selection
            alt_code_part = alt_country_code.split(' +')[-1] if ' +' in str(alt_country_code) else ''
            if alt_code_part:
                # If alt_number doesn't already have the country code, add it
                alt_number_clean = str(alt_number).strip()
                if not alt_number_clean.startswith('+'):
                    visitor_data['alt_number'] = f"+{alt_code_part} {alt_number_clean}"
                    logger.info(f"Updated alt_number with country code: {visitor_data['alt_number']}")
                else:
                    visitor_data['alt_number'] = alt_number_clean
                    logger.info(f"Alt number already has country code: {visitor_data['alt_number']}")
        elif alt_number and str(alt_number).strip():
            # Just use the alt number as-is if no country code selected
            visitor_data['alt_number'] = str(alt_number).strip()
            logger.info(f"Alt number without country code selection: {visitor_data['alt_number']}")
        
        # Handle file uploads separately with enhanced Uppy support
        files = {}
        file_fields = ['photo', 'signature', 'id_document']
        for field_name in file_fields:
            file_upload = form_data.get(field_name)
            if file_upload and hasattr(file_upload, 'filename') and file_upload.filename and file_upload.filename.strip():
                file_content = await file_upload.read()
                # Only process files that actually have content
                if file_content and len(file_content) > 0:
                    files[f'{field_name}_upload'] = {
                        'filename': file_upload.filename,
                        'content_type': file_upload.content_type or 'application/octet-stream',
                        'content': file_content
                    }
                    logger.info(f"Found file upload for {field_name}: {file_upload.filename} ({len(file_content)} bytes)")
                else:
                    logger.warning(f"File upload for {field_name} has no content")
            else:
                logger.info(f"No valid file upload found for {field_name}")
        
        if not EVTRACK_EMAIL or not EVTRACK_PASSWORD:
            raise HTTPException(status_code=500, detail="Missing credentials")
            
        driver = start_driver(headless=HEADLESS_MODE)
        login = EvTrackLogin(driver)
        await login.login(EVTRACK_EMAIL, EVTRACK_PASSWORD)
        
        # Use the new visitor create/update automation class
        from automation.visitor_create_update import VisitorCreateUpdateAutomation
        visitor_automation = VisitorCreateUpdateAutomation(driver)
        
        if hasattr(app.state, 'active_websocket'):
            visitor_automation.set_websocket(app.state.active_websocket)
        
        # Update visitor using the new automation that follows the exact EVTrack workflow
        result = await visitor_automation.update_visitor_profile(search_term, visitor_data, files)
        
        if result['success']:
            return {
                "success": True, 
                "message": result['message'],
                "updated_fields": result['updated_fields'],
                "visitor_name": result.get('visitor_name'),
                "uuid": result.get('visitor_uuid')
            }
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'Unknown error'))
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to update visitor: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}")

@app.get("/visitors/{visitor_id}")
async def get_visitor(visitor_id: str, auth_data: dict = Depends(verify_auth)):
    driver = None
    try:
        if not EVTRACK_EMAIL or not EVTRACK_PASSWORD:
            raise HTTPException(status_code=500, detail="Missing credentials")
            
        driver = start_driver(headless=HEADLESS_MODE)
        login = EvTrackLogin(driver)
        await login.login(EVTRACK_EMAIL, EVTRACK_PASSWORD)
        
        visitor_automation = VisitorAutomation(driver)
        if hasattr(app.state, 'active_websocket'):
            visitor_automation.set_websocket(app.state.active_websocket)
        
        details = await visitor_automation.get_visitor_detail(visitor_id)
        
        if details:
            # First try to get the portrait image
            try:
                # Wait for portrait image to be available
                await driver.wait_for_selector(".visitor-portrait img, .visitor-photo img", timeout=5000)
                image_element = driver.find_element(By.CSS_SELECTOR, ".visitor-portrait img, .visitor-photo img")
                portrait_url = image_element.get_attribute('src')
                logger.info(f"Found portrait image: {portrait_url}")
            except Exception as e:
                logger.warning(f"Could not find portrait image: {str(e)}")
                portrait_url = None

            visitor_data = {
                "id": visitor_id,
                "first_name": details.get("first_name", ""),
                "last_name": details.get("last_name", ""),
                "company": details.get("company", ""),
                "mobile": details.get("mobile", ""),
                "nationality": details.get("nationality", ""),
                "country_of_issue": details.get("country_of_issue", ""),
                "email": details.get("email", ""),
                "reason_for_visit": details.get("reason_for_visit", ""),
                "created_by": details.get("created_by", ""),
                "guard_house": details.get("guard_house", ""),
                "created_at": details.get("created_at", ""),
                "updated_at": details.get("updated_at", ""),
                "status": "Current", 
                "portrait_url": portrait_url,
                "profile_url": f"https://app.evtrack.com/visitor/edit?uuid={visitor_id}"
            }
            return visitor_data
        else:
            raise HTTPException(status_code=404, detail="Visitor not found")
    except Exception as e:
        logger.error(f"Failed to get visitor details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}")

@app.post("/vehicles/add")
async def add_vehicle(request: Request, auth_data: dict = Depends(verify_auth)):
    driver = None
    try:
        # Get form data from request
        form_data = await request.form()
        
        # Extract search term for visitor
        search_term = form_data.get('search_term')
        if not search_term:
            raise HTTPException(status_code=400, detail="Search term is required to find the visitor")
        
        logger.info(f"Add vehicle request - Search term: {search_term}")
        
        # Create vehicle data from form
        vehicle_data = {}
        vehicle_fields = [
            'number_plate', 'vehicle_type', 'make', 'model', 'year', 
            'colour', 'vin', 'engine_number', 'licence_disc_number', 
            'licence_expiry_date', 'document_number', 'comments'
        ]
        
        for field in vehicle_fields:
            value = form_data.get(field)
            if value and str(value).strip():
                if field == 'year':
                    try:
                        vehicle_data[field] = int(value)
                    except ValueError:
                        continue
                else:
                    vehicle_data[field] = str(value).strip()
                logger.info(f"Added vehicle field {field}: {vehicle_data[field]}")
        
        # Validate that at least VIN or number_plate is provided
        if not vehicle_data.get('vin') and not vehicle_data.get('number_plate'):
            raise HTTPException(status_code=400, detail="Either VIN or Number Plate is required")
        
        if not EVTRACK_EMAIL or not EVTRACK_PASSWORD:
            raise HTTPException(status_code=500, detail="Missing credentials")
            
        driver = start_driver(headless=HEADLESS_MODE)
        login = EvTrackLogin(driver)
        await login.login(EVTRACK_EMAIL, EVTRACK_PASSWORD)
        
        vehicle_automation = VehicleAutomation(driver)
        
        # Add the vehicle using the new method that follows exact EVTrack workflow
        result = await vehicle_automation.add_vehicle(search_term, vehicle_data)
        
        if result['success']:
            return {
                "success": True, 
                "message": result['message'],
                "search_term": search_term,
                "vehicle_data": vehicle_data,
                "visitor_name": result.get('visitor_name'),
                "visitor_uuid": result.get('visitor_uuid')
            }
        else:
            raise HTTPException(status_code=400, detail=result.get('message', 'Failed to add vehicle to visitor profile'))
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to add vehicle: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}")

@app.post(
    "/vehicles/update",
    tags=["vehicles"],
    summary="Update vehicle information",
    description="Update existing vehicle information by searching for the vehicle",
    responses={
        200: {"description": "Vehicle updated successfully"},
        400: {"description": "Invalid input data or vehicle not found"},
        401: {"description": "Authentication failed"},
        500: {"description": "Internal server error"},
    }
)
async def update_vehicle(request: Request, auth_data: dict = Depends(verify_auth)):
    driver = None
    try:
        # Get form data from request
        form_data = await request.form()
        
        # Extract search term for vehicle
        search_term = form_data.get('search_term')
        if not search_term:
            raise HTTPException(status_code=400, detail="Search term is required to find the vehicle")
        
        logger.info(f"Update vehicle request - Search term: {search_term}")
        
        # Create vehicle data from form (only include fields that have values)
        vehicle_data = {}
        vehicle_fields = [
            'number_plate', 'vehicle_type', 'make', 'model', 'year', 
            'colour', 'vin', 'engine_number', 'licence_disc_number', 
            'licence_expiry_date', 'document_number', 'comments'
        ]
        
        for field in vehicle_fields:
            value = form_data.get(field)
            if value and str(value).strip():
                if field == 'year':
                    try:
                        vehicle_data[field] = int(value)
                    except ValueError:
                        continue
                else:
                    vehicle_data[field] = str(value).strip()
                logger.info(f"Will update vehicle field {field}: {vehicle_data[field]}")
        
        # Check if any fields were provided for update
        if not vehicle_data:
            raise HTTPException(status_code=400, detail="No vehicle data provided for update")
        
        if not EVTRACK_EMAIL or not EVTRACK_PASSWORD:
            raise HTTPException(status_code=500, detail="Missing credentials")
            
        driver = start_driver(headless=HEADLESS_MODE)
        login = EvTrackLogin(driver)
        await login.login(EVTRACK_EMAIL, EVTRACK_PASSWORD)
        
        vehicle_automation = VehicleAutomation(driver)
        
        # Update the vehicle using the new method that goes to vehicle list
        result = await vehicle_automation.update_vehicle(search_term, vehicle_data)
        
        if result['success']:
            return {
                "success": True, 
                "message": result['message'],
                "search_term": search_term,
                "vehicle_data": vehicle_data,
                "updated_fields": result.get('updated_fields', [])
            }
        else:
            raise HTTPException(status_code=400, detail=result.get('message', 'Failed to update vehicle'))
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to update vehicle: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}")

@app.post(
    "/credentials/add",
    tags=["credentials"],
    summary="Add credential to visitor",
    description="Add a new access credential to an existing visitor's profile",
    responses={
        201: {"description": "Credential added successfully"},
        400: {"description": "Invalid input data or visitor not found"},
        401: {"description": "Authentication failed"},
        500: {"description": "Internal server error"},
    }
)
async def add_credential(request: Request, auth_data: dict = Depends(verify_auth)):
    driver = None
    try:
        # Get form data from request
        form_data = await request.form()
        
        # Extract search term for visitor
        search_term = form_data.get('search_term')
        if not search_term:
            raise HTTPException(status_code=400, detail="Search term is required to find the visitor")
        
        logger.info(f"Add credential request - Search term: {search_term}")
        
        # Create credential data from form
        credential_data = {}
        credential_fields = [
            'reader_type', 'unique_identifier', 'pin', 'active_date', 
            'expiry_date', 'use_limit', 'comments', 'status'
        ]
        
        # Handle time fields separately with validation
        time_fields = ['active_time', 'expiry_time']
        for time_field in time_fields:
            time_value = form_data.get(time_field)
            if time_value and str(time_value).strip():
                time_str = str(time_value).strip()
                try:
                    # Validate and get properly formatted time
                    validated_time = validate_time_format(time_str)
                    credential_data[time_field] = validated_time
                    logger.info(f"Added credential time field {time_field}: {credential_data[time_field]}")
                except HTTPException as e:
                    # Re-raise the validation error
                    raise e
        
        for field in credential_fields:
            value = form_data.get(field)
            if value and str(value).strip():
                if field == 'use_limit':
                    try:
                        credential_data[field] = int(value)
                    except ValueError:
                        continue
                elif field in ['active_date', 'expiry_date']:
                    # Handle date fields
                    credential_data[field] = str(value).strip()
                else:
                    credential_data[field] = str(value).strip()
                logger.info(f"Added credential field {field}: {credential_data[field]}")
        
        # Handle access_control_lists checkbox
        access_control_lists = form_data.get('access_control_lists')
        credential_data['access_control_lists'] = access_control_lists == 'on' if access_control_lists else True
        
        # Validate required fields
        if not credential_data.get('reader_type'):
            raise HTTPException(status_code=400, detail="Reader Type is required")

        if not EVTRACK_EMAIL or not EVTRACK_PASSWORD:
            raise HTTPException(status_code=500, detail="Missing credentials")
            
        driver = start_driver(headless=HEADLESS_MODE)
        login = EvTrackLogin(driver)
        await login.login(EVTRACK_EMAIL, EVTRACK_PASSWORD)
        
        credential_automation = CredentialAutomation(driver)
        
        # First search for the visitor to get UUID
        uuid, url = credential_automation.search_visitor_for_credentials(search_term)
        if not uuid:
            raise HTTPException(status_code=404, detail=f"Visitor not found with search term: {search_term}")
        
        # Create CredentialData object
        credential_data_obj = CredentialData(**credential_data)
        
        # Add the credential
        success = credential_automation.add_credential(uuid, credential_data_obj)
        
        if success:
            return {"status": "success",
                "message": "Credential added successfully",
                "visitor_uuid": uuid,
                "credential_data": credential_data_obj
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to add credential")
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to add credential: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}")

@app.post(
    "/credentials/update",
    tags=["credentials"],
    summary="Update credential information",
    description="Update existing credential information for a visitor",
    responses={
        200: {"description": "Credential updated successfully"},
        400: {"description": "Invalid input data or credential not found"},
        401: {"description": "Authentication failed"},
        500: {"description": "Internal server error"},
    }
)
async def update_credential(request: Request, auth_data: dict = Depends(verify_auth)):
    driver = None
    try:
        # Get form data from request
        form_data = await request.form()
        
        # Extract search term and credential search detail
        search_term = form_data.get('search_term')
        credential_search_detail = form_data.get('credential_search_detail')
        
        if not search_term:
            raise HTTPException(status_code=400, detail="Search term is required to find the visitor")
        if not credential_search_detail:
            raise HTTPException(status_code=400, detail="Credential search detail is required to find the specific credential")
        
        logger.info(f"Update credential request - Search term: {search_term}, Credential search detail: {credential_search_detail}")
        
        # Create credential data from form (only fields to update)
        credential_data = {}
        credential_fields = [
            'active_date', 'expiry_date', 'use_limit', 'comments', 'status'
        ]
        
        # Handle time fields separately with validation
        time_fields = ['active_time', 'expiry_time']
        for time_field in time_fields:
            time_value = form_data.get(time_field)
            if time_value and str(time_value).strip():
                time_str = str(time_value).strip()
                try:
                    # Validate and get properly formatted time
                    validated_time = validate_time_format(time_str)
                    credential_data[time_field] = validated_time
                    logger.info(f"Added credential time field {time_field}: {credential_data[time_field]}")
                except HTTPException as e:
                    # Re-raise the validation error
                    raise e
        
        for field in credential_fields:
            value = form_data.get(field)
            if value and str(value).strip():
                if field == 'use_limit':
                    try:
                        credential_data[field] = int(value)
                    except ValueError:
                        continue
                elif field in ['active_date', 'expiry_date']:
                    credential_data[field] = str(value).strip()
                else:
                    credential_data[field] = str(value).strip()
                logger.info(f"Added credential field {field}: {credential_data[field]}")

        if not EVTRACK_EMAIL or not EVTRACK_PASSWORD:
            raise HTTPException(status_code=500, detail="Missing credentials")
            
        driver = start_driver(headless=HEADLESS_MODE)
        login = EvTrackLogin(driver)
        await login.login(EVTRACK_EMAIL, EVTRACK_PASSWORD)
        
        credential_automation = CredentialAutomation(driver)
        
        # Create CredentialData object
        credential_data_obj = CredentialData(**credential_data)
        
        # Update the credential using the new method
        success = credential_automation.update_credential(search_term, credential_search_detail, credential_data_obj)
        
        if success:
            return {"status": "success", 
                "message": "Credential updated successfully",
                "search_term": search_term,
                "credential_search_detail": credential_search_detail,
                "updated_data": credential_data_obj
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to update credential")
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to update credential: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}")

@app.post(
    "/visitors/invite",
    tags=["invitations"],
    summary="Invite a visitor",
    description="Send an invitation to a visitor by searching for them first",
    responses={
        200: {"description": "Invitation sent successfully"},
        400: {"description": "Invalid input data or visitor not found"},
        401: {"description": "Authentication failed"},
        500: {"description": "Internal server error"},
    }
)
async def invite_visitor(request: Request, auth_data: dict = Depends(verify_auth)):
    """Invite a visitor by searching for them first."""
    driver = None
    try:
        # Get form data from request
        form_data = await request.form()
        
        # Extract search term
        search_term = form_data.get('search_term')
        if not search_term:
            logger.error("No search term found in request")
            raise HTTPException(status_code=400, detail="Search term is required to find the visitor")
        
        logger.info(f"Invite visitor request - Search term: {search_term}")
        logger.info(f"Form data received: {dict(form_data)}")
        
        # Extract invitation form data - using direct values from form
        location_mapping = {
            "Select Location...": "",
            "Inherited - Default Visitor Access List": "0",
            "IO Main Campus": "2715"
        }
        
        # Map visit reason display names to numeric IDs
        visit_reason_mapping = {
            "None": "0",
            "Visitor": "642",
            "Delivery": "643", 
            "Guest House Visitor": "645",
            "Parent Pickup/Dropoff": "647",
            "Staff": "648",
            "Tour": "646"
        }
        
        # Get form values and map display names to IDs
        location_display = form_data.get('locationId', '')
        visit_reason_display = form_data.get('visitReasonId', 'Parent Pickup/Dropoff')
        
        invite_data = {
            'credentialReaderType': form_data.get('credentialReaderType', 'QR_CODE'),
            'visitReasonId': visit_reason_mapping.get(visit_reason_display, '647'),  # Map display name to numeric ID
            'locationId': location_mapping.get(location_display, ''),  # Map display name to ID
            'activateDate': form_data.get('activateDate', ''),
            'activateTime': form_data.get('activateTime', ''),
            'expiryDate': form_data.get('expiryDate', ''),
            'expiryTime': form_data.get('expiryTime', ''),
            'visitorUuid': form_data.get('visitorUuid', '')  # Hidden field, auto-filled
        }
        
        # Validate required fields using the mapped values
        if not invite_data['locationId']:
            raise HTTPException(status_code=400, detail="Location is required")
        
        logger.info(f"Processed invite data: {invite_data}")
        
        if not EVTRACK_EMAIL or not EVTRACK_PASSWORD:
            raise HTTPException(status_code=500, detail="Missing credentials")
            
        driver = start_driver(headless=HEADLESS_MODE)
        
        # Use InvitationAutomation
        from automation.invitation import InvitationAutomation
        invitation_automation = InvitationAutomation(driver)
        if hasattr(app.state, 'active_websocket'):
            invitation_automation.set_websocket(app.state.active_websocket)
        
        # Invite visitor using the invitation automation - it handles login automatically
        result = await invitation_automation.invite_visitor(
            search_term, 
            invite_data, 
            username=EVTRACK_EMAIL, 
            password=EVTRACK_PASSWORD
        )
        
        if result['success']:
            return {
                "success": True,
                "message": result['message'],
                "visitor_uuid": result['visitor_uuid'],
                "visitor_name": result['visitor_name'],
                "invite_settings": result['invite_settings']
            }
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to invite visitor'))
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to invite visitor: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}")

@app.post(
    "/visitors/badge",
    tags=["badges"],
    summary="Generate visitor badge",
    description="Generate and download a visitor badge by searching for them first",
    responses={
        200: {
            "description": "Badge file generated successfully", 
            "content": {
                "application/pdf": {
                    "schema": {
                        "type": "string",
                        "format": "binary"
                    }
                },
                "application/octet-stream": {
                    "schema": {
                        "type": "string", 
                        "format": "binary"
                    }
                }
            }
        },
        400: {"description": "Invalid input data or visitor not found"},
        401: {"description": "Authentication failed"},
        500: {"description": "Internal server error"},
    }
)
async def get_visitor_badge(request: Request, auth_data: dict = Depends(verify_auth)):
    """Generate and download a visitor badge by searching for them first."""
    driver = None
    try:
        # Handle both form data and JSON
        search_term = None
        
        # Try form data first (for Swagger UI)
        try:
            form_data = await request.form()
            # Debug: log all form fields
            logger.info(f"Badge: All form fields: {dict(form_data)}")
            # Support both 'search' (from OpenAPI spec) and 'search_term' (from HTML site)
            search_term = form_data.get('search') or form_data.get('search_term')
            logger.info(f"Badge: Received form data: search={form_data.get('search')}, search_term={form_data.get('search_term')}")
        except Exception as form_error:
            logger.info(f"Badge: Form parsing failed: {form_error}")
            # Try JSON if form data fails
            try:
                json_data = await request.json()
                search_term = json_data.get('search') or json_data.get('search_term')
                logger.info(f"Badge: Received JSON data: search={json_data.get('search')}, search_term={json_data.get('search_term')}")
            except Exception as json_error:
                logger.info(f"Badge: JSON parsing failed: {json_error}")
        
        if not search_term:
            logger.error("Badge: No search term found in request")
            raise HTTPException(status_code=400, detail="Search term is required to find the visitor")
        
        logger.info(f"Badge generation request - Search term: {search_term}")
        
        if not EVTRACK_EMAIL or not EVTRACK_PASSWORD:
            raise HTTPException(status_code=500, detail="Missing credentials")
            
        driver = start_driver(headless=HEADLESS_MODE)
        
        # Navigate directly to visitor list instead of going through dashboard
        driver.get('https://app.evtrack.com/visitor/list')
        
        # Handle login if redirected
        if '/login' in driver.current_url:
            login = EvTrackLogin(driver)
            await login.login(EVTRACK_EMAIL, EVTRACK_PASSWORD)
            # After login, navigate back to visitor list
            driver.get('https://app.evtrack.com/visitor/list')
        
        visitor_automation = VisitorAutomation(driver)
        if hasattr(app.state, 'active_websocket'):
            visitor_automation.set_websocket(app.state.active_websocket)
        
        # Generate badge using the automation
        result = await visitor_automation.get_visitor_badge(search_term)
        
        # Decode the base64 content to get the raw file bytes
        import base64
        badge_bytes = base64.b64decode(result['badge_content'])
        
        # Return the file directly for download in Swagger UI
        from fastapi.responses import Response
        
        # Determine the appropriate content type and file extension
        content_type = result.get('content_type', 'application/pdf')
        visitor_name = result['visitor_name'].replace(' ', '_').replace(',', '').replace('.', '')
        
        # Create a clean filename
        if content_type == 'application/pdf':
            filename = f"badge_{visitor_name}_{result['visitor_uuid'][:8]}.pdf"
        elif 'image' in content_type:
            ext = 'png' if 'png' in content_type else 'jpg'
            filename = f"badge_{visitor_name}_{result['visitor_uuid'][:8]}.{ext}"
        else:
            filename = f"badge_{visitor_name}_{result['visitor_uuid'][:8]}.pdf"
        
        logger.info(f"Returning badge file: {filename}, Content-Type: {content_type}, Size: {len(badge_bytes)} bytes")
        
        # Return the badge file directly for download
        return Response(
            content=badge_bytes,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(badge_bytes))
            }
        )
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to generate badge: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}")

@app.post(
    "/visitors/profile",
    tags=["visitors"],
    summary="Get comprehensive visitor profile",
    description="Get comprehensive visitor profile by searching for them first, then navigating to profile tab",
    responses={
        200: {"description": "Profile retrieved successfully"},
        400: {"description": "Invalid input data"},
        404: {"description": "Visitor not found"},
        401: {"description": "Authentication failed"},
        500: {"description": "Internal server error"},
    }
)
async def get_visitor_profile(request: Request, auth_data: dict = Depends(verify_auth)):
    """Get comprehensive visitor profile by searching for them first, then navigating to profile tab."""
    driver = None
    try:
        # Try to get search term from multiple sources
        search_term = None
        
        # Try JSON first
        try:
            json_data = await request.json()
            search_term = json_data.get('search_term')
            logger.info(f"Profile: Received JSON data: search_term={search_term}")
        except:
            # Try form data
            try:
                form_data = await request.form()
                search_term = form_data.get('search_term')
                logger.info(f"Profile: Received form data: search_term={search_term}")
            except:
                # Try query parameters
                search_term = request.query_params.get('search_term')
                logger.info(f"Profile: Received query params: search_term={search_term}")
        
        if not search_term:
            logger.error("Profile: No search term found in request")
            raise HTTPException(status_code=400, detail="Search term is required to find the visitor")
        
        logger.info(f"Visitor profile request - Search term: {search_term}")
        
        if not EVTRACK_EMAIL or not EVTRACK_PASSWORD:
            raise HTTPException(status_code=500, detail="Missing credentials")
            
        driver = start_driver(headless=HEADLESS_MODE)
        login = EvTrackLogin(driver)
        await login.login(EVTRACK_EMAIL, EVTRACK_PASSWORD)
        
        # Use the same approach as invitation and badge generation - search first
        from automation.visitor_search import VisitorSearchAutomation
        search_automation = VisitorSearchAutomation(driver)
        if hasattr(app.state, 'active_websocket'):
            search_automation.set_websocket(app.state.active_websocket)
        
        # Search for the visitor using the reliable search method
        visitor_data = await search_automation.search_visitor_case_insensitive(search_term)
        
        if not visitor_data:
            raise HTTPException(status_code=404, detail=f"No visitor found for search term: {search_term}")
        
        # Now get comprehensive profile data using the new method
        from automation.visitor_details import VisitorDetailsAutomation
        details_automation = VisitorDetailsAutomation(driver)
        if hasattr(app.state, 'active_websocket'):
            details_automation.set_websocket(app.state.active_websocket)
        
        # Get complete profile information from the profile tab
        profile_data = await details_automation.get_comprehensive_visitor_profile(visitor_data['uuid'])
        
        return {"success": True,
            "visitor_uuid": visitor_data['uuid'],
            "visitor_name": f"{visitor_data.get('first_name', '')} {visitor_data.get('last_name', '')}".strip(),
            "profile": profile_data
        }
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to get visitor profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}")

@app.post(
    "/login",
    tags=["authentication"],
    summary="Test login functionality",
    description="Test the EVTrack login credentials and connection",
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Authentication failed"},
        500: {"description": "Internal server error"},
    }
)
async def test_login(auth_data: dict = Depends(verify_auth)):
    """Test login functionality"""
    driver = None
    try:
        if not EVTRACK_EMAIL or not EVTRACK_PASSWORD:
            raise HTTPException(status_code=500, detail="Missing credentials. Please check your .env file.")
            
        driver = start_driver(headless=HEADLESS_MODE)
        login = EvTrackLogin(driver)
        
        # Test login
        await login.login(EVTRACK_EMAIL, EVTRACK_PASSWORD)
        
        return {
            "success": True, 
            "message": "Login successful",
            "user": auth_data.get("username", "unknown"),
            "auth_type": auth_data.get("auth_type", "unknown")
        }
        
    except Exception as e:
        logger.error(f"Login test failed: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Login failed: {str(e)}")
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}")

# ===== GOOGLE SHEETS INTEGRATION ENDPOINTS =====

@app.post(
    "/sheets/visitors/create",
    tags=["google-sheets"],
    summary="Create visitors from Google Sheets data",
    description="Bulk create visitors from Google Sheets formatted data",
    responses={
        200: {"description": "Visitors processed successfully"},
        400: {"description": "Invalid sheet data"},
        401: {"description": "Authentication failed"},
        500: {"description": "Internal server error"},
    }
)
async def create_visitors_from_sheets(request: Request, auth_data: dict = Depends(verify_auth)):
    """Bulk create visitors from Google Sheets formatted data"""
    driver = None
    try:
        # Get JSON data containing sheet rows
        json_data = await request.json()
        sheet_data = json_data.get('sheet_data')
        start_row = json_data.get('start_row', 2)
        end_row = json_data.get('end_row')
        
        if not sheet_data or len(sheet_data) < 2:
            raise HTTPException(status_code=400, detail="Sheet data must have at least 2 rows (headers + data)")
        
        # Google Sheets integration not yet implemented
        raise HTTPException(status_code=501, detail="Google Sheets integration not yet implemented - use basic visitor endpoints")
        
        if not EVTRACK_EMAIL or not EVTRACK_PASSWORD:
            raise HTTPException(status_code=500, detail="Missing credentials")
            
        driver = start_driver(headless=HEADLESS_MODE)
        login = EvTrackLogin(driver)
        await login.login(EVTRACK_EMAIL, EVTRACK_PASSWORD)
        
        visitor_automation = VisitorAutomation(driver)
        if hasattr(app.state, 'active_websocket'):
            visitor_automation.set_websocket(app.state.active_websocket)
        
        # Process each row
        results = []
        errors = []
        headers = sheet_data[0]
        
        # Determine processing range
        last_row = end_row if end_row else len(sheet_data)
        
        for i in range(start_row - 1, min(last_row, len(sheet_data))):
            row_number = i + 1
            row_data = sheet_data[i]
            
            try:
                # Convert sheet row to visitor data
                visitor_data = sheets_processor.format_visitor_from_row(row_data, headers)
                
                # Validate required fields
                if not visitor_data.get('first_name') or not visitor_data.get('last_name'):
                    errors.append({
                        'row': row_number,
                        'error': 'Missing required fields: first_name, last_name'
                    })
                    continue
                
                # Create visitor using existing automation
                result = await visitor_automation.create_update_visitor(visitor_data)
                
                results.append({
                    'row': row_number,
                    'visitor_name': f"{visitor_data['first_name']} {visitor_data['last_name']}",
                    'success': True,
                    'message': 'Visitor created successfully',
                    'visitor_id': result.get('visitor_id')
                })
                
                # Add delay to avoid overwhelming the system
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error processing row {row_number}: {e}")
                errors.append({
                    'row': row_number,
                    'error': str(e)
                })
        
        success_count = len(results)
        failure_count = len(errors)
        
        return {
            "success": True,
            "processed": success_count + failure_count,
            "success_count": success_count,
            "failure_count": failure_count,
            "results": results,
            "errors": errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process visitors from sheets: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logger.error(f"Error closing browser: {e}")

@app.post(
    "/sheets/visitors/update",
    tags=["google-sheets"],
    summary="Update visitors from Google Sheets data",
    description="Bulk update visitors from Google Sheets formatted data",
    responses={
        200: {"description": "Visitors updated successfully"},
        400: {"description": "Invalid sheet data"},
        401: {"description": "Authentication failed"},
        500: {"description": "Internal server error"},
    }
)
async def update_visitors_from_sheets(request: Request, auth_data: dict = Depends(verify_auth)):
    """Bulk update visitors from Google Sheets formatted data"""
    driver = None
    try:
        # Get JSON data
        json_data = await request.json()
        sheet_data = json_data.get('sheet_data')
        search_column = json_data.get('search_column', 'email')
        start_row = json_data.get('start_row', 2)
        end_row = json_data.get('end_row')
        
        if not sheet_data or len(sheet_data) < 2:
            raise HTTPException(status_code=400, detail="Sheet data must have at least 2 rows (headers + data)")
        
        # Import the Google Sheets processor
        # from integrations.google_sheets import GoogleSheetsProcessor
        raise HTTPException(status_code=501, detail="Google Sheets bulk processing not yet implemented - use basic visitor endpoints")
        sheets_processor = GoogleSheetsProcessor()
        
        # Validate sheet structure
        validation_result = sheets_processor.validate_sheet_structure(sheet_data, [search_column])
        if not validation_result['valid']:
            raise HTTPException(status_code=400, detail=validation_result['error'])
        
        headers = sheet_data[0]
        search_column_index = headers.index(search_column)
        
        if not EVTRACK_EMAIL or not EVTRACK_PASSWORD:
            raise HTTPException(status_code=500, detail="Missing credentials")
            
        driver = start_driver(headless=HEADLESS_MODE)
        login = EvTrackLogin(driver)
        await login.login(EVTRACK_EMAIL, EVTRACK_PASSWORD)
        
        # Use the visitor update automation
        from automation.visitor_create_update import VisitorCreateUpdateAutomation
        visitor_automation = VisitorCreateUpdateAutomation(driver)
        if hasattr(app.state, 'active_websocket'):
            visitor_automation.set_websocket(app.state.active_websocket)
        
        # Process each row
        results = []
        errors = []
        
        # Determine processing range
        last_row = end_row if end_row else len(sheet_data)
        
        for i in range(start_row - 1, min(last_row, len(sheet_data))):
            row_number = i + 1
            row_data = sheet_data[i]
            
            try:
                # Get search term
                search_term = row_data[search_column_index]
                if not search_term:
                    errors.append({
                        'row': row_number,
                        'error': f'No value in search column "{search_column}"'
                    })
                    continue
                
                # Convert sheet row to visitor data
                visitor_data = sheets_processor.format_visitor_from_row(row_data, headers)
                
                # Update visitor
                result = await visitor_automation.update_visitor_profile(search_term, visitor_data, {})
                
                results.append({
                    'row': row_number,
                    'search_term': search_term,
                    'success': result['success'],
                    'message': result['message'] if result['success'] else result.get('error'),
                    'updated_fields': result.get('updated_fields', [])
                })
                
                # Add delay
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error processing row {row_number}: {e}")
                errors.append({
                    'row': row_number,
                    'error': str(e)
                })
        
        success_count = len([r for r in results if r['success']])
        failure_count = len([r for r in results if not r['success']]) + len(errors)
        
        return {
            "success": True,
            "processed": len(results) + len(errors),
            "success_count": success_count,
            "failure_count": failure_count,
            "results": results,
            "errors": errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update visitors from sheets: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logger.error(f"Error closing browser: {e}")

@app.post(
    "/sheets/visitors/search",
    tags=["google-sheets"],
    summary="Search for visitors in bulk",
    description="Search for multiple visitors and return results in Google Sheets format",
    responses={
        200: {"description": "Search completed successfully"},
        400: {"description": "Invalid search terms"},
        401: {"description": "Authentication failed"},
        500: {"description": "Internal server error"},
    }
)
async def search_visitors_for_sheets(request: Request, auth_data: dict = Depends(verify_auth)):
    """Search for multiple visitors and return results in Google Sheets format"""
    driver = None
    try:
        # Get JSON data
        json_data = await request.json()
        search_terms = json_data.get('search_terms')
        
        if not search_terms or not isinstance(search_terms, list):
            raise HTTPException(status_code=400, detail="Search terms must be provided as an array")
        
        if not EVTRACK_EMAIL or not EVTRACK_PASSWORD:
            raise HTTPException(status_code=500, detail="Missing credentials")
            
        driver = start_driver(headless=HEADLESS_MODE)
        login = EvTrackLogin(driver)
        await login.login(EVTRACK_EMAIL, EVTRACK_PASSWORD)
        
        visitor_automation = VisitorAutomation(driver)
        if hasattr(app.state, 'active_websocket'):
            visitor_automation.set_websocket(app.state.active_websocket)
        
        # Prepare results in sheet format
        results = []
        headers = [
            'Search Term', 'Status', 'First Name', 'Last Name', 'Email', 
            'Phone', 'Company', 'Visitor ID', 'Error'
        ]
        results.append(headers)
        
        for search_term in search_terms:
            try:
                # Search for visitor
                visitors = await visitor_automation.get_visitor_summary(search_term)
                
                if visitors and len(visitors) > 0:
                    visitor = visitors[0]  # Take first match
                    results.append([
                        search_term,
                        'Found',
                        visitor.get('first_name', ''),
                        visitor.get('last_name', ''),
                        visitor.get('email', ''),
                        visitor.get('mobile', ''),
                        visitor.get('company', ''),
                        visitor.get('visitor_id', ''),
                        ''
                    ])
                else:
                    results.append([
                        search_term,
                        'Not Found',
                        '', '', '', '', '', '',
                        'No matches found'
                    ])
                
                # Small delay between searches
                time.sleep(0.3)
                
            except Exception as e:
                logger.error(f"Error searching for {search_term}: {e}")
                results.append([
                    search_term,
                    'Error',
                    '', '', '', '', '', '',
                    str(e)
                ])
        
        return {
            "success": True,
            "searched": len(search_terms),
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to search visitors for sheets: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logger.error(f"Error closing browser: {e}")

# ===== GOOGLE DRIVE INTEGRATION ENDPOINTS =====

@app.post(
    "/drive/photos/process",
    tags=["google-drive"],
    summary="Process visitor photos from Google Drive",
    description="Process visitor photos from Google Drive URLs for badge generation",
    responses={
        200: {"description": "Photos processed successfully"},
        400: {"description": "Invalid Drive URLs"},
        401: {"description": "Authentication failed"},
        500: {"description": "Internal server error"},
    }
)
async def process_visitor_photos_from_drive(request: Request, auth_data: dict = Depends(verify_auth)):
    """Process visitor photos from Google Drive URLs"""
    try:
        # Get JSON data
        json_data = await request.json()
        drive_urls = json_data.get('drive_urls')
        visitor_search_term = json_data.get('visitor_search_term')
        
        if not drive_urls or not isinstance(drive_urls, list):
            raise HTTPException(status_code=400, detail="Drive URLs must be provided as an array")
        
        if not visitor_search_term:
            raise HTTPException(status_code=400, detail="Visitor search term is required")
        
        # Google Drive integration not yet implemented
        raise HTTPException(status_code=501, detail="Google Drive integration not yet implemented")
        
        # Process the URLs and validate files
        results = []
        errors = []
        
        for i, url in enumerate(drive_urls):
            try:
                # Extract file ID
                file_id = drive_processor.extract_file_id_from_url(url)
                if not file_id:
                    errors.append({
                        'url': url,
                        'error': 'Invalid Google Drive URL format'
                    })
                    continue
                
                # Validate file (this would typically check file accessibility)
                file_info = drive_processor.get_file_info(file_id, url)
                
                results.append({
                    'url': url,
                    'file_id': file_id,
                    'file_name': file_info.get('name', f'photo_{i+1}'),
                    'ready': True
                })
                
            except Exception as e:
                logger.error(f"Error processing Drive URL {url}: {e}")
                errors.append({
                    'url': url,
                    'error': str(e)
                })
        
        return {
            "success": True,
            "processed": len(drive_urls),
            "ready_count": len(results),
            "error_count": len(errors),
            "photos": results,
            "errors": errors,
            "visitor_search_term": visitor_search_term
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process Drive photos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post(
    "/drive/files/batch",
    tags=["google-drive"],
    summary="Batch process Google Drive files",
    description="Batch process files from Google Drive URLs with visitor association",
    responses={
        200: {"description": "Files processed successfully"},
        400: {"description": "Invalid sheet data or Drive URLs"},
        401: {"description": "Authentication failed"},
        500: {"description": "Internal server error"},
    }
)
async def batch_process_drive_files(request: Request, auth_data: dict = Depends(verify_auth)):
    """Batch process files from Google Drive URLs with visitor association"""
    try:
        # Get JSON data
        json_data = await request.json()
        sheet_data = json_data.get('sheet_data')
        url_column = json_data.get('url_column', 'photo_url')
        name_column = json_data.get('name_column', 'email')
        start_row = json_data.get('start_row', 2)
        
        if not sheet_data or len(sheet_data) < 2:
            raise HTTPException(status_code=400, detail="Sheet data must have at least 2 rows (headers + data)")
        
        # Google Drive integration not yet implemented  
        raise HTTPException(status_code=501, detail="Google Drive integration not yet implemented")
        
        headers = sheet_data[0]
        
        # Find column indices
        try:
            url_column_index = headers.index(url_column)
            name_column_index = headers.index(name_column)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Column not found: {e}")
        
        # Process each row
        results = []
        errors = []
        
        for i in range(start_row - 1, len(sheet_data)):
            row_number = i + 1
            row_data = sheet_data[i]
            
            try:
                drive_url = row_data[url_column_index] if url_column_index < len(row_data) else ''
                search_term = row_data[name_column_index] if name_column_index < len(row_data) else ''
                
                if not drive_url or not search_term:
                    errors.append({
                        'row': row_number,
                        'error': 'Missing URL or search term'
                    })
                    continue
                
                # Extract file ID and validate
                file_id = drive_processor.extract_file_id_from_url(drive_url)
                if not file_id:
                    errors.append({
                        'row': row_number,
                        'error': 'Invalid Google Drive URL format'
                    })
                    continue
                
                # Get file info
                file_info = drive_processor.get_file_info(file_id, drive_url)
                
                results.append({
                    'row': row_number,
                    'search_term': search_term,
                    'drive_url': drive_url,
                    'file_id': file_id,
                    'success': True,
                    'message': 'File processed and ready',
                    'file_name': file_info.get('name', 'unknown')
                })
                
            except Exception as e:
                logger.error(f"Error processing row {row_number}: {e}")
                errors.append({
                    'row': row_number,
                    'error': str(e)
                })
        
        success_count = len(results)
        failure_count = len(errors)
        
        return {
            "success": True,
            "processed": success_count + failure_count,
            "success_count": success_count,
            "failure_count": failure_count,
            "results": results,
            "errors": errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to batch process Drive files: {e}")
        raise HTTPException(status_code=500, detail=str(e))
async def google_oauth_callback(auth_code: str, redirect_uri: str):
    """Handle Google OAuth callback"""
    try:
        # Google auth not yet implemented
        raise HTTPException(status_code=501, detail="Google OAuth not yet implemented")
            
    except Exception as e:
        logger.error(f"Google OAuth callback failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get(
    "/auth/verify",
    tags=["authentication"],
    summary="Verify authentication token",
    description="Verify and return information about the current authentication token"
)
async def verify_authentication(auth_data: dict = Depends(verify_auth)):
    """Verify current authentication"""
    return {
        "authenticated": True,
        "auth_type": auth_data.get("auth_type"),
        "user_id": auth_data.get("user_id"),
        "username": auth_data.get("username"),
        "user_data": auth_data.get("user_data")
    }

@app.get(
    "/health",
    tags=["system"],
    summary="API Health Check",
    description="Check API health and configuration status"
)
async def health_check():
    """Enhanced health check endpoint for Google Apps Script and other integrations"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": time.time(),
        "authentication": {
            "cognito_configured": bool(os.getenv('COGNITO_USER_POOL_ID')),
            "google_oauth_configured": bool(os.getenv('GOOGLE_CLIENT_ID')),
            "api_keys_configured": bool(VALID_API_KEYS)
        },
        "evtrack_configured": bool(EVTRACK_EMAIL and EVTRACK_PASSWORD),
        "endpoints": {
            "visitors": "/visitors",
            "sheets_integration": "/sheets/visitors/create",
            "drive_integration": "/drive/photos/process",
            "authentication": "/auth/verify"
        }
    }

@app.get("/favicon.ico")
async def favicon():
    """Return favicon to prevent 404 errors in browser"""
    return {"message": "EVTrack API"}

@app.post(
    "/auth/verify",
    tags=["authentication"],
    summary="Verify authentication",
    description="Verify current authentication status and return user info"
)
async def verify_authentication(auth_data: dict = Depends(verify_auth)):
    """Verify authentication for Google Apps Script"""
    return {
        "authenticated": True,
        "auth_type": auth_data.get("auth_type", "unknown"),
        "username": auth_data.get("username", "unknown"),
        "scopes": auth_data.get("scopes", []),
        "expires_at": auth_data.get("expires_at"),
        "api_version": "2.0.0"
    }

# Google Sheets Integration Endpoints
@app.post(
    "/sheets/visitors/create",
    tags=["google-integration"],
    summary="Create visitor from Google Sheets data",
    description="Create a new visitor in EVTrack from Google Sheets row data"
)
async def create_visitor_from_sheets(request: Request, auth_data: dict = Depends(verify_auth)):
    """Create visitor from Google Sheets data"""
    try:
        json_data = await request.json()
        
        # Extract visitor data from sheets format
        visitor_data = {
            'first_name': json_data.get('firstName', ''),
            'last_name': json_data.get('lastName', ''),
            'email': json_data.get('email', ''),
            'mobile': json_data.get('mobile', ''),
            'company': json_data.get('company', ''),
            'reason_for_visit': json_data.get('reasonForVisit', ''),
            'comments': json_data.get('comments', '')
        }
        
        # Use existing visitor creation logic
        driver = get_driver()
        login = EvTrackLogin(driver)
        await login.login(EVTRACK_EMAIL, EVTRACK_PASSWORD)
        
        visitor_automation = VisitorAutomation(driver)
        result = await visitor_automation.create_update_visitor(visitor_data)
        
        return {
            "success": True,
            "visitor_id": result.get("visitor_id"),
            "message": "Visitor created from Google Sheets data",
            "source": "google_sheets"
        }
        
    except Exception as e:
        logger.error(f"Failed to create visitor from sheets: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'driver' in locals():
            driver.quit()

@app.post(
    "/sheets/visitors/update",
    tags=["google-integration"],
    summary="Update visitor from Google Sheets data",
    description="Update existing visitor in EVTrack from Google Sheets row data"
)
async def update_visitor_from_sheets(request: Request, auth_data: dict = Depends(verify_auth)):
    """Update visitor from Google Sheets data"""
    try:
        json_data = await request.json()
        
        search_term = json_data.get('searchTerm')
        if not search_term:
            raise HTTPException(status_code=400, detail="searchTerm is required")
        
        # Extract visitor data from sheets format
        visitor_data = {}
        field_mapping = {
            'firstName': 'first_name',
            'lastName': 'last_name',
            'email': 'email',
            'mobile': 'mobile',
            'company': 'company',
            'reasonForVisit': 'reason_for_visit',
            'comments': 'comments'
        }
        
        for sheets_field, evtrack_field in field_mapping.items():
            if sheets_field in json_data and json_data[sheets_field]:
                visitor_data[evtrack_field] = json_data[sheets_field]
        
        # Use existing visitor update logic
        driver = get_driver()
        login = EvTrackLogin(driver)
        await login.login(EVTRACK_EMAIL, EVTRACK_PASSWORD)
        
        from automation.visitor_create_update import VisitorCreateUpdateAutomation
        visitor_automation = VisitorCreateUpdateAutomation(driver)
        result = await visitor_automation.update_visitor_profile(search_term, visitor_data, {})
        
        return {
            "success": True,
            "message": result['message'],
            "updated_fields": result['updated_fields'],
            "source": "google_sheets"
        }
        
    except Exception as e:
        logger.error(f"Failed to update visitor from sheets: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'driver' in locals():
            driver.quit()

# Google Drive Integration Endpoints
@app.post(
    "/drive/photos/process",
    tags=["google-integration"],
    summary="Process photos from Google Drive",
    description="Process visitor photos stored in Google Drive and attach to EVTrack profile"
)
async def process_drive_photos(request: Request, auth_data: dict = Depends(verify_auth)):
    """Process photos from Google Drive for visitor profiles"""
    try:
        json_data = await request.json()
        
        visitor_search = json_data.get('visitorSearch')
        drive_photo_url = json_data.get('drivePhotoUrl')
        photo_type = json_data.get('photoType', 'photo')  # photo, signature, id_document
        
        if not visitor_search or not drive_photo_url:
            raise HTTPException(status_code=400, detail="visitorSearch and drivePhotoUrl are required")
        
        # TODO: Implement Google Drive photo download and processing
        # This would involve:
        # 1. Download photo from Google Drive URL
        # 2. Convert to appropriate format
        # 3. Upload to visitor profile using existing automation
        
        return {
            "success": True,
            "message": f"Photo processing initiated for {photo_type}",
            "visitor_search": visitor_search,
            "photo_url": drive_photo_url,
            "photo_type": photo_type
        }
        
    except Exception as e:
        logger.error(f"Failed to process drive photos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get(
    "/sheets/template",
    tags=["google-integration"],
    summary="Get Google Sheets template",
    description="Get the recommended column structure for Google Sheets integration"
)
async def get_sheets_template(auth_data: dict = Depends(verify_auth)):
    """Get Google Sheets template structure for EVTrack integration"""
    return {
        "template": {
            "columns": [
                "firstName",
                "lastName", 
                "email",
                "mobile",
                "company",
                "reasonForVisit",
                "comments",
                "status",
                "searchTerm",
                "lastUpdated"
            ],
            "sample_data": {
                "firstName": "John",
                "lastName": "Doe",
                "email": "john.doe@example.com",
                "mobile": "+1 555-123-4567",
                "company": "Example Corp",
                "reasonForVisit": "Business Meeting",
                "comments": "VIP guest",
                "status": "Pending",
                "searchTerm": "John Doe",
                "lastUpdated": "2025-08-18"
            }
        },
        "instructions": "Create a Google Sheet with these columns to integrate with EVTrack API",
        "api_endpoints": {
            "create_visitor": "/sheets/visitors/create",
            "update_visitor": "/sheets/visitors/update",
            "process_photos": "/drive/photos/process"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
