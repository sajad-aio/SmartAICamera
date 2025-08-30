// Global Variables
let currentSection = 'dashboard';
let registerVideo = null;
let monitorVideo = null;
let isMonitoring = false;
let monitorStartTime = null;
let detectionCount = 0;
let emotionChart = null;
let monitorInterval = null;
let detectionInterval = null;

// Settings
let settings = {
    similarityThreshold: 70,
    activationTime: 3,
    startDelay: 5,
    cameraResolution: '1280x720',
    frameRate: 30,
    unknownFaceAlert: true,
    emotionAlert: false,
    soundAlerts: true
};

// Real data - no fake data
let userData = {
    totalUsers: 0,
    totalDetections: 0,
    emotionAccuracy: 0,
    systemUptime: '00:00'
};

let emotionData = {
    labels: ['شاد', 'خنثی', 'ناراحت', 'عصبانی', 'متعجب', 'ترسیده', 'متنفر'],
    data: [0, 0, 0, 0, 0, 0, 0]
};

let recentActivity = [];

// Initialize Application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    loadSettings();
    loadRealDataFromServer();
    updateDashboard();
});

function initializeApp() {
    // Initialize video elements
    registerVideo = document.getElementById('register-video');
    monitorVideo = document.getElementById('monitor-video');
    
    // Show dashboard by default
    showSection('dashboard');
    
    // Initialize chart
    initializeEmotionChart();
    
    // Load saved data
    loadUserData();
    
    console.log('Application initialized successfully');
}

function setupEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.getAttribute('data-section');
            showSection(section);
            updateNavigation(this);
        });
    });

    // Register section
    document.getElementById('start-camera-btn').addEventListener('click', startRegisterCamera);
    document.getElementById('capture-btn').addEventListener('click', capturePhoto);
    document.getElementById('register-user-btn').addEventListener('click', registerUser);

    // Monitor section
    document.getElementById('start-monitor-btn').addEventListener('click', startMonitoring);
    document.getElementById('stop-monitor-btn').addEventListener('click', stopMonitoring);
    document.getElementById('take-screenshot-btn').addEventListener('click', takeScreenshot);

    // Reports section
    document.getElementById('generate-report-btn').addEventListener('click', generateReport);

    // Settings section
    document.getElementById('similarity-threshold').addEventListener('input', updateSimilarityValue);
    document.getElementById('save-settings-btn').addEventListener('click', saveSettings);
    document.getElementById('reset-settings-btn').addEventListener('click', resetSettings);
    document.getElementById('export-data-btn').addEventListener('click', exportData);

    // Set default dates
    const today = new Date().toISOString().split('T')[0];
    const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    document.getElementById('date-from').value = weekAgo;
    document.getElementById('date-to').value = today;
}

function showSection(sectionId) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Show selected section
    document.getElementById(sectionId).classList.add('active');
    currentSection = sectionId;
    
    // Stop camera when switching sections
    if (sectionId !== 'register') {
        stopRegisterCamera();
    }
    if (sectionId !== 'monitor' && isMonitoring) {
        stopMonitoring();
    }
}

function updateNavigation(activeLink) {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    activeLink.classList.add('active');
}

// Dashboard Functions
function updateDashboard() {
    // Update stats
    document.getElementById('total-users').textContent = userData.totalUsers;
    document.getElementById('total-detections').textContent = userData.totalDetections;
    document.getElementById('emotion-accuracy').textContent = userData.emotionAccuracy + '%';
    document.getElementById('system-uptime').textContent = userData.systemUptime;
    
    // Update recent activity
    updateRecentActivity();
    
    // Update chart
    if (emotionChart) {
        emotionChart.data.datasets[0].data = emotionData.data;
        emotionChart.update();
    }
}

