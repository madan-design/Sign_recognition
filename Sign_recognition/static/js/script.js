let isCameraOn = false;
let isSkeletonOn = false;

document.getElementById('toggleCamera').addEventListener('change', () => {
    fetch('/toggle_camera', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            isCameraOn = data.camera;
            document.getElementById('overlayText').style.display = isCameraOn ? 'none' : 'block';
        });
});

document.getElementById('toggleSkeleton').addEventListener('change', () => {
    fetch('/toggle_skeleton', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            isSkeletonOn = data.skeleton;
        });
});
