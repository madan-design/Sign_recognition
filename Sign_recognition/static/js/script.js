const toggleCameraEl   = document.getElementById('toggleCamera');
const toggleSkeletonEl = document.getElementById('toggleSkeleton');
const gestureBadge     = document.getElementById('gestureBadge');
const gestureBadgeMob  = document.getElementById('gestureBadgeMobile');
const cameraOverlay    = document.getElementById('cameraOverlay');
const historyList      = document.getElementById('gestureHistory');

let lastGesture = '';
let isCameraOn  = false;

// ── Camera toggle ──────────────────────────────────────
toggleCameraEl.addEventListener('change', () => {
    fetch('/toggle_camera', { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            isCameraOn = data.camera;
            cameraOverlay.classList.toggle('hidden', isCameraOn);
            if (!isCameraOn) {
                setBadge('—', false);
                lastGesture = '';
            }
        });
});

// ── Skeleton toggle ────────────────────────────────────
toggleSkeletonEl.addEventListener('change', () => {
    fetch('/toggle_skeleton', { method: 'POST' });
});

// ── Poll gesture every 300ms ───────────────────────────
function pollGesture() {
    if (!isCameraOn) return;
    fetch('/gesture')
        .then(r => r.json())
        .then(data => {
            const g = data.gesture || '';
            if (g !== lastGesture) {
                setBadge(g || '—', !!g);
                if (g) addHistory(g);
                lastGesture = g;
            }
        })
        .catch(() => {});
}
setInterval(pollGesture, 300);

// ── Update both desktop + mobile badges ───────────────
function setBadge(text, active) {
    const cls = active ? 'active' : 'idle';

    if (gestureBadge) {
        gestureBadge.textContent = text;
        gestureBadge.className   = 'gesture-badge ' + cls;
    }
    if (gestureBadgeMob) {
        gestureBadgeMob.textContent = text;
        gestureBadgeMob.className   = 'gesture-badge-mobile ' + cls;
    }
}

// ── History log ────────────────────────────────────────
function addHistory(gesture) {
    const empty = historyList.querySelector('.empty-history');
    if (empty) empty.remove();

    const time = new Date().toLocaleTimeString([], {
        hour: '2-digit', minute: '2-digit', second: '2-digit'
    });
    const li = document.createElement('li');
    li.innerHTML = `<span>${gesture}</span><span class="history-time">${time}</span>`;
    historyList.prepend(li);

    while (historyList.children.length > 20)
        historyList.removeChild(historyList.lastChild);
}

// ── Mobile bottom tab switching ────────────────────────
document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;

        // Update active button
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // Show matching panel, hide others
        document.querySelectorAll('.panel-section').forEach(p => {
            p.classList.toggle('hidden', p.id !== 'panel-' + tab);
        });
    });
});
