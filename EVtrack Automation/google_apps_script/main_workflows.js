/**
 * Main Workflow Functions for EVTrack Google Sheets Integration
 * High-level functions that combine all the component scripts
 */

/**
 * Main function to process a Google Sheet for bulk visitor creation
 * This is the primary function users will call
 */
function processVisitorSheet() {
  console.log(' Starting EVTrack visitor processing from Google Sheet');
  
  try {
    // Get the active spreadsheet
    const sheet = SpreadsheetApp.getActiveSheet();
    const sheetData = sheet.getDataRange().getValues();
    
    if (sheetData.length < 2) {
      throw new Error('Sheet must have at least 2 rows (headers + data)');
    }
    
    // Validate sheet structure
    const validation = validateSheetStructure(sheetData, ['first_name', 'last_name', 'mobile']);
    if (!validation.valid) {
      throw new Error(`Sheet validation failed: ${validation.error}`);
    }
    
    console.log(` Processing ${validation.rowCount} visitors from sheet`);
    
    // Test API connection first
    const connectionTest = testAPIConnection();
    if (!connectionTest.success) {
      throw new Error(`API connection failed: ${connectionTest.message}`);
    }
    
    console.log(' API connection verified');
    
    // Process all visitors
    const results = processVisitorsFromSheet(sheetData);
    
    if (!results.success) {
      throw new Error(`Processing failed: ${results.error}`);
    }
    
    // Update sheet with results
    updateSheetWithResults(sheet, results);
    
    // Show summary
    showProcessingSummary(results);
    
    console.log(' Processing complete!');
    
    return results;
    
  } catch (error) {
    console.error(' Processing failed:', error);
    SpreadsheetApp.getUi().alert('Error', `Processing failed: ${error.message}`, SpreadsheetApp.getUi().Button.OK);
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * Process visitor updates from Google Sheet
 */
function updateVisitorSheet() {
  console.log(' Starting EVTrack visitor updates from Google Sheet');
  
  try {
    const sheet = SpreadsheetApp.getActiveSheet();
    const sheetData = sheet.getDataRange().getValues();
    
    // Get search column from user
    const ui = SpreadsheetApp.getUi();
    const response = ui.prompt(
      'Update Visitors',
      'Which column should be used to search for existing visitors? (e.g., email, mobile)',
      ui.Button.OK_CANCEL
    );
    
    if (response.getSelectedButton() !== ui.Button.OK) {
      return { success: false, error: 'Cancelled by user' };
    }
    
    const searchColumn = response.getResponseText().trim();
    if (!searchColumn) {
      throw new Error('Search column is required');
    }
    
    // Test API connection
    const connectionTest = testAPIConnection();
    if (!connectionTest.success) {
      throw new Error(`API connection failed: ${connectionTest.message}`);
    }
    
    // Process updates
    const results = updateVisitorsFromSheet(sheetData, searchColumn);
    
    if (!results.success) {
      throw new Error(`Update failed: ${results.error}`);
    }
    
    // Update sheet with results
    updateSheetWithResults(sheet, results);
    
    // Show summary
    showProcessingSummary(results);
    
    console.log(' Updates complete!');
    
    return results;
    
  } catch (error) {
    console.error(' Update failed:', error);
    SpreadsheetApp.getUi().alert('Error', `Update failed: ${error.message}`, SpreadsheetApp.getUi().Button.OK);
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * Process Google Drive photos for visitors
 */
function processPhotosFromDrive() {
  console.log(' Starting photo processing from Google Drive');
  
  try {
    const sheet = SpreadsheetApp.getActiveSheet();
    const sheetData = sheet.getDataRange().getValues();
    
    // Process photos
    const results = batchProcessDriveFiles(sheetData, 'photo_drive_id', 'email');
    
    if (!results.success) {
      throw new Error(`Photo processing failed: ${results.error}`);
    }
    
    // Update sheet with photo processing results
    updateSheetWithPhotoResults(sheet, results);
    
    // Show summary
    showProcessingSummary(results);
    
    console.log(' Photo processing complete!');
    
    return results;
    
  } catch (error) {
    console.error(' Photo processing failed:', error);
    SpreadsheetApp.getUi().alert('Error', `Photo processing failed: ${error.message}`, SpreadsheetApp.getUi().Button.OK);
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * Update sheet with processing results
 */
function updateSheetWithResults(sheet, results) {
  console.log(' Updating sheet with results...');
  
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  
  // Find or create status column
  let statusColumn = headers.indexOf('status') + 1;
  if (statusColumn === 0) {
    statusColumn = sheet.getLastColumn() + 1;
    sheet.getRange(1, statusColumn).setValue('status');
  }
  
  // Find or create message column
  let messageColumn = headers.indexOf('message') + 1;
  if (messageColumn === 0) {
    messageColumn = sheet.getLastColumn() + 1;
    sheet.getRange(1, messageColumn).setValue('message');
  }
  
  // Update each row with results
  for (const result of results.results) {
    const rowNumber = result.row;
    const status = result.success ? ' Success' : ' Failed';
    const message = result.message || '';
    
    sheet.getRange(rowNumber, statusColumn).setValue(status);
    sheet.getRange(rowNumber, messageColumn).setValue(message);
    
    // Color code the row
    const rowRange = sheet.getRange(rowNumber, 1, 1, sheet.getLastColumn());
    if (result.success) {
      rowRange.setBackground('#d4edda'); // Light green
    } else {
      rowRange.setBackground('#f8d7da'); // Light red
    }
  }
  
  console.log(' Sheet updated with results');
}

/**
 * Update sheet with photo processing results
 */
function updateSheetWithPhotoResults(sheet, results) {
  console.log(' Updating sheet with photo results...');
  
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  
  // Find or create photo status column
  let photoStatusColumn = headers.indexOf('photo_status') + 1;
  if (photoStatusColumn === 0) {
    photoStatusColumn = sheet.getLastColumn() + 1;
    sheet.getRange(1, photoStatusColumn).setValue('photo_status');
  }
  
  // Update each row with photo results
  for (const result of results.results) {
    const rowNumber = result.row;
    const status = result.success ? ' Ready' : ' Failed';
    
    sheet.getRange(rowNumber, photoStatusColumn).setValue(status);
  }
  
  console.log(' Sheet updated with photo results');
}

/**
 * Show processing summary to user
 */
function showProcessingSummary(results) {
  const ui = SpreadsheetApp.getUi();
  
  const summary = `
Processing Complete!

 Total Processed: ${results.processed}
 Successful: ${results.successCount}
 Failed: ${results.failureCount}

Check the 'status' and 'message' columns for details.
  `;
  
  ui.alert('Processing Summary', summary, ui.Button.OK);
}

/**
 * Setup function - run this first to configure the API
 */
function setupEVTrackIntegration() {
  console.log(' Setting up EVTrack integration...');
  
  const ui = SpreadsheetApp.getUi();
  
  // Get API configuration from user
  const urlResponse = ui.prompt(
    'Setup EVTrack API',
    'Enter your EVTrack API base URL:\n(e.g., https://your-api.amazonaws.com)',
    ui.Button.OK_CANCEL
  );
  
  if (urlResponse.getSelectedButton() !== ui.Button.OK) {
    return;
  }
  
  const keyResponse = ui.prompt(
    'Setup EVTrack API',
    'Enter your API key:\n(e.g., evtrack)',
    ui.Button.OK_CANCEL
  );
  
  if (keyResponse.getSelectedButton() !== ui.Button.OK) {
    return;
  }
  
  const baseUrl = urlResponse.getResponseText().trim();
  const apiKey = keyResponse.getResponseText().trim();
  
  // Update configuration
  const setupResult = setupAPIConfig(baseUrl, apiKey);
  
  if (setupResult.success) {
    ui.alert('Setup Complete', 'EVTrack API configured successfully!\nYou can now process visitor data.', ui.Button.OK);
  } else {
    ui.alert('Setup Failed', `Configuration failed: ${setupResult.message}`, ui.Button.OK);
  }
}

/**
 * Create menu in Google Sheets for easy access
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  
  ui.createMenu('EVTrack Automation')
    .addItem('Setup API Connection', 'setupEVTrackIntegration')
    .addSeparator()
    .addItem('Process New Visitors', 'processVisitorSheet')
    .addItem('Update Existing Visitors', 'updateVisitorSheet')
    .addItem('Process Drive Photos', 'processPhotosFromDrive')
    .addSeparator()
    .addItem('Test API Connection', 'testAPIConnection')
    .addToUi();
}
