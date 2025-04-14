/**
 * UI Module - Handles UI interactions and animations
 * 
 * This module provides helper functions for UI elements like theme switching,
 * scroll animations, and lightbox functionality, while maintaining compatibility
 * with existing inline JavaScript.
 */

// Safely initialize UI namespace
window.UI = window.UI || {};

/**
 * Initialize all UI functionality
 */
UI.init = function() {
    console.log('UI module initializing...');
    
    // Initialize components (without overriding existing functionality)
    UI.setupThemeToggle();
    UI.setupScrollAnimations();
    UI.setupLightbox();
    
    console.log('UI module initialized');
};

/**
 * Set up theme toggle functionality
 * This enhances but doesn't replace existing theme toggle code
 */
UI.setupThemeToggle = function() {
    const themeBtn = document.getElementById('theme-btn');
    if (!themeBtn) return;
    
    // Check for saved theme preference (if not already handled)
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark' && !document.body.classList.contains('dark-mode')) {
        document.body.classList.add('dark-mode');
        const icon = themeBtn.querySelector('.btn-icon');
        if (icon) icon.textContent = '☾';
    }
    
    // Only add listener if it doesn't already exist
    if (!themeBtn._themeToggleInitialized) {
        themeBtn.addEventListener('click', function() {
            document.body.classList.toggle('dark-mode');
            
            // Update the theme icon
            const icon = themeBtn.querySelector('.btn-icon');
            if (icon) {
                const isDark = document.body.classList.contains('dark-mode');
                icon.textContent = isDark ? '☾' : '☀';
                themeBtn.setAttribute('aria-label', isDark ? 'Switch to light mode' : 'Switch to dark mode');
                localStorage.setItem('theme', isDark ? 'dark' : 'light');
            }
        });
        
        // Mark the button as initialized to avoid duplicate listeners
        themeBtn._themeToggleInitialized = true;
    }
};

/**
 * Set up scroll animations using Intersection Observer
 */
UI.setupScrollAnimations = function() {
    // Don't re-initialize if already set up
    if (window._scrollAnimationsInitialized) return;
    
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target); // Stop observing once visible
            }
        });
    }, observerOptions);
    
    // Observe all sections for animation
    document.querySelectorAll('section').forEach(section => {
        observer.observe(section);
    });
    
    // Mark as initialized
    window._scrollAnimationsInitialized = true;
};

/**
 * Set up lightbox functionality
 */
UI.setupLightbox = function() {
    const lightbox = document.getElementById('image-lightbox');
    const lightboxClose = document.querySelector('.lightbox-close');
    
    if (!lightbox || !lightboxClose) return;
    
    // Don't add listeners if already initialized
    if (lightbox._lightboxInitialized) return;
    
    // Close lightbox when clicking the close button
    lightboxClose.addEventListener('click', function() {
        lightbox.style.display = 'none';
    });
    
    // Close lightbox when clicking outside the image
    lightbox.addEventListener('click', function(e) {
        if (e.target === lightbox) {
            lightbox.style.display = 'none';
        }
    });
    
    // Add global function to open lightbox (maintaining compatibility)
    window.openLightbox = function(imgSrc) {
        const lightboxImg = document.getElementById('lightbox-img');
        if (lightboxImg) {
            lightboxImg.src = imgSrc;
            lightbox.style.display = 'flex';
        }
    };
    
    // Mark as initialized
    lightbox._lightboxInitialized = true;
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize UI functionality
    UI.init();
}); 