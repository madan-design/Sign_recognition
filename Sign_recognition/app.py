from flask import Flask, render_template, Response, jsonify
import cv2
import mediapipe as mp
import threading
import numpy as np
import time
import sys
from hand_gesture_utils import detect_gesture

app = Flask(__name__)

frame_lock      = threading.Lock()
gesture_lock    = threading.Lock()
output_frame    = None
current_gesture = ""
is_camera_on    = False
show_skeleton   = False
stop_thread     = False

camera = None  # opened/closed dynamically

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.6,
)
mp_draw        = mp.solutions.drawing_utils
draw_spec_dot  = mp_draw.DrawingSpec(color=(0, 255, 180), thickness=2, circle_radius=3)
draw_spec_line = mp_draw.DrawingSpec(color=(255, 255, 255), thickness=2)

BLANK_FRAME = None

def make_blank_frame():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(frame, "Turn Camera On for Detection", (60, 240),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (100, 100, 100), 2)
    return cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])[1].tobytes()


def update_camera_frames():
    global output_frame, current_gesture, camera, BLANK_FRAME

    BLANK_FRAME = make_blank_frame()

    while not stop_thread:
        if not is_camera_on:
            # Release camera as soon as it's toggled off
            if camera is not None and camera.isOpened():
                camera.release()
                camera = None

            with frame_lock:
                output_frame = BLANK_FRAME
            with gesture_lock:
                current_gesture = ""
            time.sleep(0.05)
            continue

        # Open camera only when toggled on
        if camera is None or not camera.isOpened():
            camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            time.sleep(0.2)  # let camera warm up

        success, frame = camera.read()
        if not success:
            time.sleep(0.01)
            continue

        frame = cv2.flip(frame, 1)
        h, w  = frame.shape[:2]
        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = hands.process(rgb)
        rgb.flags.writeable = True

        gesture_text = ""
        if results.multi_hand_landmarks:
            for handLms in results.multi_hand_landmarks:
                xs = [lm.x * w for lm in handLms.landmark]
                ys = [lm.y * h for lm in handLms.landmark]
                x1 = max(0, int(min(xs)) - 15)
                y1 = max(0, int(min(ys)) - 15)
                x2 = min(w, int(max(xs)) + 15)
                y2 = min(h, int(max(ys)) + 15)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 180), 2)
                if show_skeleton:
                    mp_draw.draw_landmarks(frame, handLms, mp_hands.HAND_CONNECTIONS,
                                           draw_spec_dot, draw_spec_line)
                gesture_text = detect_gesture(handLms)

        with gesture_lock:
            current_gesture = gesture_text

        encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])[1].tobytes()
        with frame_lock:
            output_frame = encoded

    # Thread exiting — release camera
    if camera is not None and camera.isOpened():
        camera.release()
        camera = None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    def generate():
        while True:
            with frame_lock:
                frame_bytes = output_frame
            if frame_bytes is None:
                time.sleep(0.01)
                continue
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.03)
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/gesture')
def gesture():
    with gesture_lock:
        return jsonify(gesture=current_gesture, camera=is_camera_on)


@app.route('/toggle_camera', methods=['POST'])
def toggle_camera():
    global is_camera_on
    is_camera_on = not is_camera_on
    return jsonify(status='ok', camera=is_camera_on)


@app.route('/toggle_skeleton', methods=['POST'])
def toggle_skeleton():
    global show_skeleton
    show_skeleton = not show_skeleton
    return jsonify(status='ok', skeleton=show_skeleton)


if __name__ == '__main__':
    t = threading.Thread(target=update_camera_frames, daemon=True)
    t.start()
    try:
        app.run(debug=False, threaded=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        pass
    finally:
        stop_thread = True
        time.sleep(0.2)
        if camera is not None and camera.isOpened():
            camera.release()
            print("Camera released on exit.")
        sys.exit(0)
