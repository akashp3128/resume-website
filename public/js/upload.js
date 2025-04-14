/**
 * Upload Module - Handles file upload functionality
 * 
 * This module provides functions for uploading files to the server,
 * with backward compatibility with the existing upload code.
 */

// Safely initialize Upload namespace
window.Upload = window.Upload || {};

// Configuration 
Upload.ENDPOINTS = {
    PRIMARY: 'https://upload-handler.akashpatelresume.us/upload',
    FALLBACK: 'http://localhost:8001/upload'
};

// State
Upload.activeEndpoint = null;
Upload.endpointChecked = false;

/**
 * Initialize upload functionality
 */
Upload.init = function() {
    console.log('Upload module initializing...');
    
    // Add upload status elements if they don't exist
    Upload.setupStatusElements();
    
    // Check endpoint availability
    Upload.checkEndpoints();
    
    // Load any previously uploaded files
    Upload.loadSavedUploads();
    
    console.log('Upload module initialized');
};

/**
 * Add status elements to upload containers if they don't exist
 */
Upload.setupStatusElements = function() {
    const uploadContainers = [
        document.getElementById('photo-upload-container'),
        document.getElementById('resume-upload-container'),
        document.getElementById('eval-upload-container')
    ];
    
    uploadContainers.forEach(container => {
        if (container && !container.querySelector('.upload-status')) {
            const statusDiv = document.createElement('div');
            statusDiv.className = 'upload-status';
            statusDiv.style.fontSize = '0.8rem';
            statusDiv.style.marginTop = '0.5rem';
            container.appendChild(statusDiv);
        }
    });
};

/**
 * Check which endpoint is available
 * This doesn't override the existing endpoint checking logic
 */
Upload.checkEndpoints = async function() {
    if (Upload.endpointChecked) return;
    
    const currentOrigin = window.location.origin;
    
    try {
        console.log('Checking primary endpoint...');
        // Try primary endpoint first
        const response = await fetch(Upload.ENDPOINTS.PRIMARY, { 
            method: 'OPTIONS',
            headers: { 'Origin': currentOrigin }
        });
        
        if (response.ok) {
            Upload.activeEndpoint = Upload.ENDPOINTS.PRIMARY;
            console.log('Using production upload endpoint');
            Upload.endpointChecked = true;
            return;
        }
    } catch (error) {
        console.log('Primary endpoint not available:', error.message);
    }
    
    try {
        console.log('Checking fallback endpoint...');
        // Try fallback endpoint
        const response = await fetch(Upload.ENDPOINTS.FALLBACK, { 
            method: 'OPTIONS',
            headers: { 'Origin': currentOrigin }
        });
        
        if (response.ok) {
            Upload.activeEndpoint = Upload.ENDPOINTS.FALLBACK;
            console.log('Using local upload endpoint');
            Upload.endpointChecked = true;
            return;
        }
    } catch (error) {
        console.log('Fallback endpoint not available:', error.message);
    }
    
    // If we get here, neither endpoint is available
    console.error('No upload endpoints available');
    
    // Show error message in upload status divs
    document.querySelectorAll('.upload-status').forEach(statusDiv => {
        statusDiv.textContent = 'Upload service unavailable';
        statusDiv.style.color = 'red';
    });
};

/**
 * Update status element with message and appropriate styling
 */
Upload.updateStatus = function(statusElement, message, status) {
    if (!statusElement) return;
    
    statusElement.textContent = message;
    
    // Set appropriate color
    if (status === 'error') {
        statusElement.style.color = 'red';
    } else if (status === 'success') {
        statusElement.style.color = 'green';
    } else if (status === 'pending') {
        statusElement.style.color = 'orange';
    }
};

/**
 * Save upload information to localStorage
 */
Upload.saveUploadInfo = function(fileType, filename, url) {
    const uploads = JSON.parse(localStorage.getItem('uploads') || '{}');
    uploads[fileType] = { filename, url, timestamp: new Date().toISOString() };
    localStorage.setItem('uploads', JSON.stringify(uploads));
};

/**
 * Display resume in the appropriate section
 * This maintains compatibility with existing displayResume function
 */
