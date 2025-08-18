/**
 * Comprehensive EVTrack Google Apps Script Example
 * This file demonstrates how to use all the EVTrack API functions together
 * with Google Sheets and Google Drive integration
 */

// ===== CONFIGURATION =====
// Set your API configuration in the authentication.js file
// Make sure to set API_BASE_URL and API_KEY there first

/**
 * Example 1: Simple visitor search
 */
function example1_searchVisitors() {
  console.log('=== Example 1: Search Visitors ===');
  
  // Test API connection first
  const connectionTest = testAPIConnection();
  if (!connectionTest.success) {
    console.error('❌ API connection failed:', connectionTest.error);
    return;
  }
  
  // Search for visitors
  const searchResult = searchVisitors('john@example.com');
  
  if (searchResult.success) {
    console.log(`✅ Found ${searchResult.count} visitors`);
    searchResult.visitors.forEach(visitor => {
      console.log(`- ${visitor.first_name} ${visitor.last_name} (${visitor.email})`);
    });
  } else {
    console.error('❌ Search failed:', searchResult.error);
  }
}

/**
 * Example 2: Create a new visitor
 */
function example2_createVisitor() {
  console.log('=== Example 2: Create Visitor ===');
  
  const visitorData = {
    first_name: 'Jane',
    last_name: 'Doe',
    email: 'jane.doe@example.com',
    mobile: '+1 555-123-4567',
    company: 'Example Corp',
    purpose: 'Business Meeting',
    visit_date: '2025-01-20',
    visit_time: '10:00'
  };
  
  const result = createVisitor(visitorData);
  
  if (result.success) {
    console.log('✅ Visitor created successfully');
    console.log('Visitor ID:', result.visitorId);
  } else {
    console.error('❌ Failed to create visitor:', result.error);
  }
}

/**
 * Example 3: Update visitor information
 */
function example3_updateVisitor() {
  console.log('=== Example 3: Update Visitor ===');
  
  const updateData = {
    mobile: '+1 555-987-6543',
    company: 'New Company Ltd',
    notes: 'Updated contact information'
  };
  
  const result = updateVisitor('jane.doe@example.com', updateData);
  
  if (result.success) {
    console.log('✅ Visitor updated successfully');
    console.log('Updated fields:', result.updatedFields);
  } else {
    console.error('❌ Failed to update visitor:', result.error);
  }
}

/**
 * Example 4: Add vehicle to visitor
 */
function example4_addVehicle() {
  console.log('=== Example 4: Add Vehicle ===');
  
  const vehicleData = {
    number_plate: 'ABC123',
    make: 'Toyota',
    model: 'Camry',
    year: 2020,
    colour: 'Blue',
    vin: '1HGBH41JXMN109186'
  };
  
  const result = addVehicle('jane.doe@example.com', vehicleData);
  
  if (result.success) {
    console.log('✅ Vehicle added successfully');
  } else {
    console.error('❌ Failed to add vehicle:', result.error);
  }
}

/**
 * Example 5: Add credentials to visitor
 */
function example5_addCredential() {
  console.log('=== Example 5: Add Credential ===');
  
  const credentialData = {
    reader_type: 'QR_CODE',
    unique_identifier: 'QR123456',
    active_date: '2025-01-20',
    expiry_date: '2025-12-31',
    active_time: '00:00',
    expiry_time: '23:59',
    comments: 'QR code for main entrance'
  };
  
  const result = addCredential('jane.doe@example.com', credentialData);
  
  if (result.success) {
    console.log('✅ Credential added successfully');
  } else {
    console.error('❌ Failed to add credential:', result.error);
  }
}

/**
 * Example 6: Send visitor invitation
 */
function example6_inviteVisitor() {
  console.log('=== Example 6: Invite Visitor ===');
  
  const invitationData = {
    credentialReaderType: 'QR_CODE',
    visitReasonId: '647', // Parent Pickup/Dropoff
    locationId: '2715',   // IO Main Campus
    activateDate: '2025-01-20',
    activateTime: '08:00',
    expiryDate: '2025-01-20',
    expiryTime: '18:00'
  };
  
  const result = inviteVisitor('jane.doe@example.com', invitationData);
  
  if (result.success) {
    console.log('✅ Invitation sent successfully');
    console.log('Visitor:', result.visitorName);
  } else {
    console.error('❌ Failed to send invitation:', result.error);
  }
}

/**
 * Example 7: Process visitors from Google Sheets
 */