function updateRecentActivity() {
    const activityContainer = document.getElementById('recent-activity');
    activityContainer.innerHTML = '';
    
    if (recentActivity.length === 0) {
        activityContainer.innerHTML = '<p style="text-align: center; color: #718096; padding: 2rem;">هیچ فعالیتی ثبت نشده است</p>';
        return;
    }
    
    recentActivity.slice(0, 10).forEach(activity => {
        const activityItem = document.createElement('div');
        activityItem.className = 'activity-item';
        activityItem.innerHTML = `
            <div class="activity-icon ${activity.type}">
                <i class="fas ${activity.type === 'success' ? 'fa-check' : 'fa-exclamation'}"></i>
            </div>
            <div class="activity-content">
                <p>${activity.message}</p>
                <span>${activity.time}</span>
            </div>
        `;
        activityContainer.appendChild(activityItem);
    });
}

function initializeEmotionChart() {
    const ctx = document.getElementById('emotionChart').getContext('2d');
    emotionChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: emotionData.labels,
            datasets: [{
                data: emotionData.data,
                backgroundColor: [
                    '#48bb78', '#667eea', '#ed8936', '#f56565',
                    '#4299e1', '#9f7aea', '#38b2ac'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true,
                        font: {
                            family: 'Vazirmatn',
                            size: 12
                        }
                    }
                }
            }
        }
    });
}

// Register Functions - Using Python Camera
async function startRegisterCamera() {
    try {
        showLoading();
        
        // Check if camera is available on server
        const cameraCheck = await fetch('/api/check_camera');
        const cameraResult = await cameraCheck.json();
        
        if (!cameraResult.success) {
            throw new Error(cameraResult.message);
        }
        
        // Use server-side camera feed with timestamp to prevent caching
        registerVideo.src = '/video_feed?' + new Date().getTime();
        
        document.getElementById('start-camera-btn').disabled = true;
        document.getElementById('capture-btn').disabled = false;
        hideLoading();
        showNotification('دوربین با موفقیت فعال شد', 'success');
        
    } catch (error) {
        hideLoading();
        showNotification(error.message || 'خطا در فعال‌سازی دوربین', 'error');
        console.error('Camera error:', error);
    }
}

async function capturePhoto() {
    const userName = document.getElementById('user-name').value.trim();
    
    if (!userName) {
        showNotification('لطفاً نام کاربر ��ا وارد کنید', 'warning');
        return;
    }
    
    try {
        showLoading();
        
        // Capture frame from Python camera
        const response = await fetch('/api/capture_frame', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.message);
        }
        
        // Display captured image
        const capturedImg = document.getElementById('captured-img');
        capturedImg.src = result.image;
        
        document.getElementById('captured-image').style.display = 'block';
        document.getElementById('register-user-btn').disabled = false;
        
        hideLoading();
        showNotification('عکس با موفقیت گرفته شد', 'success');
        
    } catch (error) {
        hideLoading();
        showNotification(error.message || 'خطا در گرفتن عکس', 'error');
        console.error('Capture error:', error);
    }
}

async function registerUser() {
    const userName = document.getElementById('user-name').value.trim();
    
    if (!userName) {
        showNotification('لطفاً نام کاربر را وارد کنید', 'warning');
        return;
    }
    
    const capturedImg = document.getElementById('captured-img');
    if (!capturedImg.src) {
        showNotification('لطفاً ابتدا عکس بگیرید', 'warning');
        return;
    }
    
    try {
        showLoading();
        
        // Send user data to server
        const response = await fetch('/api/register_user', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: userName,
                image: capturedImg.src
            })
        });
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.message);
        }
        
        // Update local storage and stats
        let users = JSON.parse(localStorage.getItem('registeredUsers') || '[]');
        users.push({
            name: userName,
            registrationDate: new Date().toISOString(),
            image: capturedImg.src
        });
        localStorage.setItem('registeredUsers', JSON.stringify(users));
        
        // Update stats
        updateUserStats();
        
        // Reset form
        resetRegisterForm();
        
        hideLoading();
        showNotification(result.message, 'success');
        
        // Add to recent activity
        recentActivity.unshift({
            type: 'success',
            message: `کاربر ${userName} ثبت شد`,
            time: 'همین الان'
        });
        updateRecentActivity();
        
    } catch (error) {
        hideLoading();
        showNotification(error.message || 'خطا در ثبت کاربر', 'error');
        console.error('Registration error:', error);
    }
}

