const socket         = io();
const toggleCameraEl = document.getElementById('toggleCamera');
const toggleSkelEl   = document.getElementById('toggleSkeleton');
const gestureBadge   = document.getElementById('gestureBadge');
const gestureBadgeMob= document.getElementById('gestureBadgeMobile');
const cameraOverlay  = document.getElementById('cameraOverlay');
const historyList    = document.getElementById('gestureHistory');
const rawVideo       = document.getElementById('rawVideo');
const captureCanvas  = document.getElementById('captureCanvas');
const displayCanvas  = document.getElementById('displayCanvas');
const ctx            = displayCanvas.getContext('2d');

let isCameraOn  = false;
let lastGesture = '';
let stream      = null;
let sending     = false;

// ── Camera toggle ──────────────────────────────────────
toggleCameraEl.addEventListener('change', async () => {
    isCameraOn = toggleCameraEl.checked;

    if (isCameraOn) {
        try {
            stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 640, height: 480, facingMode: 'user' },
                audio: false
            });
            rawVideo.srcObject = stream;
            await rawVideo.play();

            // Match canvas sizes to video
            displayCanvas.width  = captureCanvas.width  = 640;
            displayCanvas.height = captureCanvas.height = 480;

            cameraOverlay.classList.add('hidden');
            startSendingFrames();
        } catch (err) {
            console.error('Camera error:', err);
            toggleCameraEl.checked = false;
            isCameraOn = false;
            alert('Could not access camera: ' + err.message);
        }
    } else {
        stopCamera();
    }
});

// ── Skeleton toggle ────────────────────────────────────
toggleSkelEl.addEventListener('change', () => {
    fetch('/toggle_skeleton', { method: 'POST' });
});

// ── Send frames to server via WebSocket ───────────────
function startSendingFrames() {
    if (sending) return;
    sending = true;

    function sendFrame() {
        if (!isCameraOn) { sending = false; return; }
        if (rawVideo.readyState === rawVideo.HAVE_ENOUGH_DATA) {
            const capCtx = captureCanvas.getContext('2d');
            capCtx.drawImage(rawVideo, 0, 0, 640, 480);
            const b64 = captureCanvas.toDataURL('image/jpeg', 0.7);
            socket.emit('frame', b64);
        }
        // ~20 fps
        setTimeout(sendFrame, 50);
    }
    sendFrame();
}

// ── Receive annotated frame + gesture from server ─────
socket.on('result', (data) => {
    // Draw annotated frame on display canvas
    const img = new Image();
    img.onload = () => ctx.drawImage(img, 0, 0);
    img.src = data.frame;

    // Update gesture badge
    const g = data.gesture || '';
    if (g !== lastGesture) {
        setBadge(g || '—', !!g);
        if (g) addHistory(g);
        lastGesture = g;
    }
});

// ── Stop camera & release stream ──────────────────────
function stopCamera() {
    isCameraOn = false;
    sending    = false;
    if (stream) {
        stream.getTracks().forEach(t => t.stop());
        stream = null;
    }
    rawVideo.srcObject = null;
    ctx.clearRect(0, 0, displayCanvas.width, displayCanvas.height);
    cameraOverlay.classList.remove('hidden');
    setBadge('—', false);
    lastGesture = '';
}

// ── Badge update ───────────────────────────────────────
function setBadge(text, active) {
    const cls = active ? 'active' : 'idle';
    if (gestureBadge)    { gestureBadge.textContent    = text; gestureBadge.className    = 'gesture-badge ' + cls; }
    if (gestureBadgeMob) { gestureBadgeMob.textContent = text; gestureBadgeMob.className = 'gesture-badge-mobile ' + cls; }
}

// ── History log ────────────────────────────────────────
function addHistory(gesture) {
    const empty = historyList.querySelector('.empty-history');
    if (empty) empty.remove();

    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const li   = document.createElement('li');
    li.innerHTML = `<span>${gesture}</span><span class="history-time">${time}</span>`;
    historyList.prepend(li);
    while (historyList.children.length > 20) historyList.removeChild(historyList.lastChild);
}

// ── Mobile tab switching ───────────────────────────────
// Only apply tab hiding on mobile screens
function initTabs() {
    const isMobile = window.innerWidth <= 600;
    if (isMobile) {
        // Hide gestures panel by default on mobile
        document.getElementById('panel-gestures').classList.add('hidden');
    }

    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            document.querySelectorAll('.panel-section').forEach(p => {
                p.classList.toggle('hidden', p.id !== 'panel-' + btn.dataset.tab);
            });
        });
    });
}
initTabs();
window.addEventListener('resize', () => {
    if (window.innerWidth > 600) {
        // On desktop always show both panels
        document.querySelectorAll('.panel-section').forEach(p => p.classList.remove('hidden'));
    }
});
