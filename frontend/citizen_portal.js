// Mobile menu toggle
function toggleMobileMenu() {
    const menu = document.getElementById('mobileMenu');
    menu.classList.toggle('active');
}

// Close mobile menu when clicking outside or on a link
document.addEventListener('click', function(e) {
    const menu = document.getElementById('mobileMenu');
    const hamburger = document.querySelector('button[onclick="toggleMobileMenu()"]');

    // Close if clicking outside menu and hamburger
    if (!menu.contains(e.target) && !hamburger.contains(e.target)) {
        menu.classList.remove('active');
    }

    // Close if clicking a link inside menu
    if (e.target.tagName === 'A' && menu.contains(e.target)) {
        menu.classList.remove('active');
    }
});

// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
        // Close mobile menu if open
        document.getElementById('mobileMenu').classList.remove('active');
    });
});

// Global variables for camera and location
let currentStream = null;
let gpsCoordinates = null;

// ===== RESTORE TRACKING NUMBER FROM STORAGE ON PAGE LOAD =====
function restoreTrackingNumberFromStorage() {
    const savedTrackingNumber = localStorage.getItem('lastTrackingNumber');
    const savedTime = localStorage.getItem('lastTrackingNumberTime');

    if (savedTrackingNumber && savedTime) {
        const timeAgo = Date.now() - parseInt(savedTime);
        // Show tracking number for up to 24 hours
        if (timeAgo < 24 * 60 * 60 * 1000) {
            const successMessage = document.getElementById('successMessage');
            const trackingNumberElement = document.getElementById('trackingNumber');

            trackingNumberElement.textContent = savedTrackingNumber;

            // Show success message
            successMessage.classList.remove('hidden');
            successMessage.style.display = 'block';
            successMessage.style.visibility = 'visible';
            successMessage.style.opacity = '1';

            console.log('✅ Restored tracking number from storage:', savedTrackingNumber);

            // Scroll to it after a short delay
            setTimeout(() => {
                successMessage.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, 300);
        } else {
            // Clear if older than 24 hours
            localStorage.removeItem('lastTrackingNumber');
            localStorage.removeItem('lastTrackingNumberTime');
        }
    }
}

// Restore on page load
document.addEventListener('DOMContentLoaded', restoreTrackingNumberFromStorage);
// Also try immediately in case DOM is already loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', restoreTrackingNumberFromStorage);
} else {
    restoreTrackingNumberFromStorage();
}

// Camera functionality
document.getElementById('cameraBtn').addEventListener('click', async function() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'environment' } // Use back camera on mobile
        });

        currentStream = stream;
        const video = document.getElementById('cameraPreview');
        video.srcObject = stream;
        video.play();

        // Show camera preview and controls
        document.getElementById('uploadOptions').classList.add('hidden');
        document.getElementById('cameraPreview').classList.remove('hidden');
        document.getElementById('cameraControls').classList.remove('hidden');

    } catch (error) {
        console.error('Camera access denied:', error);
        alert('Camera access is required to take photos. Please allow camera access or use the upload option.');
    }
});

// Capture photo from camera
document.getElementById('captureBtn').addEventListener('click', function() {
    const video = document.getElementById('cameraPreview');
    const canvas = document.getElementById('cameraCanvas');
    const ctx = canvas.getContext('2d');

    // Set canvas dimensions to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw video frame to canvas
    ctx.drawImage(video, 0, 0);

    // Convert to blob and create file
    canvas.toBlob(function(blob) {
        const file = new File([blob], 'camera-photo.jpg', { type: 'image/jpeg' });

        // Create a new FileList-like object
        const dt = new DataTransfer();
        dt.items.add(file);
        document.getElementById('photoInput').files = dt.files;

        // Show preview
        const preview = document.getElementById('photoPreview');
        preview.src = canvas.toDataURL();
        preview.classList.remove('hidden');

        // Stop camera and hide controls
        stopCamera();

    }, 'image/jpeg', 0.8);
});

// Retake photo
document.getElementById('retakeBtn').addEventListener('click', function() {
    // Clear the current preview and canvas, reset to camera mode
    const video = document.getElementById('cameraPreview');
    const canvas = document.getElementById('cameraCanvas');

    // Clear canvas
    canvas.width = 0;
    canvas.height = 0;

    // Restart video stream
    if (currentStream) {
        video.play();
    }
});

// Cancel camera
document.getElementById('cancelCameraBtn').addEventListener('click', function() {
    stopCamera();
});

