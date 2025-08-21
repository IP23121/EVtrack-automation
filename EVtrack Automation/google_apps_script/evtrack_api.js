/**
 * EVTrack API Wrapper Functions for Google Apps Script
 * Main API interaction functions for visitor, vehicle, and credential management
 */

/**
 * Search for visitors in EVTrack
 * @param {string} searchTerm - Search term (name, email, etc.)
 * @returns {Object} Search results
 */
function searchVisitors(searchTerm) {
  console.log(`Searching for visitors: ${searchTerm}`);
  
  const endpoint = `/visitors?search=${encodeURIComponent(searchTerm)}`;
  const result = makeAuthenticatedRequest(endpoint, 'GET');
  
  if (result.success) {
    console.log(`Found ${result.data.visitors.length} visitors`);
    return {
      success: true,
      visitors: result.data.visitors,
      count: result.data.visitors.length
    };
  } else {
    const error = handleAPIError(result);
    console.error('Search failed:', error);
    return {
      success: false,
      error: error,
      visitors: []
    };
  }
}

/**
 * Create a new visitor in EVTrack
 * @param {Object} visitorData - Visitor information
 * @returns {Object} Creation result
 */
function createVisitor(visitorData) {
  console.log('Creating visitor:', visitorData.first_name, visitorData.last_name);
  
  const result = makeAuthenticatedRequest('/visitors', 'POST', visitorData);
  
  if (result.success) {
    console.log(' Visitor created successfully');
    return {
      success: true,
      message: 'Visitor created successfully',
      visitorId: result.data.visitor_id
    };
  } else {
    const error = handleAPIError(result);
    console.error(' Visitor creation failed:', error);
    return {
      success: false,
      error: error
    };
  }
}

/**
 * Update an existing visitor
 * @param {string} searchTerm - Term to find the visitor
 * @param {Object} updateData - Data to update
 * @returns {Object} Update result
 */
function updateVisitor(searchTerm, updateData) {
  console.log(`Updating visitor: ${searchTerm}`);
  
  const payload = {
    search_term: searchTerm,
    ...updateData
  };
  
  const result = makeAuthenticatedRequest('/visitors/update', 'POST', payload);
  
  if (result.success) {
    console.log(' Visitor updated successfully');
    return {
      success: true,
      message: result.data.message,
      updatedFields: result.data.updated_fields
    };
  } else {
    const error = handleAPIError(result);
    console.error(' Visitor update failed:', error);
    return {
      success: false,
      error: error
    };
  }
}

/**
 * Get detailed visitor profile
 * @param {string} searchTerm - Term to find the visitor
 * @returns {Object} Visitor profile data
 */
function getVisitorProfile(searchTerm) {
  console.log(`Getting visitor profile: ${searchTerm}`);
  
  const payload = { search_term: searchTerm };
  const result = makeAuthenticatedRequest('/visitors/profile', 'POST', payload);
  
  if (result.success) {
    console.log(' Visitor profile retrieved');
    return {
      success: true,
      profile: result.data.profile,
      visitorUuid: result.data.visitor_uuid,
      visitorName: result.data.visitor_name
    };
  } else {
    const error = handleAPIError(result);
    console.error(' Failed to get visitor profile:', error);
    return {
      success: false,
      error: error
    };
  }
}

/**
 * Add a vehicle to a visitor
 * @param {string} searchTerm - Term to find the visitor
 * @param {Object} vehicleData - Vehicle information
 * @returns {Object} Addition result
 */
function addVehicle(searchTerm, vehicleData) {
  console.log(`Adding vehicle to visitor: ${searchTerm}`);
  
  const payload = {
    search_term: searchTerm,
    ...vehicleData
  };
  
  const result = makeAuthenticatedRequest('/vehicles/add', 'POST', payload);
  
  if (result.success) {
    console.log(' Vehicle added successfully');
    return {
      success: true,
      message: result.data.message
    };
  } else {
    const error = handleAPIError(result);
    console.error(' Vehicle addition failed:', error);
    return {
      success: false,
      error: error
    };
  }
}