function example7_processVisitorsFromSheets() {
  console.log('=== Example 7: Process Visitors from Google Sheets ===');
  
  // Get data from current sheet
  const sheet = SpreadsheetApp.getActiveSheet();
  const range = sheet.getDataRange();
  const values = range.getValues();
  
  if (values.length < 2) {
    console.error('❌ Sheet must have at least 2 rows (headers + data)');
    return;
  }
  
  // Validate sheet structure
  const validation = validateSheetStructure(values, ['first_name', 'last_name']);
  if (!validation.valid) {
    console.error('❌ Sheet validation failed:', validation.error);
    console.log('Available columns:', validation.availableColumns);
    return;
  }
  
  console.log(`✅ Sheet validation passed: ${validation.rowCount} data rows, ${validation.columnCount} columns`);
  
  // Process visitors from sheet (rows 2 onwards)
  const result = processVisitorsFromSheet(values);
  
  if (result.success) {
    console.log(`✅ Processing complete: ${result.successCount} success, ${result.failureCount} failures`);
    
    // Log results
    result.results.forEach(res => {
      if (res.success) {
        console.log(`✅ Row ${res.row}: ${res.visitorName} - ${res.message}`);
      } else {
        console.log(`❌ Row ${res.row}: ${res.visitorName} - ${res.message}`);
      }
    });
    
    // Log errors
    result.errors.forEach(err => {
      console.error(`❌ Row ${err.row}: ${err.error}`);
    });
  } else {
    console.error('❌ Sheet processing failed:', result.error);
  }
}

/**
 * Example 8: Update visitors from Google Sheets
 */
function example8_updateVisitorsFromSheets() {
  console.log('=== Example 8: Update Visitors from Google Sheets ===');
  
  // Get data from current sheet
  const sheet = SpreadsheetApp.getActiveSheet();
  const range = sheet.getDataRange();
  const values = range.getValues();
  
  // Update visitors using email as search key
  const result = updateVisitorsFromSheet(values, 'email');
  
  if (result.success) {
    console.log(`✅ Update complete: ${result.successCount} success, ${result.failureCount} failures`);
    
    // Log results
    result.results.forEach(res => {
      if (res.success) {
        console.log(`✅ Row ${res.row}: ${res.searchTerm} - ${res.message}`);
        if (res.updatedFields) {
          console.log(`   Updated: ${res.updatedFields.join(', ')}`);
        }
      } else {
        console.log(`❌ Row ${res.row}: ${res.searchTerm} - ${res.message}`);
      }
    });
  } else {
    console.error('❌ Update failed:', result.error);
  }
}

/**
 * Example 9: Search visitors and export to new sheet
 */
function example9_searchAndExport() {
  console.log('=== Example 9: Search and Export ===');
  
  // Define search terms
  const searchTerms = [
    'jane.doe@example.com',
    'john@example.com',
    'alice@company.com',
    'bob@organization.org'
  ];
  
  // Get visitor data
  const results = getVisitorsForSheet(searchTerms);
  
  // Create new sheet with results
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const newSheet = spreadsheet.insertSheet('Visitor Search Results');
  
  // Write results to new sheet
  if (results.length > 0) {
    const range = newSheet.getRange(1, 1, results.length, results[0].length);
    range.setValues(results);
    
    // Format headers
    const headerRange = newSheet.getRange(1, 1, 1, results[0].length);
    headerRange.setFontWeight('bold');
    headerRange.setBackground('#e1f5fe');
    
    console.log(`✅ Exported ${results.length - 1} search results to new sheet`);
  } else {
    console.error('❌ No results to export');
  }
}

/**
 * Example 10: Process visitor photos from Google Drive
 */
function example10_processPhotosFromDrive() {
  console.log('=== Example 10: Process Photos from Google Drive ===');
  
  // Example Google Drive photo URLs
  const driveUrls = [
    'https://drive.google.com/file/d/1ABC123_example_file_id/view',
    'https://drive.google.com/open?id=1XYZ789_example_file_id'
  ];
  
  const result = processVisitorPhotosFromDrive(driveUrls, 'jane.doe@example.com');
  
  if (result.success) {
    console.log(`✅ Photo processing complete: ${result.readyCount} ready, ${result.errorCount} errors`);
    
    // Log ready photos
    result.photos.forEach(photo => {
      console.log(`✅ Photo ready: ${photo.fileName} (${photo.sizeKB}KB)`);
    });
    
    // Log errors
    result.errors.forEach(error => {
      console.error(`❌ Photo error: ${error.url} - ${error.error}`);
    });
  } else {
    console.error('❌ Photo processing failed:', result.error);
  }
}

/**
 * Example 11: Batch process Drive files from sheet
 */
