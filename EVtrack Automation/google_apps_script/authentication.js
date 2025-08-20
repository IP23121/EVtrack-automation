/**
 * EVTrack API Authentication Helper for Google Apps Script
 * Handles authentication with the EVTrack automation API
 */

// Configuration - Production deployment ready
const CONFIG = {
  // Production API URL (update after AWS Lambda deployment)
  API_BASE_URL: 'https://your-lambda-url.amazonaws.com',  // AWS Lambda API Gateway URL
  
  API_KEY: 'evtrack',  // API key for authentication
  GOOGLE_OAUTH_CLIENT_ID: 'your-google-client-id.apps.googleusercontent.com'  // For enhanced security (future)
};

/**
 * Make authenticated API request to EVTrack API
 * @param {string} endpoint - API endpoint path (e.g., '/visitors')
 * @param {string} method - HTTP method ('GET', 'POST', 'PUT', 'DELETE')
 * @param {Object} data - Request payload for POST/PUT requests
 * @param {Object} options - Additional options (headers, etc.)
 * @returns {Object} API response
 */
function makeAuthenticatedRequest(endpoint, method = 'GET', data = null, options = {}) {
  try {
    const url = CONFIG.API_BASE_URL + endpoint;
    
    // Set up headers with authentication
    const headers = {
      'X-API-Key': CONFIG.API_KEY,  // Use X-API-Key header
      'Content-Type': 'application/json',
      ...options.headers
    };
    
    // Configure request options
    const requestOptions = {
      method: method,
      headers: headers,
      muteHttpExceptions: true  // Don't throw on HTTP errors
    };
    
    // Add payload for POST/PUT requests
    if (data && (method === 'POST' || method === 'PUT')) {
      requestOptions.payload = JSON.stringify(data);
    }
    
    console.log(`Making ${method} request to: ${url}`);
    
    // Make the request
    const response = UrlFetchApp.fetch(url, requestOptions);
    const responseCode = response.getResponseCode();
    const responseText = response.getContentText();
    
    console.log(`Response code: ${responseCode}`);
    
    // Parse response
    let responseData;
    try {
      responseData = JSON.parse(responseText);
    } catch (e) {
      responseData = { error: 'Invalid JSON response', raw: responseText };
    }
    
    // Handle different response codes
    if (responseCode >= 200 && responseCode < 300) {
      return {
        success: true,
        data: responseData,
        status: responseCode
      };
    } else {
      return {
        success: false,
        error: responseData.detail || responseData.error || 'API request failed',
        status: responseCode,
        data: responseData
      };
    }
    
  } catch (error) {
    console.error('API request error:', error);
    return {
      success: false,
      error: `Request failed: ${error.message}`,
      status: 0
    };
  }
}

/**
 * Test API connection and authentication
 * @returns {Object} Test result
 */
function testAPIConnection() {
  console.log('Testing API connection...');
  
  // Test with health endpoint
  const result = makeAuthenticatedRequest('/health', 'GET');
  
  if (result.success) {
    console.log('✅ API connection successful');
    console.log('API Status:', result.data);
    return {
      success: true,
      message: 'API connection successful',
      apiStatus: result.data
    };
  } else {
    console.error('❌ API connection failed');
    console.error('Error:', result.error);
    return {
      success: false,
      message: `API connection failed: ${result.error}`,
      status: result.status
    };
  }
}

/**
 * Get current authentication status
 * @returns {Object} Authentication verification result
 */
function verifyAuthentication() {
  console.log('Verifying authentication...');
  
  const result = makeAuthenticatedRequest('/auth/verify', 'GET');
  
  if (result.success) {
    console.log('✅ Authentication verified');
    console.log('User info:', result.data);
    return {
      success: true,
      message: 'Authentication verified',
      userInfo: result.data
    };
  } else {
    console.error('❌ Authentication failed');
    console.error('Error:', result.error);
    return {
      success: false,
      message: `Authentication failed: ${result.error}`,
      status: result.status
    };
  }
}

/**
 * Handle API errors with user-friendly messages
 * @param {Object} apiResponse - Response from makeAuthenticatedRequest
 * @returns {string} User-friendly error message
 */
function handleAPIError(apiResponse) {
  if (apiResponse.success) {
    return null;  // No error
  }
  
  switch (apiResponse.status) {
    case 401:
      return 'Authentication failed. Please check your API key.';
    case 403:
      return 'Access denied. Your API key may not have the required permissions.';
    case 404:
      return 'API endpoint not found. Please check the URL configuration.';
    case 500:
      return 'Server error. Please try again later or contact support.';
    default:
      return `API Error (${apiResponse.status}): ${apiResponse.error}`;
  }
}

/**
 * Set up API configuration
 * Call this function first to configure your API details
 * @param {string} baseUrl - Your API base URL
 * @param {string} apiKey - Your API key
 */
function setupAPIConfig(baseUrl, apiKey) {
  CONFIG.API_BASE_URL = baseUrl;
  CONFIG.API_KEY = apiKey;
  
  console.log('API configuration updated');
  console.log('Base URL:', CONFIG.API_BASE_URL);
  console.log('API Key:', CONFIG.API_KEY.substring(0, 10) + '...');
  
  // Test the new configuration
  return testAPIConnection();
}

/**
 * Get API configuration for debugging
 * @returns {Object} Current configuration (with masked API key)
 */
function getAPIConfig() {
  return {
    baseUrl: CONFIG.API_BASE_URL,
    apiKeyPreview: CONFIG.API_KEY.substring(0, 10) + '...',
    hasApiKey: !!CONFIG.API_KEY
  };
}
