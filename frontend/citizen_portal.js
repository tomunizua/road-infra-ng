// --- API Configuration ---
let API_BASE_URL = 'https://roadwatch-ng.onrender.com';
if (typeof API_CONFIG !== 'undefined') {
    API_BASE_URL = API_CONFIG.getApiUrl();
} 

// Mobile menu toggle
function toggleMobileMenu() {
    const menu = document.getElementById('mobileMenu');
    const overlay = document.getElementById('mobileMenuOverlay');
    if (menu && overlay) {
        menu.classList.toggle('active');
        overlay.classList.toggle('active');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const overlay = document.getElementById('mobileMenuOverlay');
    if (overlay) {
        overlay.addEventListener('click', function() {
            const menu = document.getElementById('mobileMenu');
            if (menu) {
                menu.classList.remove('active');
                this.classList.remove('active');
            }
        });
    }
});

document.addEventListener('click', function(e) {
    const menu = document.getElementById('mobileMenu');
    const overlay = document.getElementById('mobileMenuOverlay');
    const hamburger = document.querySelector('button[onclick="toggleMobileMenu()"]');

    if (!menu || !overlay || !hamburger) return;
    if (e.target === overlay) {
        menu.classList.remove('active');
        overlay.classList.remove('active');
        return;
    }
    if (!menu.contains(e.target) && !hamburger.contains(e.target) && e.target !== hamburger) {
        menu.classList.remove('active');
        overlay.classList.remove('active');
    }
    if (e.target.tagName === 'A' && menu.contains(e.target)) {
        menu.classList.remove('active');
        overlay.classList.remove('active');
    }
});

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
        document.getElementById('mobileMenu').classList.remove('active');
    });
});

let currentStream = null;
let gpsCoordinates = null;

function restoreTrackingNumberFromStorage() {
    const savedTrackingNumber = localStorage.getItem('lastTrackingNumber');
    const savedTime = localStorage.getItem('lastTrackingNumberTime');

    if (savedTrackingNumber && savedTime) {
        const timeAgo = Date.now() - parseInt(savedTime);
        if (timeAgo >= 24 * 60 * 60 * 1000) {
            localStorage.removeItem('lastTrackingNumber');
            localStorage.removeItem('lastTrackingNumberTime');
        }
    }
}

document.addEventListener('DOMContentLoaded', restoreTrackingNumberFromStorage);

// Camera functions
document.addEventListener('DOMContentLoaded', function() {
    const cameraBtn = document.getElementById('cameraBtn');
    if (cameraBtn) {
        cameraBtn.addEventListener('click', async function() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
                currentStream = stream;
                const video = document.getElementById('cameraPreview');
                video.srcObject = stream;
                video.play();
                document.getElementById('uploadOptions').style.display = 'none';
                video.style.display = 'block';
                document.getElementById('cameraControls').style.display = 'block';
            } catch (error) {
                console.error('Camera access denied:', error);
                alert('Camera access is required to take photos. Please allow camera access or use the upload option.');
            }
        });
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const captureBtn = document.getElementById('captureBtn');
    if (captureBtn) {
        captureBtn.addEventListener('click', function() {
            const video = document.getElementById('cameraPreview');
            const canvas = document.getElementById('cameraCanvas');
            const ctx = canvas.getContext('2d');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            ctx.drawImage(video, 0, 0);
            canvas.toBlob(function(blob) {
                const file = new File([blob], 'camera-photo.jpg', { type: 'image/jpeg' });
                const dt = new DataTransfer();
                dt.items.add(file);
                document.getElementById('photoInput').files = dt.files;
                const preview = document.getElementById('photoPreview');
                preview.src = canvas.toDataURL();
                document.getElementById('previewContainer').style.display = 'block';
                document.getElementById('uploadOptions').style.display = 'none';
                stopCamera();
            }, 'image/jpeg', 0.8);
        });
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const retakeBtn = document.getElementById('retakeBtn');
    if (retakeBtn) {
        retakeBtn.addEventListener('click', function() {
            const video = document.getElementById('cameraPreview');
            document.getElementById('previewContainer').style.display = 'none';
            document.getElementById('photoPreview').src = '';
            document.getElementById('photoInput').value = '';
            if (currentStream) video.play();
            document.getElementById('uploadOptions').style.display = 'block';
        });
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const cancelCameraBtn = document.getElementById('cancelCameraBtn');
    if (cancelCameraBtn) cancelCameraBtn.addEventListener('click', stopCamera);
});

function stopCamera() {
    if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
        currentStream = null;
    }
    document.getElementById('cameraPreview').style.display = 'none';
    document.getElementById('cameraControls').style.display = 'none';
    if (document.getElementById('previewContainer').style.display !== 'block') {
        document.getElementById('uploadOptions').style.display = 'block';
    }
}

