from flask import Flask, render_template, Response, request
import cv2
import mediapipe as mp
import threading
import numpy as np
from hand_gesture_utils import detect_gesture

app = Flask(__name__)

camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
frame_lock = threading.Lock()
output_frame = None
is_camera_on = False
show_skeleton = False

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

def update_camera_frames():
    global output_frame, is_camera_on

    while True:
        if not is_camera_on:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, "Turn Camera On for Detection", (30, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2, cv2.LINE_AA)
            with frame_lock:
                output_frame = frame
            continue

        success, frame = camera.read()
        if not success:
            continue

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        gesture_text = ""
        if results.multi_hand_landmarks:
            for handLms in results.multi_hand_landmarks:
                if show_skeleton:
                    mp_draw.draw_landmarks(frame, handLms, mp_hands.HAND_CONNECTIONS)
                gesture_text = detect_gesture(handLms)

        cv2.putText(frame, gesture_text, (10, 460), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 165, 255), 2)
        with frame_lock:
            output_frame = frame.copy()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    def generate():
        global output_frame
        while True:
            with frame_lock:
                if output_frame is None:
                    continue
                ret, buffer = cv2.imencode('.jpg', output_frame)
                frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/toggle_camera', methods=['POST'])
def toggle_camera():
    global is_camera_on
    is_camera_on = not is_camera_on
    return {'status': 'ok', 'camera': is_camera_on}

@app.route('/toggle_skeleton', methods=['POST'])
def toggle_skeleton():
    global show_skeleton
    show_skeleton = not show_skeleton
    return {'status': 'ok', 'skeleton': show_skeleton}

if __name__ == '__main__':
    t = threading.Thread(target=update_camera_frames)
    t.daemon = True
    t.start()
    app.run(debug=True)

