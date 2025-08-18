/**
 * Google Drive Integration Functions for EVTrack API
 * Functions for handling Google Drive files in EVTrack workflows
 */

/**
 * Extract file ID from Google Drive URL
 * @param {string} url - Google Drive URL
 * @returns {string|null} File ID or null if invalid
 */
function extractDriveFileId(url) {
  if (!url) return null;
  
  // Handle different Google Drive URL formats
  const patterns = [
    /\/file\/d\/([a-zA-Z0-9-_]+)/,  // /file/d/FILE_ID
    /id=([a-zA-Z0-9-_]+)/,          // ?id=FILE_ID
    /\/d\/([a-zA-Z0-9-_]+)/,        // /d/FILE_ID
    /^([a-zA-Z0-9-_]+)$/            // Just the ID
  ];
  
  for (const pattern of patterns) {
    const match = url.match(pattern);
    if (match) {
      return match[1];
    }
  }
  
  return null;
}

/**
 * Get file information from Google Drive
 * @param {string} fileId - Google Drive file ID
 * @returns {Object} File information
 */
function getDriveFileInfo(fileId) {
  try {
    const file = DriveApp.getFileById(fileId);
    
    return {
      success: true,
      fileId: fileId,
      name: file.getName(),
      mimeType: file.getBlob().getContentType(),
      size: file.getSize(),
      url: file.getUrl(),
      downloadUrl: file.getDownloadUrl(),
      isImage: file.getBlob().getContentType().startsWith('image/'),
      isPdf: file.getBlob().getContentType() === 'application/pdf'
    };
  } catch (error) {
    console.error('Error getting file info:', error);
    return {
      success: false,
      error: `Cannot access file: ${error.message}`,
      fileId: fileId
    };
  }
}

/**
 * Convert Google Drive file to base64 for API upload
 * @param {string} fileId - Google Drive file ID
 * @param {number} maxSizeKB - Maximum file size in KB (default 5MB)
 * @returns {Object} File data ready for API
 */
function prepareDriveFileForUpload(fileId, maxSizeKB = 5120) {
  try {
    const file = DriveApp.getFileById(fileId);
    const blob = file.getBlob();
    const sizeKB = blob.getBytes().length / 1024;
    
    if (sizeKB > maxSizeKB) {
      return {
        success: false,
        error: `File too large: ${sizeKB.toFixed(1)}KB (max: ${maxSizeKB}KB)`,
        fileSize: sizeKB
      };
    }
    
    const base64Data = Utilities.base64Encode(blob.getBytes());
    
    return {
      success: true,
      fileName: file.getName(),
      mimeType: blob.getContentType(),
      size: blob.getBytes().length,
      sizeKB: sizeKB,
      base64Data: base64Data,
      fileId: fileId
    };
  } catch (error) {
    console.error('Error preparing file for upload:', error);
    return {
      success: false,
      error: `Cannot prepare file: ${error.message}`,
      fileId: fileId
    };
  }
}

/**
 * Process photo attachments from Google Drive for visitor profiles
 * @param {Array} driveUrls - Array of Google Drive URLs
 * @param {string} visitorSearchTerm - Term to identify the visitor
 * @returns {Object} Processing results
 */
function processVisitorPhotosFromDrive(driveUrls, visitorSearchTerm) {
  console.log(`Processing ${driveUrls.length} photos for visitor: ${visitorSearchTerm}`);
  
  const results = [];
  const errors = [];
  
  for (let i = 0; i < driveUrls.length; i++) {
    const url = driveUrls[i];
    
    try {
      console.log(`Processing photo ${i + 1}: ${url}`);
      
      // Extract file ID
      const fileId = extractDriveFileId(url);
      if (!fileId) {
        errors.push({
          url: url,
          error: 'Invalid Google Drive URL format'
        });
        continue;
      }
      
      // Get file info
      const fileInfo = getDriveFileInfo(fileId);
      if (!fileInfo.success) {
        errors.push({
          url: url,
          fileId: fileId,
          error: fileInfo.error
        });
        continue;
      }
      
      // Verify it's an image
      if (!fileInfo.isImage) {
        errors.push({
          url: url,
          fileId: fileId,
          error: `File is not an image: ${fileInfo.mimeType}`
        });
        continue;
      }
      
      // Prepare for upload
      const fileData = prepareDriveFileForUpload(fileId, 2048); // 2MB limit for photos
      if (!fileData.success) {
        errors.push({
          url: url,
          fileId: fileId,
          error: fileData.error
        });
        continue;
      }
      
      results.push({
        url: url,
        fileId: fileId,
        fileName: fileInfo.name,
        mimeType: fileInfo.mimeType,
        sizeKB: fileData.sizeKB,
        ready: true
      });
      
      console.log(`✅ Photo ${i + 1} processed: ${fileInfo.name} (${fileData.sizeKB.toFixed(1)}KB)`);
      
    } catch (error) {
      console.error(`Error processing photo ${i + 1}:`, error);
      errors.push({
        url: url,
        error: error.toString()
      });
    }
  }
  
  console.log(`Photo processing complete: ${results.length} ready, ${errors.length} errors`);
  
  return {
    success: true,
    processed: driveUrls.length,
    readyCount: results.length,
    errorCount: errors.length,
    photos: results,
    errors: errors,
    visitorSearchTerm: visitorSearchTerm
  };
}