Upload.displayResume = function(resumeUrl, filename) {
    console.log(`Displaying resume: ${resumeUrl}`);
    const container = document.getElementById('resume-container');
    if (!container) return;
    
    // If the original displayResume function exists, use it
    if (typeof window.displayResume === 'function') {
        window.displayResume(resumeUrl, filename);
        return;
    }
    
    // Otherwise, implement our own version
    // Create the preview container
    const previewContainer = document.createElement('div');
    previewContainer.className = 'resume-preview-container';
    
    // Create actions bar with download link
    const actionsDiv = document.createElement('div');
    actionsDiv.className = 'resume-actions';
    
    // Create download link
    const downloadLink = document.createElement('a');
    downloadLink.href = resumeUrl;
    downloadLink.className = 'resume-download-link';
    downloadLink.textContent = 'Download Resume';
    downloadLink.target = '_blank';
    downloadLink.setAttribute('rel', 'noopener');
    actionsDiv.appendChild(downloadLink);
    
    // Add filename display if available
    if (filename) {
        const filenameSpan = document.createElement('span');
        filenameSpan.textContent = filename;
        filenameSpan.style.color = '#666';
        filenameSpan.style.fontSize = '0.9rem';
        actionsDiv.appendChild(filenameSpan);
    }
    
    previewContainer.appendChild(actionsDiv);
    
    // Create PDF viewer (for PDFs)
    if (resumeUrl.toLowerCase().endsWith('.pdf')) {
        const pdfViewer = document.createElement('iframe');
        pdfViewer.className = 'pdf-viewer';
        pdfViewer.style.width = '100%';
        pdfViewer.style.height = '500px';
        pdfViewer.style.border = 'none';
        pdfViewer.src = resumeUrl;
        
        previewContainer.appendChild(pdfViewer);
    }
    
    // Clear container and add new elements
    container.innerHTML = '';
    container.appendChild(previewContainer);
};

/**
 * Load previously uploaded files from localStorage
 * This maintains compatibility with the existing loadSavedUploads function
 */
Upload.loadSavedUploads = function() {
    // If the original function exists, call it first to maintain compatibility
    if (typeof window.loadSavedUploads === 'function') {
        window.loadSavedUploads();
        return;
    }
    
    // Otherwise, implement our own version
    const uploads = JSON.parse(localStorage.getItem('uploads') || '{}');
    
    // Handle resume if it exists
    if (uploads.resume && uploads.resume.url) {
        Upload.displayResume(uploads.resume.url, uploads.resume.filename);
    }
    
    // Handle photo if it exists
    if (uploads.photo && uploads.photo.url) {
        const photoContainer = document.querySelector('.photo-container');
        if (photoContainer) {
            photoContainer.innerHTML = '';
            const img = document.createElement('img');
            img.src = uploads.photo.url;
            img.alt = "Uploaded photo";
            photoContainer.appendChild(img);
        }
    }
    
    // Handle evaluations if they exist
    if (uploads.evaluations && Array.isArray(uploads.evaluations)) {
        const listElement = document.querySelector('#navy .document-list');
        if (listElement && uploads.evaluations.length > 0) {
            listElement.innerHTML = '';
            
            uploads.evaluations.forEach(eval => {
                const li = document.createElement('li');
                
                // Check if it's an image
                const isImage = eval.url.toLowerCase().endsWith('.jpg') || 
                                eval.url.toLowerCase().endsWith('.jpeg') || 
                                eval.url.toLowerCase().endsWith('.png');
                
                if (isImage) {
                    // Create thumbnail for images
                    const thumbnail = document.createElement('img');
                    thumbnail.src = eval.url;
                    thumbnail.alt = eval.name;
                    thumbnail.className = 'thumbnail';
                    thumbnail.onclick = function() {
                        if (typeof window.openLightbox === 'function') {
                            window.openLightbox(eval.url);
                        }
                    };
                    li.appendChild(thumbnail);
                }
                
                const a = document.createElement('a');
                a.href = eval.url;
                a.target = '_blank';
                a.textContent = eval.name;
                li.appendChild(a);
                
                listElement.appendChild(li);
            });
        }
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize upload functionality
    Upload.init();
}); 