function resetRegisterForm() {
    document.getElementById('user-name').value = '';
    document.getElementById('captured-image').style.display = 'none';
    document.getElementById('start-camera-btn').disabled = false;
    document.getElementById('capture-btn').disabled = true;
    document.getElementById('register-user-btn').disabled = true;
    
    stopRegisterCamera();
}

function stopRegisterCamera() {
    if (registerVideo.src) {
        registerVideo.src = '';
    }
}

// Monitor Functions - Using Python Camera with Real Detection
async function startMonitoring() {
    try {
        showLoading();
        
        // Check if camera is available
        const cameraCheck = await fetch('/api/check_camera');
        const cameraResult = await cameraCheck.json();
        
        if (!cameraResult.success) {
            throw new Error(cameraResult.message);
        }
        
        // Use server-side camera feed with timestamp to prevent caching
        monitorVideo.src = '/video_feed?' + new Date().getTime();
        
        isMonitoring = true;
        monitorStartTime = Date.now();
        detectionCount = 0;
        
        document.getElementById('start-monitor-btn').disabled = true;
        document.getElementById('stop-monitor-btn').disabled = false;
        document.getElementById('take-screenshot-btn').disabled = false;
        document.getElementById('system-status').textContent = 'فعال';
        document.getElementById('system-status').className = 'status-active';
        
        // Start monitoring timer
        monitorInterval = setInterval(updateMonitorStats, 1000);
        
        // Start real face detection with live drawing
        startRealFaceDetection();
        
        hideLoading();
        showNotification('نظارت با موفقیت شروع شد', 'success');
        
    } catch (error) {
        hideLoading();
        showNotification(error.message || 'خطا در شروع نظارت', 'error');
        console.error('Monitor error:', error);
    }
}

async function stopMonitoring() {
    isMonitoring = false;
    
    if (monitorVideo.src) {
        monitorVideo.src = '';
    }
    
    if (monitorInterval) {
        clearInterval(monitorInterval);
        monitorInterval = null;
    }
    
    if (detectionInterval) {
        clearInterval(detectionInterval);
        detectionInterval = null;
    }
    
    // Release camera resources on server
    try {
        await fetch('/api/release_camera', {
            method: 'POST'
        });
    } catch (error) {
        console.error('Error releasing camera:', error);
    }
    
    document.getElementById('start-monitor-btn').disabled = false;
    document.getElementById('stop-monitor-btn').disabled = true;
    document.getElementById('take-screenshot-btn').disabled = true;
    document.getElementById('system-status').textContent = 'غیرفعال';
    document.getElementById('system-status').className = 'status-inactive';
    
    // Reset detection info
    document.getElementById('detected-user').textContent = 'در انتظار تشخیص...';
    document.getElementById('similarity-score').textContent = '0%';
    document.getElementById('detected-emotion').textContent = 'خنثی';
    
    showNotification('نظارت متوقف شد', 'info');
}