// Location logic
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

function getLGAFromCoordinates(lat, lng) {
    for (const [lga, bounds] of Object.entries(lagosLGABoundaries)) {
        if (lat >= bounds.lat[0] && lat <= bounds.lat[1] && lng >= bounds.lng[0] && lng <= bounds.lng[1]) {
            return lga;
        }
    }
    return null;
}

document.addEventListener('DOMContentLoaded', function() {
    const detectLocationBtn = document.getElementById('detectLocationBtn');
    if (detectLocationBtn) {
        detectLocationBtn.addEventListener('click', function() {
            const button = this;
            const spinner = document.getElementById('locationSpinner');
            button.disabled = true;
            spinner.style.display = 'inline-block';

            if (!navigator.geolocation) {
                alert('Geolocation is not supported by this browser.');
                button.disabled = false;
                spinner.style.display = 'none';
                return;
            }

            navigator.geolocation.getCurrentPosition(
                function(position) {
                    const lat = position.coords.latitude;
                    const lng = position.coords.longitude;
                    gpsCoordinates = { lat, lng };
                    document.getElementById('gpsCoords').textContent = `Lat: ${lat.toFixed(6)}, Lng: ${lng.toFixed(6)}`;
                    
                    const detectedLGAName = getLGAFromCoordinates(lat, lng);
                    const detectedLGA = document.getElementById('detectedLGA');
                    if (detectedLGAName) {
                        detectedLGA.innerHTML = `<strong>LGA Detected:</strong> ${detectedLGAName}`;
                        document.getElementById('lga').value = detectedLGAName;
                    } else {
                        detectedLGA.innerHTML = `<strong>Location Outside Lagos LGAs</strong> - Please select manually`;
                    }
                    document.getElementById('gpsDisplay').style.display = 'block';
                    button.innerHTML = 'Location Detected Successfully';
                    button.style.background = 'linear-gradient(135deg, #16a34a 0%, #15803d 100%)';
                    spinner.style.display = 'none';
                },
                function(error) {
                    alert('Unable to get location. Please try again.');
                    button.disabled = false;
                    spinner.style.display = 'none';
                },
                { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
            );
        });
    }
});

// Photo handling
document.addEventListener('DOMContentLoaded', function() {
    const photoInput = document.getElementById('photoInput');
    if (photoInput) {
        photoInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(event) {
                    document.getElementById('photoPreview').src = event.target.result;
                    document.getElementById('previewContainer').style.display = 'block';
                    document.getElementById('uploadOptions').style.display = 'none';
                };
                reader.readAsDataURL(file);
            }
        });
    }
    document.getElementById('changePhotoBtn')?.addEventListener('click', () => document.getElementById('photoInput').click());
    document.getElementById('removePhotoBtn')?.addEventListener('click', () => {
        document.getElementById('previewContainer').style.display = 'none';
        document.getElementById('photoInput').value = '';
        document.getElementById('uploadOptions').style.display = 'block';
    });
});