function stopCamera() {
    if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
        currentStream = null;
    }

    document.getElementById('uploadOptions').classList.remove('hidden');
    document.getElementById('cameraPreview').classList.add('hidden');
    document.getElementById('cameraControls').classList.add('hidden');
}

// Lagos LGA coordinate boundaries (approximate)
const lagosLGABoundaries = {
    'Agege': { lat: [6.58, 6.65], lng: [3.34, 3.40] },
    'Ajeromi-Ifelodun': { lat: [6.48, 6.58], lng: [3.32, 3.40] },
    'Alimosho': { lat: [6.60, 6.72], lng: [3.28, 3.42] },
    'Amuwo-Odofin': { lat: [6.42, 6.50], lng: [3.12, 3.28] },
    'Apapa': { lat: [6.40, 6.48], lng: [3.32, 3.38] },
    'Badagry': { lat: [6.40, 6.52], lng: [2.80, 3.02] },
    'Epe': { lat: [6.50, 6.65], lng: [3.92, 4.15] },
    'Eti-Osa': { lat: [6.42, 6.55], lng: [3.58, 3.75] },
    'Ibeju-Lekki': { lat: [6.45, 6.60], lng: [3.75, 4.02] },
    'Ifako-Ijaiye': { lat: [6.65, 6.72], lng: [3.35, 3.42] },
    'Ikeja': { lat: [6.57, 6.68], lng: [3.32, 3.42] },
    'Ikorodu': { lat: [6.55, 6.68], lng: [3.48, 3.62] },
    'Kosofe': { lat: [6.48, 6.58], lng: [3.52, 3.62] },
    'Lagos Island': { lat: [6.40, 6.50], lng: [3.38, 3.48] },
    'Lagos Mainland': { lat: [6.48, 6.58], lng: [3.38, 3.50] },
    'Mushin': { lat: [6.60, 6.70], lng: [3.32, 3.42] },
    'Ojo': { lat: [6.48, 6.60], lng: [3.08, 3.22] },
    'Oshodi-Isolo': { lat: [6.55, 6.65], lng: [3.42, 3.55] },
    'Shomolu': { lat: [6.52, 6.62], lng: [3.42, 3.52] },
    'Surulere': { lat: [6.52, 6.62], lng: [3.32, 3.42] }
};

// Function to determine LGA from coordinates
function getLGAFromCoordinates(lat, lng) {
    for (const [lga, bounds] of Object.entries(lagosLGABoundaries)) {
        if (lat >= bounds.lat[0] && lat <= bounds.lat[1] &&
            lng >= bounds.lng[0] && lng <= bounds.lng[1]) {
            return lga;
        }
    }
    return null; // Not in any known LGA
}

// Auto-detect location
document.getElementById('detectLocationBtn').addEventListener('click', function() {
    const button = this;
    const spinner = document.getElementById('locationSpinner');
    const gpsDisplay = document.getElementById('gpsDisplay');
    const gpsCoords = document.getElementById('gpsCoords');
    const detectedLGA = document.getElementById('detectedLGA');

    button.disabled = true;
    spinner.classList.remove('hidden');

    if (!navigator.geolocation) {
        alert('❌ Geolocation is not supported by this browser.\n\nPlease manually enter your location and select your LGA below.');
        button.disabled = false;
        spinner.classList.add('hidden');
        return;
    }

    navigator.geolocation.getCurrentPosition(
        function(position) {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;

            gpsCoordinates = { lat, lng };

            // Display GPS coordinates
            gpsCoords.textContent = `📍 Lat: ${lat.toFixed(6)}, Lng: ${lng.toFixed(6)}`;

            // Determine LGA from coordinates
            const detectedLGAName = getLGAFromCoordinates(lat, lng);

            if (detectedLGAName) {
                detectedLGA.innerHTML = `<strong>🏘️ LGA Detected:</strong> ${detectedLGAName}`;
                document.getElementById('lga').value = detectedLGAName;
            } else {
                detectedLGA.innerHTML = `<strong>⚠️ Location Outside Lagos LGAs</strong> - Please select your LGA manually below`;
            }

            gpsDisplay.classList.remove('hidden');

            // Update button appearance
            button.disabled = false;
            spinner.classList.add('hidden');
            button.innerHTML = '<i class="fas fa-check-circle mr-2"></i>Location Detected Successfully';
            button.classList.remove('from-blue-600', 'to-blue-700', 'hover:from-blue-700', 'hover:to-blue-800');
            button.classList.add('from-green-600', 'to-green-700', 'hover:from-green-700', 'hover:to-green-800');
            button.disabled = true;
        },
        function(error) {
            let message = '❌ Unable to get your location.\n\n';
            switch(error.code) {
                case error.PERMISSION_DENIED:
                    message += 'Please allow location access in your browser settings and try again.\n\nOr manually enter your location below.';
                    break;
                case error.POSITION_UNAVAILABLE:
                    message += 'Location information is not available. Please check your GPS and try again.\n\nOr manually enter your location below.';
                    break;
                case error.TIMEOUT:
                    message += 'Location request timed out. Please try again in an area with better GPS signal.\n\nOr manually enter your location below.';
                    break;
            }
            alert(message);
            button.disabled = false;
            spinner.classList.add('hidden');
        },
        {
            enableHighAccuracy: true,
            timeout: 15000,
            maximumAge: 0
        }
    );
});