function example11_batchProcessDriveFiles() {
  console.log('=== Example 11: Batch Process Drive Files ===');
  
  // Get data from current sheet (assuming columns: email, photo_url)
  const sheet = SpreadsheetApp.getActiveSheet();
  const range = sheet.getDataRange();
  const values = range.getValues();
  
  const result = batchProcessDriveFiles(values, 'photo_url', 'email');
  
  if (result.success) {
    console.log(`✅ Batch processing complete: ${result.successCount} success, ${result.failureCount} failures`);
    
    // Log results
    result.results.forEach(res => {
      if (res.success) {
        console.log(`✅ Row ${res.row}: ${res.searchTerm} - ${res.fileName}`);
      } else {
        console.log(`❌ Row ${res.row}: ${res.searchTerm} - ${res.message}`);
      }
    });
  } else {
    console.error('❌ Batch processing failed:', result.error);
  }
}

/**
 * Example 12: Generate visitor badge
 */
function example12_generateBadge() {
  console.log('=== Example 12: Generate Visitor Badge ===');
  
  const result = generateVisitorBadge('jane.doe@example.com');
  
  if (result.success) {
    console.log('✅ Badge generated successfully');
    console.log('Badge is ready for download');
  } else {
    console.error('❌ Badge generation failed:', result.error);
  }
}

/**
 * Run all examples in sequence
 */
function runAllExamples() {
  console.log('🚀 Running all EVTrack API examples...\n');
  
  try {
    example1_searchVisitors();
    console.log('');
    
    example2_createVisitor();
    console.log('');
    
    // Add delay between operations
    Utilities.sleep(1000);
    
    example3_updateVisitor();
    console.log('');
    
    example4_addVehicle();
    console.log('');
    
    example5_addCredential();
    console.log('');
    
    example6_inviteVisitor();
    console.log('');
    
    example12_generateBadge();
    console.log('');
    
    console.log('✅ All individual examples completed!');
    console.log('');
    console.log('📊 Sheet-based examples require data in the active sheet:');
    console.log('- example7_processVisitorsFromSheets()');
    console.log('- example8_updateVisitorsFromSheets()');
    console.log('- example9_searchAndExport()');
    console.log('- example11_batchProcessDriveFiles()');
    
  } catch (error) {
    console.error('❌ Error running examples:', error);
  }
}

/**
 * Test individual functions - run this first to verify setup
 */
function testBasicFunctions() {
  console.log('🧪 Testing basic EVTrack API functions...\n');
  
  // Test API connection
  console.log('1. Testing API connection...');
  const connectionTest = testAPIConnection();
  if (connectionTest.success) {
    console.log('✅ API connection successful');
  } else {
    console.error('❌ API connection failed:', connectionTest.error);
    return;
  }
  
  // Test EVTrack login
  console.log('2. Testing EVTrack login...');
  const loginTest = testEVTrackLogin();
  if (loginTest.success) {
    console.log('✅ EVTrack login successful');
    console.log('User:', loginTest.user);
  } else {
    console.error('❌ EVTrack login failed:', loginTest.error);
    return;
  }
  
  // Test visitor search
  console.log('3. Testing visitor search...');
  const searchTest = searchVisitors('test@example.com');
  console.log(`Search result: ${searchTest.success ? 'Success' : 'Failed'}`);
  if (!searchTest.success) {
    console.log('Search error:', searchTest.error);
  }
  
  console.log('\n✅ Basic function tests completed!');
  console.log('You can now run runAllExamples() to see all functionality.');
}

/**
 * Create a sample Google Sheet with visitor data for testing
 */
function createSampleVisitorSheet() {
  console.log('📋 Creating sample visitor sheet...');
  
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = spreadsheet.insertSheet('Sample Visitors');
  
  // Sample data with headers
  const sampleData = [
    ['first_name', 'last_name', 'email', 'mobile', 'company', 'purpose', 'visit_date', 'visit_time'],
    ['John', 'Smith', 'john.smith@example.com', '+1 555-0101', 'Tech Corp', 'Meeting', '2025-01-20', '09:00'],
    ['Alice', 'Johnson', 'alice.johnson@company.com', '+1 555-0102', 'Design Ltd', 'Interview', '2025-01-20', '10:30'],
    ['Bob', 'Wilson', 'bob.wilson@org.com', '+1 555-0103', 'Marketing Inc', 'Presentation', '2025-01-20', '14:00'],
    ['Sarah', 'Davis', 'sarah.davis@startup.com', '+1 555-0104', 'StartupXYZ', 'Demo', '2025-01-20', '15:30']
  ];
  
  // Write data to sheet
  const range = sheet.getRange(1, 1, sampleData.length, sampleData[0].length);
  range.setValues(sampleData);
  
  // Format headers
  const headerRange = sheet.getRange(1, 1, 1, sampleData[0].length);
  headerRange.setFontWeight('bold');
  headerRange.setBackground('#4CAF50');
  headerRange.setFontColor('white');
  
  // Auto-resize columns
  sheet.autoResizeColumns(1, sampleData[0].length);
  
  console.log('✅ Sample visitor sheet created with 4 test visitors');
  console.log('You can now run example7_processVisitorsFromSheets() to test bulk creation');
}