/**
 * Update vehicle information
 * @param {string} searchTerm - Term to find the vehicle
 * @param {Object} vehicleData - Vehicle data to update
 * @returns {Object} Update result
 */
function updateVehicle(searchTerm, vehicleData) {
  console.log(`Updating vehicle: ${searchTerm}`);
  
  const payload = {
    search_term: searchTerm,
    ...vehicleData
  };
  
  const result = makeAuthenticatedRequest('/vehicles/update', 'POST', payload);
  
  if (result.success) {
    console.log(' Vehicle updated successfully');
    return {
      success: true,
      message: result.data.message,
      updatedFields: result.data.updated_fields
    };
  } else {
    const error = handleAPIError(result);
    console.error(' Vehicle update failed:', error);
    return {
      success: false,
      error: error
    };
  }
}

/**
 * Add credentials to a visitor
 * @param {string} searchTerm - Term to find the visitor
 * @param {Object} credentialData - Credential information
 * @returns {Object} Addition result
 */
function addCredential(searchTerm, credentialData) {
  console.log(`Adding credential to visitor: ${searchTerm}`);
  
  const payload = {
    search_term: searchTerm,
    ...credentialData
  };
  
  const result = makeAuthenticatedRequest('/credentials/add', 'POST', payload);
  
  if (result.success) {
    console.log(' Credential added successfully');
    return {
      success: true,
      message: 'Credential added successfully',
      visitorUuid: result.data.visitor_uuid
    };
  } else {
    const error = handleAPIError(result);
    console.error(' Credential addition failed:', error);
    return {
      success: false,
      error: error
    };
  }
}

/**
 * Send invitation to a visitor
 * @param {string} searchTerm - Term to find the visitor
 * @param {Object} invitationData - Invitation settings
 * @returns {Object} Invitation result
 */
function inviteVisitor(searchTerm, invitationData) {
  console.log(`Sending invitation to visitor: ${searchTerm}`);
  
  const payload = {
    search_term: searchTerm,
    ...invitationData
  };
  
  const result = makeAuthenticatedRequest('/visitors/invite', 'POST', payload);
  
  if (result.success) {
    console.log(' Invitation sent successfully');
    return {
      success: true,
      message: result.data.message,
      visitorUuid: result.data.visitor_uuid,
      visitorName: result.data.visitor_name
    };
  } else {
    const error = handleAPIError(result);
    console.error(' Invitation failed:', error);
    return {
      success: false,
      error: error
    };
  }
}

/**
 * Generate visitor badge
 * @param {string} searchTerm - Term to find the visitor
 * @returns {Object} Badge generation result with file data
 */
function generateVisitorBadge(searchTerm) {
  console.log(`Generating badge for visitor: ${searchTerm}`);
  
  const payload = { search: searchTerm };
  const result = makeAuthenticatedRequest('/visitors/badge', 'POST', payload);
  
  if (result.success) {
    console.log(' Badge generated successfully');
    
    // The API returns the badge file directly, so we need to handle binary data
    // In Apps Script, this would be handled differently for file downloads
    return {
      success: true,
      message: 'Badge generated successfully',
      // Note: Actual file handling would need additional implementation
      badgeReady: true
    };
  } else {
    const error = handleAPIError(result);
    console.error(' Badge generation failed:', error);
    return {
      success: false,
      error: error
    };
  }
}

/**
 * Test EVTrack login functionality
 * @returns {Object} Login test result
 */
function testEVTrackLogin() {
  console.log('Testing EVTrack login...');
  
  const result = makeAuthenticatedRequest('/login', 'POST');
  
  if (result.success) {
    console.log(' EVTrack login test successful');
    return {
      success: true,
      message: result.data.message,
      user: result.data.user,
      authType: result.data.auth_type
    };
  } else {
    const error = handleAPIError(result);
    console.error(' EVTrack login test failed:', error);
    return {
      success: false,
      error: error
    };
  }
}