// Form Submission
async function handleReportSubmit(e) {
    e.preventDefault();
    const submitButton = e.target.querySelector('button[type="submit"]');
    const spinner = document.getElementById('submitSpinner');
    const form = this;

    submitButton.disabled = true;
    spinner.style.display = 'inline-block';

    try {
        if (!document.getElementById('consentCheckbox').checked) throw new Error('Please accept privacy policy');
        
        const location = document.getElementById('location').value.trim();
        const lga = document.getElementById('lga').value;
        if (!location || !lga) throw new Error('Location and LGA are required');

        // --- NEW: Get Visual Size Selection ---
        const sizeElement = document.querySelector('input[name="damageSize"]:checked');
        if (!sizeElement) {
            throw new Error('Please select the approximate size of the damage');
        }
        const damageSize = sizeElement.value;
        // --------------------------------------

        const photoFile = document.getElementById('photoInput').files[0];
        if (!photoFile) throw new Error('Please select a photo');

        const reader = new FileReader();
        const photoBase64 = await new Promise((resolve, reject) => {
            reader.onload = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsDataURL(photoFile);
        });

        const payload = {
            location: `${location}, ${lga} LGA, Lagos`,
            lga: lga,
            state: 'Lagos',
            description: document.getElementById('description').value,
            contact: document.getElementById('phone').value,
            photo: photoBase64,
            gps_coordinates: gpsCoordinates,
            size: damageSize // Include size in payload
        };

        const response = await fetch(`${API_BASE_URL}/api/submit-report`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const result = await response.json();
        if (!response.ok) throw new Error(result.error || 'Server error');

        if (result.tracking_number) {
            document.getElementById('trackingNumber').textContent = result.tracking_number;
            localStorage.setItem('lastTrackingNumber', result.tracking_number);
            localStorage.setItem('lastTrackingNumberTime', Date.now().toString());
        }

        const successMessage = document.getElementById('successMessage');
        successMessage.style.display = 'block';
        successMessage.scrollIntoView({ behavior: 'smooth', block: 'center' });

        // Add close handler
        if (!successMessage.querySelector('.close-btn')) {
            const closeBtn = document.createElement('button');
            closeBtn.className = 'close-btn absolute top-2 right-2 text-green-800 hover:text-green-900 text-2xl font-bold';
            closeBtn.innerHTML = '&times;';
            closeBtn.onclick = () => {
                successMessage.style.display = 'none';
                form.reset();
                document.getElementById('previewContainer').style.display = 'none';
                document.getElementById('uploadOptions').style.display = 'block';
                gpsCoordinates = null;
            };
            successMessage.style.position = 'relative';
            successMessage.appendChild(closeBtn);
        }

    } catch (error) {
        console.error(error);
        alert(error.message);
    } finally {
        submitButton.disabled = false;
        spinner.style.display = 'none';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const reportForm = document.getElementById('reportForm');
    if (reportForm) reportForm.addEventListener('submit', handleReportSubmit);
});

// Track Report
async function trackReport() {
    const trackingNum = document.getElementById('trackingInput').value.trim();
    if (!trackingNum) return alert('Please enter a tracking number');

    try {
        const response = await fetch(`${API_BASE_URL}/api/track/${trackingNum}`);
        if (!response.ok) return alert('Report not found');
        const data = await response.json();

        document.getElementById('statusDisplay').innerHTML = `
            <div class="border-b border-gray-100 pb-6 mb-6">
                <h3 class="text-2xl font-bold text-gray-900 mb-2">Report Details</h3>
                <p class="text-gray-600">Tracking ID: <span class="font-mono font-semibold text-green-600">${trackingNum}</span></p>
            </div>
            <div class="grid md:grid-cols-2 gap-8 mb-8">
                <div class="bg-gray-50 rounded-xl p-6">
                    <h4 class="font-semibold text-gray-900 mb-4">Issue Info</h4>
                    <div class="space-y-3">
                        <div class="flex justify-between"><span class="text-gray-600">Location:</span><span class="font-medium">${data.location}</span></div>
                        <div class="flex justify-between"><span class="text-gray-600">Status:</span><span class="font-medium capitalize">${data.status.replace('_', ' ')}</span></div>
                    </div>
                </div>
                <div class="bg-green-50 rounded-xl p-6 text-center">
                    <div class="text-3xl font-bold text-green-600 mb-2">${getStatusIcon(data.status)}</div>
                    <div class="text-lg font-semibold capitalize">${data.status.replace('_', ' ')}</div>
                </div>
            </div>
        `;
        document.getElementById('statusDisplay').style.display = 'block';
    } catch (error) {
        alert('Error tracking report: ' + error.message);
    }
}

function getStatusIcon(status) {
    const icons = { 'submitted': 'Submitted', 'under_review': 'Reviewing', 'scheduled': 'Scheduled', 'completed': 'Complete' };
    return icons[status] || 'Processing';
}

// Animations
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.animationDelay = '0s';
            entry.target.style.animationFillMode = 'both';
        }
    });
}, { threshold: 0.1 });

document.querySelectorAll('.animate-slide-up, .animate-slide-in-left, .animate-slide-in-right, .animate-fade-in').forEach(el => observer.observe(el));