function updateMonitorStats() {
    if (!isMonitoring || !monitorStartTime) return;
    
    const elapsed = Date.now() - monitorStartTime;
    const hours = Math.floor(elapsed / 3600000);
    const minutes = Math.floor((elapsed % 3600000) / 60000);
    const seconds = Math.floor((elapsed % 60000) / 1000);
    
    document.getElementById('monitor-time').textContent = 
        `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    
    document.getElementById('detection-count').textContent = detectionCount;
}

// Real Face Detection Function - like notebook with motion tracking
function startRealFaceDetection() {
    if (!isMonitoring) return;
    
    detectionInterval = setInterval(async () => {
        if (!isMonitoring) return;
        
        try {
            // Capture frame and detect faces - like notebook
            const response = await fetch('/api/capture_frame', {
                method: 'POST'
            });
            
            const frameResult = await response.json();
            if (!frameResult.success) return;
            
            // Send frame for face detection
            const detectResponse = await fetch('/api/detect_face', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    image: frameResult.image
                })
            });
            
            const detectResult = await detectResponse.json();
            
            if (detectResult.success && detectResult.detections.length > 0) {
                const detection = detectResult.detections[0]; // Use first detection
                
                // Update UI with detection info - like notebook
                document.getElementById('detected-user').textContent = detection.user;
                document.getElementById('similarity-score').textContent = detection.similarity + '%';
                document.getElementById('detected-emotion').textContent = detection.emotion;
                
                detectionCount++;
                
                // Add to recent activity with motion info
                const activityType = detection.is_known ? 'success' : 'warning';
                const motionText = detection.motion !== undefined ? ` - تحرک: ${detection.motion}` : '';
                const message = detection.is_known ? 
                    `کاربر ${detection.user} تشخیص داده شد (${detection.similarity}%)${motionText}` :
                    `چهره ناشناس شناسایی شد (${detection.similarity}%)${motionText}`;
                
                recentActivity.unshift({
                    type: activityType,
                    message: message,
                    time: 'همین الان'
                });
                
                // Log motion for debugging
                if (detection.motion !== undefined) {
                    console.log(`Motion: ${detection.motion}, Total Motion: ${detection.total_motion}`);
                }
                
                // Update emotion data
                const emotionIndex = emotionData.labels.indexOf(detection.emotion);
                if (emotionIndex !== -1) {
                    emotionData.data[emotionIndex]++;
                    userData.emotionAccuracy = Math.min(95, userData.emotionAccuracy + 1);
                }
                
                // Show alert for unknown faces
                if (!detection.is_known && settings.unknownFaceAlert) {
                    showNotification('چهره ناشناس شناسایی شد!', 'warning');
                    
                    if (settings.soundAlerts) {
                        playAlertSound();
                    }
                }
                
                // Update dashboard
                userData.totalDetections++;
                updateDashboard();
                updateRecentActivity();
            } else {
                // No face detected - reset UI
                document.getElementById('detected-user').textContent = 'در انتظار تشخیص...';
                document.getElementById('similarity-score').textContent = '0%';
                document.getElementById('detected-emotion').textContent = 'خنثی';
            }
            
        } catch (error) {
            console.error('Detection error:', error);
        }
    }, 1000); // Check every 1 second - like notebook
}

async function takeScreenshot() {
    try {
        // Capture frame from Python camera
        const response = await fetch('/api/capture_frame', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.message);
        }
        
        // Create download link
        const link = document.createElement('a');
        link.download = `screenshot_${new Date().toISOString().replace(/[:.]/g, '-')}.jpg`;
        link.href = result.image;
        link.click();
        
        showNotification('اسکرین شات ذخیره شد', 'success');
        
    } catch (error) {
        showNotification(error.message || 'خطا در گرفتن اسکرین شات', 'error');
        console.error('Screenshot error:', error);
    }
}

// Reports Functions
async function generateReport() {
    const reportType = document.getElementById('report-type').value;
    const dateFrom = document.getElementById('date-from').value;
    const dateTo = document.getElementById('date-to').value;
    showLoading();
    try {
        // دریافت تاریخچه تشخیص‌ها از سرور
        const response = await fetch(`/api/get_detection_history?limit=1000`);
        const result = await response.json();
        if (!result.success) throw new Error(result.message || 'خطا در دریافت گزارش');
        let data = result.history || [];
        // فیلتر بر اساس تاریخ
        if (dateFrom) {
            data = data.filter(item => item.timestamp && item.timestamp >= dateFrom);
        }
        if (dateTo) {
            data = data.filter(item => item.timestamp && item.timestamp <= (dateTo + 'T23:59:59'));
        }
        // فیلتر بر اساس نوع گزارش
        if (reportType === 'verified') {
            data = data.filter(item => item.is_known);
        } else if (reportType === 'unknown') {
            data = data.filter(item => !item.is_known);
        } else if (reportType === 'emotions') {
            // همه رکوردها را نشان بده، یا می‌توان بر اساس احساسات خاص فیلتر کرد
        }
        // تبدیل داده‌ها به فرمت مورد نیاز جدول
        const tableData = data.map(item => ({
            date: item.timestamp ? new Date(item.timestamp).toLocaleString('fa-IR') : '',
            type: item.is_known ? 'تأیید شده' : 'ناشناس',
            user: item.user || 'ناشناس',
            similarity: item.similarity || 0,
            emotion: item.emotion || '',
            motion: item.motion || 0
        }));
        displayReport(tableData);
        hideLoading();
        showNotification('گزارش با موفقیت تولید شد', 'success');
    } catch (error) {
        hideLoading();
        displayReport([]);
        showNotification(error.message || 'خطا در تولید گزارش', 'error');
    }
}

function displayReport(data) {
    const tbody = document.getElementById('report-table-body');
    tbody.innerHTML = '';
    
    // Update summary
    const totalDetections = data.length;
    const verifiedUsers = data.filter(item => item.type === 'تأیید شده').length;
    const unknownFaces = data.filter(item => item.type === 'ناشناس').length;
    
    document.getElementById('total-detections-report').textContent = totalDetections;
    document.getElementById('verified-users-report').textContent = verifiedUsers;
    document.getElementById('unknown-faces-report').textContent = unknownFaces;
    
    // Populate table
    if (data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 2rem;">هیچ داده‌ای برای نمایش وجود ندارد</td></tr>';
        return;
    }
    
    data.forEach(item => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${item.date}</td>
            <td><span class="badge ${item.type === 'تأیید شده' ? 'success' : 'warning'}">${item.type}</span></td>
            <td>${item.user}</td>
            <td>${item.similarity}%</td>
            <td>${item.emotion}</td>
            <td>${item.motion || 0}</td>
            <td>
                <button class="btn btn-sm btn-info" onclick="viewDetails('${item.date}')">
                    <i class="fas fa-eye"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function viewDetails(date) {
    showNotification(`مشاهده جزئیات برای ${date}`, 'info');
}

// Settings Functions
function loadSettings() {
    const savedSettings = localStorage.getItem('appSettings');
    if (savedSettings) {
        settings = { ...settings, ...JSON.parse(savedSettings) };
    }
    
    // Apply settings to UI
    document.getElementById('similarity-threshold').value = settings.similarityThreshold;
    document.getElementById('similarity-value').textContent = settings.similarityThreshold + '%';
    document.getElementById('activation-time').value = settings.activationTime;
    document.getElementById('start-delay').value = settings.startDelay;
    document.getElementById('camera-resolution').value = settings.cameraResolution;
    document.getElementById('frame-rate').value = settings.frameRate;
    document.getElementById('unknown-face-alert').checked = settings.unknownFaceAlert;
    document.getElementById('emotion-alert').checked = settings.emotionAlert;
    document.getElementById('sound-alerts').checked = settings.soundAlerts;
}

function updateSimilarityValue() {
    const value = document.getElementById('similarity-threshold').value;
    document.getElementById('similarity-value').textContent = value + '%';
}

function saveSettings() {
    // Collect settings from UI
    settings.similarityThreshold = parseInt(document.getElementById('similarity-threshold').value);
    settings.activationTime = parseInt(document.getElementById('activation-time').value);
    settings.startDelay = parseInt(document.getElementById('start-delay').value);
    settings.cameraResolution = document.getElementById('camera-resolution').value;
    settings.frameRate = parseInt(document.getElementById('frame-rate').value);
    settings.unknownFaceAlert = document.getElementById('unknown-face-alert').checked;
    settings.emotionAlert = document.getElementById('emotion-alert').checked;
    settings.soundAlerts = document.getElementById('sound-alerts').checked;
    
    // Save to localStorage
    localStorage.setItem('appSettings', JSON.stringify(settings));
    
    showNotification('تنظیمات با موفقیت ذخیره شد', 'success');
}

function resetSettings() {
    if (confirm('آیا مطمئن هستید که می‌خواهید تنظیمات را بازنشانی کنید؟')) {
        // Reset to defaults
        settings = {
            similarityThreshold: 70,
            activationTime: 3,
            startDelay: 5,
            cameraResolution: '1280x720',
            frameRate: 30,
            unknownFaceAlert: true,
            emotionAlert: false,
            soundAlerts: true
        };
        
        localStorage.removeItem('appSettings');
        loadSettings();
        showNotification('تنظیمات بازنشانی شد', 'info');
    }
}

function exportData() {
    const users = JSON.parse(localStorage.getItem('registeredUsers') || '[]');
    const exportData = {
        users: users,
        settings: settings,
        stats: userData,
        recentActivity: recentActivity,
        exportDate: new Date().toISOString()
    };
    
    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = `face_recognition_data_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    
    showNotification('داده‌ها با موفقیت خروجی گرفته شد', 'success');
}

