/**
 * Simple API Client for EVTrack API
 * 
 * Usage:
 * 1. Set Script Properties: BASE_URL, API_KEY
 * 2. Call functions like: callApi('/visitors', 'POST', visitorData)
 */

/**
 * Make an API call with API key authentication
 * @param {string} path - API endpoint path (e.g., '/visitors')
 * @param {string} method - HTTP method (GET, POST, PUT, DELETE)
 * @param {Object} payload - Request body object (optional)
 * @return {Object} Response from API
 */
function callApi(path, method = 'GET', payload = null) {
  const props = PropertiesService.getScriptProperties();
  const baseUrl = props.getProperty('BASE_URL');
  const apiKey = props.getProperty('API_KEY');
  
  if (!baseUrl || !apiKey) {
    throw new Error('BASE_URL and API_KEY must be set in Script Properties');
  }
  
  const options = {
    method: method.toUpperCase(),
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': apiKey
    },
    muteHttpExceptions: true
  };
  
  if (payload && (method.toUpperCase() === 'POST' || method.toUpperCase() === 'PUT')) {
    options.payload = JSON.stringify(payload);
  }
  
  try {
    const response = UrlFetchApp.fetch(baseUrl + path, options);
    const responseCode = response.getResponseCode();
    const responseText = response.getContentText();
    
    if (responseCode >= 200 && responseCode < 300) {
      try {
        return JSON.parse(responseText);
      } catch (e) {
        return { success: true, data: responseText };
      }
    } else {
      throw new Error(`API Error ${responseCode}: ${responseText}`);
    }
  } catch (error) {
    Logger.log(`API call failed: ${error.message}`);
    throw error;
  }
}

/**
 * Test API connectivity
 */
function testApiConnection() {
  try {
    const response = callApi('/health', 'GET');
    Logger.log('API connection successful:', response);
    return response;
  } catch (error) {
    Logger.log('API connection failed:', error.message);
    throw error;
  }
}

/**
 * Setup Script Properties (run this once to configure)
 * Replace with your actual values
 */
function setupScriptProperties() {
  const properties = {
    'BASE_URL': 'https://your-api-gateway-url.amazonaws.com/prod',  // Replace with deployed URL
    'API_KEY': 'evtrack'  // Replace with your API key
  };
  
  PropertiesService.getScriptProperties().setProperties(properties);
  Logger.log('Script properties configured');
}
