import math
from collections import deque

# Store previous positions to detect waving
previous_positions = deque(maxlen=10)

def detect_gesture(hand_landmarks):
    landmarks = hand_landmarks.landmark

    def distance(a, b):
        return math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2)

    thumb_tip = landmarks[4]
    index_tip = landmarks[8]
    middle_tip = landmarks[12]
    ring_tip = landmarks[16]
    pinky_tip = landmarks[20]
    palm_base = landmarks[0]

    # Save horizontal motion
    previous_positions.append(palm_base.x)
    if len(previous_positions) == previous_positions.maxlen:
        diff = max(previous_positions) - min(previous_positions)
        if diff > 0.1:
            return "HELLO"

    extended_fingers = [
        distance(index_tip, palm_base) > 0.1,
        distance(middle_tip, palm_base) > 0.1,
        distance(ring_tip, palm_base) > 0.1,
        distance(pinky_tip, palm_base) > 0.1,
    ]

    is_thumb_up = thumb_tip.y < landmarks[3].y
    is_fist = all(distance(tip, palm_base) < 0.07 for tip in [index_tip, middle_tip, ring_tip, pinky_tip])
    is_one_finger = extended_fingers[0] and not any(extended_fingers[1:])
    is_all_fingers = all(extended_fingers)

    if is_one_finger:
        return "NO"
    elif is_all_fingers:
        return "STOP"
    elif is_fist:
        return "THANK YOU"
    elif is_thumb_up:
        return "OKAY"
    else:
        return ""
