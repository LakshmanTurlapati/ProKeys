// Renderer process JavaScript for ProKeys

let isRunning = false;
let config = null;

// DOM elements
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');
const toggleBtn = document.getElementById('toggle-btn');
const speedSlider = document.getElementById('speed-slider');
const speedValue = document.getElementById('speed-value');

// Initialize
async function init() {
    try {
        // Load configuration
        config = await window.electronAPI.getConfig();
        
        speedSlider.value = config.typing_speed_wpm;
        speedValue.textContent = `${config.typing_speed_wpm} WPM`;
        
        // Check accessibility permission on startup
        const permissionStatus = await window.electronAPI.checkAccessibilityPermission();
        if (!permissionStatus.hasPermission) {
            showPermissionAlert();
        }
        
        // Check initial status
        const status = await window.electronAPI.getProKeysStatus();
        updateUI(status.running);
        
        // Set up event listeners
        setupEventListeners();
    } catch (error) {
        console.error('Initialization error:', error);
    }
}

function setupEventListeners() {
    // Toggle button
    toggleBtn.addEventListener('click', toggleProKeys);
    
    // Version link click
    const versionLink = document.getElementById('version-link');
    versionLink.addEventListener('click', () => {
        window.electronAPI.openExternal('https://github.com/LakshmanTurlapati/ProKeys');
    });
    
    // Speed slider
    speedSlider.addEventListener('input', (e) => {
        const wpm = parseInt(e.target.value);
        speedValue.textContent = `${wpm} WPM`;
        
        // Update config
        config.typing_speed_wpm = wpm;
        config.delay = wpmToDelay(wpm);
        saveConfig();
    });
    
    // Preset buttons
    document.querySelectorAll('.btn-preset').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const speed = parseInt(e.target.dataset.speed);
            speedSlider.value = speed;
            speedValue.textContent = `${speed} WPM`;
            
            config.typing_speed_wpm = speed;
            config.delay = wpmToDelay(speed);
            saveConfig();
        });
    });
    
    // Listen for ProKeys events
    window.electronAPI.onProKeysOutput((data) => {
        console.log('ProKeys output:', data);
    });
    
    window.electronAPI.onProKeysError((data) => {
        console.error('ProKeys error:', data);
        updateUI(false);
    });
    
    window.electronAPI.onProKeysStopped(() => {
        updateUI(false);
    });
}

async function toggleProKeys() {
    try {
        if (isRunning) {
            const result = await window.electronAPI.stopProKeys();
            
            if (result.success) {
                updateUI(false);
            } else {
                console.error('Stop error:', result.error);
            }
        } else {
            const result = await window.electronAPI.startProKeys();
            
            if (result.success) {
                updateUI(true);
            } else {
                console.error('Start error:', result.error);
                // Check if it's a permission error
                if (result.needsPermission || result.error.includes('accessibility') || result.error.includes('permission')) {
                    await requestPermissionWithDialog();
                    // Don't auto-retry - let user try manually after granting permission
                }
            }
        }
    } catch (error) {
        console.error('Toggle error:', error);
    }
}

function updateUI(running) {
    isRunning = running;
    
    if (running) {
        statusDot.classList.remove('stopped');
        statusDot.classList.add('running');
        statusText.textContent = 'Running';
        toggleBtn.textContent = 'Stop ProKeys';
    } else {
        statusDot.classList.remove('running');
        statusDot.classList.add('stopped');
        statusText.textContent = 'Stopped';
        toggleBtn.textContent = 'Start ProKeys';
    }
}

async function saveConfig() {
    await window.electronAPI.saveConfig(config);
}

function wpmToDelay(wpm) {
    // Convert WPM to delay between keystrokes
    const baseDelay = 60.0 / (wpm * 5);
    
    // Add realistic overhead
    let overhead;
    if (wpm < 60) {
        overhead = 0.3;
    } else if (wpm < 120) {
        overhead = 0.25;
    } else if (wpm < 200) {
        overhead = 0.2;
    } else {
        overhead = 0.15;
    }
    
    return baseDelay * (1 + overhead);
}

async function requestPermissionWithDialog() {
    const userResponse = confirm(
        'ProKeys needs accessibility permissions to monitor keyboard input.\n\n' +
        'Click OK to open System Preferences, or Cancel to continue without starting ProKeys.'
    );
    
    if (userResponse) {
        // Request permission (this will show the system dialog)
        const result = await window.electronAPI.requestAccessibilityPermission();
        
        if (!result.hasPermission) {
            // If still no permission, give user instructions
            alert(
                'Please grant accessibility permission in System Preferences:\n\n' +
                '1. Go to System Preferences > Security & Privacy > Privacy\n' +
                '2. Select "Accessibility" from the list\n' +
                '3. Click the lock icon and enter your password\n' +
                '4. Check the box next to "ProKeys"\n' +
                '5. Try starting ProKeys again'
            );
            
            // Wait a bit and check again
            setTimeout(async () => {
                const recheckResult = await window.electronAPI.checkAccessibilityPermission();
                if (recheckResult.hasPermission) {
                    alert('Permission granted! You can now start ProKeys.');
                }
            }, 2000);
        }
        
        return result.hasPermission;
    }
    
    return false;
}

function showPermissionAlert() {
    // Show a non-blocking notification about permissions
    setTimeout(() => {
        const userResponse = confirm(
            'ProKeys requires accessibility permissions to function properly.\n\n' +
            'Would you like to grant permissions now?'
        );
        
        if (userResponse) {
            window.electronAPI.requestAccessibilityPermission();
        }
    }, 1000); // Delay to ensure UI is ready
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Show loading screen for 2 seconds, then expand and show main app
    setTimeout(async () => {
        // Hide loading screen
        const loadingScreen = document.getElementById('loading-screen');
        const mainApp = document.getElementById('main-app');
        
        // Expand window
        await window.electronAPI.expandWindow();
        
        // Wait a bit for window animation, then show main app
        setTimeout(() => {
            loadingScreen.style.display = 'none';
            mainApp.classList.remove('hidden');
            
            // Initialize app after showing
            init();
        }, 300);
        
    }, 2000);
});