/**
 * Upload visitor badge photo from Google Drive
 * @param {string} visitorSearchTerm - Term to find the visitor
 * @param {string} driveUrl - Google Drive URL of the photo
 * @returns {Object} Upload result
 */
function uploadVisitorBadgePhoto(visitorSearchTerm, driveUrl) {
  console.log(`Uploading badge photo for visitor: ${visitorSearchTerm}`);
  
  try {
    // Extract and validate file
    const fileId = extractDriveFileId(driveUrl);
    if (!fileId) {
      return {
        success: false,
        error: 'Invalid Google Drive URL format'
      };
    }
    
    const fileInfo = getDriveFileInfo(fileId);
    if (!fileInfo.success) {
      return {
        success: false,
        error: fileInfo.error
      };
    }
    
    if (!fileInfo.isImage) {
      return {
        success: false,
        error: `File is not an image: ${fileInfo.mimeType}`
      };
    }
    
    // Prepare file data
    const fileData = prepareDriveFileForUpload(fileId, 1024); // 1MB limit for badge photos
    if (!fileData.success) {
      return {
        success: false,
        error: fileData.error
      };
    }
    
    // Here you would typically send the file data to your API
    // For now, we'll return the prepared data
    console.log('✅ Badge photo ready for upload');
    
    return {
      success: true,
      message: 'Badge photo prepared successfully',
      fileName: fileData.fileName,
      fileSize: `${fileData.sizeKB.toFixed(1)}KB`,
      visitorSearchTerm: visitorSearchTerm,
      // In a real implementation, you'd include the base64Data for API upload
      ready: true
    };
    
  } catch (error) {
    console.error('Error uploading badge photo:', error);
    return {
      success: false,
      error: error.toString()
    };
  }
}

/**
 * Batch process files from a Google Sheets column containing Drive URLs
 * @param {Array} sheetData - 2D array with headers in first row
 * @param {string} urlColumn - Column name containing Drive URLs
 * @param {string} nameColumn - Column name containing visitor names/search terms
 * @param {number} startRow - Row to start processing (1-based, default 2)
 * @returns {Object} Batch processing results
 */
function batchProcessDriveFiles(sheetData, urlColumn = 'photo_url', nameColumn = 'email', startRow = 2) {
  console.log('Batch processing Drive files from Google Sheet');
  
  if (!sheetData || sheetData.length < 2) {
    return {
      success: false,
      error: 'Sheet must have at least 2 rows (headers + data)',
      processed: 0
    };
  }
  
  const headers = sheetData[0];
  const urlColumnIndex = headers.findIndex(h => h.toLowerCase().trim() === urlColumn.toLowerCase());
  const nameColumnIndex = headers.findIndex(h => h.toLowerCase().trim() === nameColumn.toLowerCase());
  
  if (urlColumnIndex === -1) {
    return {
      success: false,
      error: `URL column '${urlColumn}' not found in headers`
    };
  }
  
  if (nameColumnIndex === -1) {
    return {
      success: false,
      error: `Name column '${nameColumn}' not found in headers`
    };
  }
  
  const results = [];
  const errors = [];
  
  for (let i = startRow - 1; i < sheetData.length; i++) {
    const rowNumber = i + 1;
    const rowData = sheetData[i];
    
    try {
      const driveUrl = rowData[urlColumnIndex];
      const searchTerm = rowData[nameColumnIndex];
      
      if (!driveUrl || !searchTerm) {
        errors.push({
          row: rowNumber,
          error: 'Missing URL or search term'
        });
        continue;
      }
      
      const result = uploadVisitorBadgePhoto(searchTerm, driveUrl);
      
      results.push({
        row: rowNumber,
        searchTerm: searchTerm,
        driveUrl: driveUrl,
        success: result.success,
        message: result.success ? result.message : result.error,
        fileName: result.fileName || null
      });
      
      // Small delay between processes
      Utilities.sleep(1000);
      
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
  
  console.log(`✅ Batch processing complete: ${successCount} success, ${failureCount} failures`);
  
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
 * Create a shareable Google Drive folder for EVTrack files
 * @param {string} folderName - Name for the new folder
 * @param {string} parentFolderId - Optional parent folder ID
 * @returns {Object} Folder creation result
 */
function createEVTrackFolder(folderName = 'EVTrack Files', parentFolderId = null) {
  try {
    let folder;
    
    if (parentFolderId) {
      const parentFolder = DriveApp.getFolderById(parentFolderId);
      folder = parentFolder.createFolder(folderName);
    } else {
      folder = DriveApp.createFolder(folderName);
    }
    
    // Make folder shareable (view access for anyone with link)
    folder.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
    
    console.log(`✅ Created EVTrack folder: ${folderName}`);
    
    return {
      success: true,
      message: `Folder '${folderName}' created successfully`,
      folderId: folder.getId(),
      folderUrl: folder.getUrl(),
      folderName: folderName
    };
    
  } catch (error) {
    console.error('Error creating folder:', error);
    return {
      success: false,
      error: error.toString()
    };
  }
}