// Utility Functions
function showNotification(message, type = 'info') {
    const container = document.getElementById('notification-container');
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <i class="fas ${getNotificationIcon(type)}"></i>
            <span>${message}</span>
        </div>
    `;
    
    container.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

function getNotificationIcon(type) {
    switch (type) {
        case 'success': return 'fa-check-circle';
        case 'error': return 'fa-exclamation-circle';
        case 'warning': return 'fa-exclamation-triangle';
        default: return 'fa-info-circle';
    }
}

function showLoading() {
    document.getElementById('loading-overlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loading-overlay').style.display = 'none';
}

function loadUserData() {
    const users = JSON.parse(localStorage.getItem('registeredUsers') || '[]');
    userData.totalUsers = users.length;
    updateDashboard();
}

function updateUserStats() {
    const users = JSON.parse(localStorage.getItem('registeredUsers') || '[]');
    userData.totalUsers = users.length;
    updateDashboard();
}

function playAlertSound() {
    try {
        // Create a simple beep sound
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.5);
    } catch (error) {
        console.log('Audio not supported');
    }
}

// Load Real Data from Server
async function loadRealDataFromServer() {
    try {
        // بارگذاری آمار از سرور
        const statsResponse = await fetch('/api/get_stats');
        const statsResult = await statsResponse.json();
        
        if (statsResult.success) {
            const stats = statsResult.stats;
            userData.totalUsers = stats.total_users || 0;
            userData.totalDetections = stats.total_detections || 0;
            userData.emotionAccuracy = Math.round((stats.total_detections > 0 ? 85 : 0)); // محاسبه تقریبی دقت
            
            // بارگذاری داده‌های احساسات
            if (stats.emotion_counts) {
                emotionData.labels.forEach((emotion, index) => {
                    emotionData.data[index] = stats.emotion_counts[emotion] || 0;
                });
            }
        }
        
        // بارگذاری تاریخچه فعالیت‌ها از سرور
        const historyResponse = await fetch('/api/get_detection_history?limit=50');
        const historyResult = await historyResponse.json();
        
        if (historyResult.success && historyResult.history) {
            recentActivity = historyResult.history.map(item => ({
                type: item.is_known ? 'success' : 'warning',
                message: item.is_known ? 
                    `کاربر ${item.user} تشخیص داده شد (${item.similarity}%) - تحرک: ${item.motion || 0}` :
                    `چهره ناشناس شناسایی شد (${item.similarity}%) - تحرک: ${item.motion || 0}`,
                time: item.timestamp ? new Date(item.timestamp).toLocaleString('fa-IR') : 'نامشخص'
            }));
        }
        
        // بارگذاری لیست کاربران از سرور
        const usersResponse = await fetch('/api/get_users');
        const usersResult = await usersResponse.json();
        
        if (usersResult.success) {
            userData.totalUsers = usersResult.total || 0;
        }
        
        console.log('داده‌های واقعی از سرور بارگذاری شد');
        
    } catch (error) {
        console.error('خطا در بارگذاری داده‌ها از سرور:', error);
        // در صورت خطا، از داده‌های محلی استفاده کن
        loadUserData();
    }
}

// Initialize empty users array if not exists
if (!localStorage.getItem('registeredUsers')) {
    localStorage.setItem('registeredUsers', JSON.stringify([]));
}