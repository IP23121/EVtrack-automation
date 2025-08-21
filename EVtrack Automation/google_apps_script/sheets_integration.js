/**
 * Google Sheets Integration Functions for EVTrack API
 * Specialized functions for processing data from Google Sheets
 */

/**
 * Process visitor data from a Google Sheets row
 * @param {Array} rowData - Array of cell values from a sheet row
 * @param {Array} headers - Array of column headers
 * @returns {Object} Formatted visitor data
 */
function formatVisitorFromSheet(rowData, headers) {
  const visitor = {};
  
  // Create mapping from headers to row data
  for (let i = 0; i < headers.length && i < rowData.length; i++) {
    const header = headers[i].toLowerCase().trim();
    const value = rowData[i] ? rowData[i].toString().trim() : '';
    
    // Map common column names to API fields
    switch (header) {
      case 'first name':
      case 'firstname':
      case 'first_name':
        visitor.first_name = value;
        break;
      case 'last name':
      case 'lastname':
      case 'last_name':
        visitor.last_name = value;
        break;
      case 'email':
      case 'email address':
        visitor.email = value;
        break;
      case 'phone':
      case 'phone number':
      case 'mobile':
        visitor.phone = value;
        break;
      case 'company':
      case 'organization':
        visitor.company = value;
        break;
      case 'purpose':
      case 'visit purpose':
        visitor.purpose = value;
        break;
      case 'visit date':
      case 'date':
        visitor.visit_date = value;
        break;
      case 'visit time':
      case 'time':
        visitor.visit_time = value;
        break;
      case 'notes':
      case 'comments':
        visitor.notes = value;
        break;
      case 'license plate':
      case 'license_plate':
      case 'plate':
        visitor.license_plate = value;
        break;
      case 'vehicle make':
      case 'make':
        visitor.vehicle_make = value;
        break;
      case 'vehicle model':
      case 'model':
        visitor.vehicle_model = value;
        break;
      case 'vehicle color':
      case 'color':
        visitor.vehicle_color = value;
        break;
    }
  }
  
  return visitor;
}

/**
 * Process multiple visitors from a Google Sheet
 * @param {Array} sheetData - 2D array with headers in first row
 * @param {number} startRow - Row to start processing (1-based, default 2)
 * @param {number} endRow - Row to end processing (optional)
 * @returns {Object} Processing results
 */
function processVisitorsFromSheet(sheetData, startRow = 2, endRow = null) {
  console.log('Processing visitors from Google Sheet');
  
  if (!sheetData || sheetData.length < 2) {
    return {
      success: false,
      error: 'Sheet must have at least 2 rows (headers + data)',
      processed: 0,
      results: []
    };
  }
  
  const headers = sheetData[0];
  const results = [];
  const errors = [];
  
  // Determine end row
  const lastRow = endRow || sheetData.length;
  
  console.log(`Processing rows ${startRow} to ${lastRow}`);
  
  for (let i = startRow - 1; i < lastRow && i < sheetData.length; i++) {
    const rowNumber = i + 1;
    const rowData = sheetData[i];
    
    try {
      console.log(`Processing row ${rowNumber}`);
      
      // Format visitor data
      const visitorData = formatVisitorFromSheet(rowData, headers);
      
      // Validate required fields
      if (!visitorData.first_name || !visitorData.last_name) {
        errors.push({
          row: rowNumber,
          error: 'Missing required fields: first_name, last_name'
        });
        continue;
      }
      
      // Create visitor
      const result = createVisitor(visitorData);
      
      results.push({
        row: rowNumber,
        visitorName: `${visitorData.first_name} ${visitorData.last_name}`,
        success: result.success,
        message: result.success ? result.message : result.error,
        visitorId: result.visitorId || null
      });
      
      // Add small delay to avoid overwhelming the API
      Utilities.sleep(500);
      
    } catch (error) {
      console.error(`Error processing row ${rowNumber}:`, error);
      errors.push({
        row: rowNumber,
        error: error.toString()
      });
    }
  }
  
  const successCount = results.filter(r => r.success).length;
  const failureCount = results.filter(r => !r.success).length;
  
  console.log(` Processing complete: ${successCount} success, ${failureCount} failures`);
  
  return {
    success: true,
    processed: results.length,
    successCount: successCount,
    failureCount: failureCount,
    results: results,
    errors: errors
  };
}

/**
 * Update visitors from a Google Sheet
 * @param {Array} sheetData - 2D array with headers in first row
 * @param {string} searchColumn - Column name to use for finding existing visitors
 * @param {number} startRow - Row to start processing (1-based, default 2)
 * @param {number} endRow - Row to end processing (optional)
 * @returns {Object} Update results
 */
