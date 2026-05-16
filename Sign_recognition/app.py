import os
import base64
import numpy as np
import cv2
import mediapipe as mp
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
from hand_gesture_utils import detect_gesture

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sign_recognition_secret'
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='eventlet')

mp_hands   = mp.solutions.hands
hands      = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.6,
)
mp_draw        = mp.solutions.drawing_utils
draw_spec_dot  = mp_draw.DrawingSpec(color=(0, 255, 180), thickness=2, circle_radius=3)
draw_spec_line = mp_draw.DrawingSpec(color=(255, 255, 255), thickness=2)

show_skeleton = False


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/toggle_skeleton', methods=['POST'])
def toggle_skeleton():
    global show_skeleton
    show_skeleton = not show_skeleton
    return jsonify(status='ok', skeleton=show_skeleton)


@socketio.on('frame')
def handle_frame(data):
    """Receive a base64 JPEG frame from the browser, run MediaPipe, return annotated frame + gesture."""
    try:
        img_data = base64.b64decode(data.split(',')[1])
        np_arr   = np.frombuffer(img_data, np.uint8)
        frame    = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is None:
            return

        frame = cv2.flip(frame, 1)
        h, w  = frame.shape[:2]
        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = hands.process(rgb)
        rgb.flags.writeable = True

        gesture_text = ''
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

        # Encode annotated frame back to base64
        _, buffer   = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
        b64_frame   = 'data:image/jpeg;base64,' + base64.b64encode(buffer).decode('utf-8')

        emit('result', {'frame': b64_frame, 'gesture': gesture_text})

    except Exception as e:
        print(f'Frame error: {e}')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