// Photo preview functionality
document.getElementById('photoInput').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(event) {
            const preview = document.getElementById('photoPreview');
            preview.src = event.target.result;
            preview.classList.remove('hidden');
        };
        reader.readAsDataURL(file);
    }
});

// Enhanced form submission with loading states
document.getElementById('reportForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const submitButton = e.target.querySelector('button[type="submit"]');
    const spinner = document.getElementById('submitSpinner');
    const form = this;

    // Show loading state
    submitButton.disabled = true;
    spinner.classList.remove('hidden');

    try {
        // Validate consent checkbox
        const consentCheckbox = document.getElementById('consentCheckbox');
        if (!consentCheckbox.checked) {
            throw new Error('Please accept the privacy policy and terms of service to submit your report');
        }

        // Validate required fields
        const location = document.getElementById('location').value.trim();
        const lga = document.getElementById('lga').value;

        if (!location) {
            throw new Error('Please enter a location description');
        }
        if (!lga) {
            throw new Error('Please select your Local Government Area (LGA)');
        }

        // Combine location description with LGA
        const fullLocation = `${location}, ${lga} LGA, Lagos`;

        // Get image file and convert to base64
        const photoFile = document.getElementById('photoInput').files[0];
        if (!photoFile) {
            throw new Error('Please select a photo');
        }

        // Convert image to base64
        const reader = new FileReader();
        const photoBase64 = await new Promise((resolve, reject) => {
            reader.onload = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsDataURL(photoFile);
        });

        // Prepare JSON payload for integrated_backend
        const payload = {
            location: fullLocation,
            lga: lga,
            state: 'Lagos',
            description: document.getElementById('description').value,
            contact: document.getElementById('phone').value,
            photo: photoBase64,
            gps_coordinates: gpsCoordinates // Include GPS coordinates if detected
        };

        const response = await fetch('http://localhost:5000/api/submit-report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Server error');
        }

        console.log('✅ Report submitted successfully:', result);
        console.log('📋 Full response object:', JSON.stringify(result, null, 2));
        console.log('🔢 Tracking number value:', result.tracking_number);
        console.log('🔢 Type of tracking_number:', typeof result.tracking_number);

        // Show success message with tracking number
        const trackingNumberElement = document.getElementById('trackingNumber');
        console.log('📍 Tracking number element found:', trackingNumberElement);
        console.log('📍 Element ID:', trackingNumberElement?.id);

        if (result.tracking_number) {
            trackingNumberElement.textContent = result.tracking_number;
            console.log('✅ Setting tracking number to:', result.tracking_number);
            console.log('✅ Element text content is now:', trackingNumberElement.textContent);

            // ===== SAVE TRACKING NUMBER TO LOCALSTORAGE =====
            localStorage.setItem('lastTrackingNumber', result.tracking_number);
            localStorage.setItem('lastTrackingNumberTime', Date.now().toString());
            console.log('💾 Saved tracking number to localStorage');
        } else {
            console.error('❌ No tracking_number in response!');
            trackingNumberElement.textContent = 'N/A';
        }
        const successMessage = document.getElementById('successMessage');

        // Completely unhide the element by removing all hidden classes
        successMessage.classList.remove('hidden');
        successMessage.classList.remove('hidden-by-user');

        // Set explicit inline styles to keep it visible
        successMessage.style.display = 'block';
        successMessage.style.visibility = 'visible';
        successMessage.style.opacity = '1';
        successMessage.style.pointerEvents = 'auto';
        successMessage.style.position = 'relative';

        // Force a repaint
        void successMessage.offsetHeight;
        console.log('✅ Success message display:', successMessage.style.display);
        console.log('✅ Success message visibility:', successMessage.style.visibility);
        console.log('✅ Success message opacity:', successMessage.style.opacity);

        // PREVENT ANYTHING FROM HIDING THE MESSAGE - MutationObserver
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.attributeName === 'class') {
                    console.log('🔍 Class mutation detected on success message:', successMessage.className);
                    // Immediately remove 'hidden' class if someone tries to add it
                    if (successMessage.classList.contains('hidden')) {
                        console.warn('⚠️ Someone tried to add hidden class! Removing it...');
                        successMessage.classList.remove('hidden');
                    }
                }
                if (mutation.attributeName === 'style') {
                    console.log('🔍 Style mutation detected on success message');
                    // Ensure display stays visible
                    if (successMessage.style.display === 'none') {
                        console.warn('⚠️ Someone tried to set display:none! Fixing it...');
                        successMessage.style.display = 'block';
                    }
                }
            });
        });

        observer.observe(successMessage, {
            attributes: true,
            attributeFilter: ['class', 'style'],
            attributeOldValue: true
        });
        console.log('✅ MutationObserver set up to protect success message');

        // Scroll to success message after a tiny delay to ensure rendering
        setTimeout(() => {
            successMessage.scrollIntoView({ behavior: 'smooth', block: 'center' });
            console.log('✅ Scrolled to success message');
        }, 100);

        // Store tracking number in console for user reference
        console.log(`Report submitted! Tracking Number: ${result.tracking_number}`);

        // Add a "Copy Tracking Number" button
        trackingNumberElement.style.cursor = 'pointer';
        trackingNumberElement.title = 'Click to copy tracking number';
        trackingNumberElement.onclick = function() {
            navigator.clipboard.writeText(result.tracking_number);
            alert('Tracking number copied to clipboard!');
            console.log('✅ Tracking number copied to clipboard');
        };

        // Add close button to success message if not present
        if (!successMessage.querySelector('.close-btn')) {
            const closeBtn = document.createElement('button');
            closeBtn.className = 'close-btn absolute top-2 right-2 text-white hover:text-gray-200 text-2xl font-bold';
            closeBtn.innerHTML = '&times;';
            closeBtn.style.padding = '0.5rem 0.75rem';
            closeBtn.style.lineHeight = '1';
            closeBtn.onclick = function(e) {
                e.preventDefault();
                console.log('❌ Close button clicked - hiding message');
                successMessage.classList.add('hidden-by-user');
                successMessage.style.display = 'none';
                // Reset form after closing success message
                form.reset();
                document.getElementById('photoPreview').classList.add('hidden');
                document.getElementById('gpsDisplay').classList.add('hidden');

                // Reset location button
                const locationBtn = document.getElementById('detectLocationBtn');
                locationBtn.innerHTML = '<i class="fas fa-crosshairs mr-2"></i>Auto-detect My Location';
                locationBtn.classList.remove('bg-green-600', 'hover:bg-green-700');
                locationBtn.classList.add('bg-orange-600', 'hover:bg-orange-700');

                gpsCoordinates = null;
            };
            successMessage.style.position = 'relative';
            successMessage.appendChild(closeBtn);
        }

    } catch (error) {
        console.error('Full error:', error);
        alert('Error submitting report: ' + error.message);
    } finally {
        // Reset button state
        submitButton.disabled = false;
        spinner.classList.add('hidden');
    }
});