function updateVisitorsFromSheet(sheetData, searchColumn = 'email', startRow = 2, endRow = null) {
  console.log(`Updating visitors from Google Sheet using ${searchColumn} as search key`);
  
  if (!sheetData || sheetData.length < 2) {
    return {
      success: false,
      error: 'Sheet must have at least 2 rows (headers + data)',
      processed: 0,
      results: []
    };
  }
  
  const headers = sheetData[0];
  const results = [];
  const errors = [];
  
  // Find search column index
  const searchColumnIndex = headers.findIndex(h => 
    h.toLowerCase().trim() === searchColumn.toLowerCase()
  );
  
  if (searchColumnIndex === -1) {
    return {
      success: false,
      error: `Search column '${searchColumn}' not found in headers`,
      processed: 0,
      results: []
    };
  }
  
  // Determine end row
  const lastRow = endRow || sheetData.length;
  
  console.log(`Updating rows ${startRow} to ${lastRow}`);
  
  for (let i = startRow - 1; i < lastRow && i < sheetData.length; i++) {
    const rowNumber = i + 1;
    const rowData = sheetData[i];
    
    try {
      console.log(`Updating row ${rowNumber}`);
      
      // Get search term
      const searchTerm = rowData[searchColumnIndex];
      if (!searchTerm) {
        errors.push({
          row: rowNumber,
          error: `No value in search column '${searchColumn}'`
        });
        continue;
      }
      
      // Format visitor data (excluding search field to avoid conflicts)
      const visitorData = formatVisitorFromSheet(rowData, headers);
      
      // Update visitor
      const result = updateVisitor(searchTerm, visitorData);
      
      results.push({
        row: rowNumber,
        searchTerm: searchTerm,
        success: result.success,
        message: result.success ? result.message : result.error,
        updatedFields: result.updatedFields || null
      });
      
      // Add small delay
      Utilities.sleep(500);
      
    } catch (error) {
      console.error(`Error updating row ${rowNumber}:`, error);
      errors.push({
        row: rowNumber,
        error: error.toString()
      });
    }
  }
  
  const successCount = results.filter(r => r.success).length;
  const failureCount = results.filter(r => !r.success).length;
  
  console.log(` Update complete: ${successCount} success, ${failureCount} failures`);
  
  return {
    success: true,
    processed: results.length,
    successCount: successCount,
    failureCount: failureCount,
    results: results,
    errors: errors
  };
}

/**
 * Get visitor data and write to Google Sheet
 * @param {Array} searchTerms - Array of search terms to look up
 * @returns {Array} 2D array suitable for writing to a sheet
 */
function getVisitorsForSheet(searchTerms) {
  console.log(`Retrieving ${searchTerms.length} visitors for sheet export`);
  
  const results = [];
  const headers = [
    'Search Term', 'Status', 'First Name', 'Last Name', 'Email', 
    'Phone', 'Company', 'Visitor ID', 'Error'
  ];
  
  results.push(headers);
  
  for (const searchTerm of searchTerms) {
    try {
      const searchResult = searchVisitors(searchTerm);
      
      if (searchResult.success && searchResult.visitors.length > 0) {
        const visitor = searchResult.visitors[0]; // Take first match
        results.push([
          searchTerm,
          'Found',
          visitor.first_name || '',
          visitor.last_name || '',
          visitor.email || '',
          visitor.phone || '',
          visitor.company || '',
          visitor.visitor_id || '',
          ''
        ]);
      } else {
        results.push([
          searchTerm,
          'Not Found',
          '', '', '', '', '', '',
          searchResult.error || 'No matches found'
        ]);
      }
      
      // Small delay between requests
      Utilities.sleep(300);
      
    } catch (error) {
      console.error(`Error searching for ${searchTerm}:`, error);
      results.push([
        searchTerm,
        'Error',
        '', '', '', '', '', '',
        error.toString()
      ]);
    }
  }
  
  console.log(` Retrieved data for ${results.length - 1} search terms`);
  return results;
}

/**
 * Helper function to validate sheet data structure
 * @param {Array} sheetData - 2D array from Google Sheet
 * @param {Array} requiredColumns - Array of required column names
 * @returns {Object} Validation result
 */
function validateSheetStructure(sheetData, requiredColumns = ['first_name', 'last_name']) {
  if (!sheetData || sheetData.length === 0) {
    return {
      valid: false,
      error: 'Sheet is empty'
    };
  }
  
  if (sheetData.length < 2) {
    return {
      valid: false,
      error: 'Sheet must have at least 2 rows (headers + data)'
    };
  }
  
  const headers = sheetData[0].map(h => h.toLowerCase().trim());
  const missingColumns = [];
  
  for (const required of requiredColumns) {
    const found = headers.some(h => 
      h === required.toLowerCase() || 
      h.replace(/[_\s]/g, '') === required.replace(/[_\s]/g, '')
    );
    
    if (!found) {
      missingColumns.push(required);
    }
  }
  
  if (missingColumns.length > 0) {
    return {
      valid: false,
      error: `Missing required columns: ${missingColumns.join(', ')}`,
      missingColumns: missingColumns,
      availableColumns: headers
    };
  }
  
  return {
    valid: true,
    rowCount: sheetData.length - 1,
    columnCount: headers.length,
    columns: headers
  };
}