// Enhanced track report function
async function trackReport() {
    const trackingNum = document.getElementById('trackingInput').value.trim();

    if (!trackingNum) {
        alert('Please enter a tracking number');
        return;
    }

    try {
        const response = await fetch(`http://localhost:5000/api/track/${trackingNum}`);

        if (!response.ok) {
            alert('Report not found. Please check your tracking number.');
            return;
        }

        const data = await response.json();

        // Enhanced status display with better styling
        document.getElementById('statusDisplay').innerHTML = `
            <div class="border-b border-gray-100 pb-6 mb-6">
                <h3 class="text-2xl font-bold text-gray-900 mb-2 flex items-center">
                    <i class="fas fa-search text-green-600 mr-3"></i>Report Details
                </h3>
                <p class="text-gray-600">Tracking ID: <span class="font-mono font-semibold text-green-600">${trackingNum}</span></p>
            </div>

            <div class="grid md:grid-cols-2 gap-8 mb-8">
                <div class="bg-gray-50 rounded-xl p-6">
                    <h4 class="font-semibold text-gray-900 mb-4">Issue Information</h4>
                    <div class="space-y-3">
                        <div class="flex justify-between">
                            <span class="text-gray-600">Location:</span>
                            <span class="font-medium text-gray-900">${data.location}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">Submitted:</span>
                            <span class="font-medium text-gray-900">${new Date(data.created_at).toLocaleDateString()}</span>
                        </div>
                    </div>
                </div>

                <div class="bg-green-50 rounded-xl p-6">
                    <h4 class="font-semibold text-gray-900 mb-4">Current Status</h4>
                    <div class="text-center">
                        <div class="text-3xl font-bold text-green-600 mb-2">${getStatusIcon(data.status)}</div>
                        <div class="text-lg font-semibold text-gray-900 capitalize">${data.status.replace('_', ' ')}</div>
                        <div class="text-sm text-gray-600 mt-1">${getStatusDescription(data.status)}</div>
                    </div>
                </div>
            </div>

            <div class="status-timeline">
                <h4 class="font-semibold text-gray-900 mb-6">Progress Timeline</h4>
                <div class="space-y-6">
                    ${generateTimelineSteps(data)}
                </div>
            </div>
        `;

        document.getElementById('statusDisplay').classList.remove('hidden');
        document.getElementById('statusDisplay').classList.add('animate-slide-up');

    } catch (error) {
        console.error('Error tracking report:', error);
        alert('Error tracking report: ' + error.message);
    }
}

function getStatusIcon(status) {
    const icons = {
        'submitted': '📤',
        'under_review': '🔍',
        'scheduled': '📅',
        'completed': '✅'
    };
    return icons[status] || '⏳';
}

function getStatusDescription(status) {
    const descriptions = {
        'submitted': 'Report received and queued for analysis',
        'under_review': 'AI analysis completed, awaiting prioritization',
        'scheduled': 'Repair work has been scheduled',
        'completed': 'Issue has been resolved'
    };
    return descriptions[status] || 'Processing...';
}

function generateTimelineSteps(data) {
    const steps = [
        { key: 'submitted', title: 'Submitted', desc: 'Report received', timestamp: data.created_at },
        { key: 'under_review', title: 'Under Review', desc: 'AI analysis complete', timestamp: data.status !== 'submitted' ? 'Completed' : null },
        { key: 'scheduled', title: 'Scheduled', desc: 'Repair scheduled', timestamp: ['scheduled', 'completed'].includes(data.status) ? 'Completed' : null },
        { key: 'completed', title: 'Completed', desc: 'Issue resolved', timestamp: data.status === 'completed' ? 'Completed' : null }
    ];

    return steps.map(step => {
        const isActive = data.status === step.key || (data.status === 'completed' && ['submitted', 'under_review', 'scheduled'].includes(step.key));
        const isCompleted = ['submitted', 'under_review', 'scheduled'].includes(step.key) && data.status === 'completed';

        return `
            <div class="timeline-item flex items-center ${isActive || isCompleted ? 'active' : ''}">
                <div class="w-10 h-10 ${isActive || isCompleted ? 'bg-gradient-to-br from-green-500 to-green-600' : 'bg-gray-300'} rounded-full flex items-center justify-center text-white mr-4 flex-shrink-0">
                    <i class="fas ${isCompleted ? 'fa-check' : (isActive ? 'fa-spinner fa-spin' : 'fa-clock')}"></i>
                </div>
                <div class="flex-1">
                    <p class="font-semibold text-gray-900">${step.title}</p>
                    <p class="text-sm text-gray-600">${step.desc}</p>
                    ${step.timestamp ? `<p class="text-xs text-gray-500 mt-1">${step.timestamp}</p>` : ''}
                </div>
            </div>
        `;
    }).join('');
}

// Intersection Observer for animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.animationDelay = '0s';
            entry.target.style.animationFillMode = 'both';
        }
    });
}, observerOptions);

// Observe all animated elements
document.querySelectorAll('.animate-slide-up, .animate-slide-in-left, .animate-slide-in-right, .animate-fade-in').forEach(el => {
    observer.observe(el);
});

// Add navbar scroll effect
window.addEventListener('scroll', () => {
    const navbar = document.querySelector('nav');
    if (window.scrollY > 100) {
        navbar.classList.add('shadow-lg');
    } else {
        navbar.classList.remove('shadow-lg');
    }
});
