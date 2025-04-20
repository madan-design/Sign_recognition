# Sign_recognition
# ✋ Hand Sign Detection System

A real-time hand gesture recognition system built using Python, OpenCV, Flask, and MediaPipe. The system detects specific hand gestures like Hello, Stop, No, Thank You, and Okay, displaying both a live video feed and gesture output via a web-based interface.

## 📌 Features

- 🔴 Real-time camera feed in browser
- 🧠 Gesture detection using MediaPipe hand landmarks
- ✋ Recognizes:
  - Hello (relaxed hand)
  - Stop (all fingers extended)
  - No (one finger pointing)
  - Okay (thumbs up)
  - Thank You (fist)
- 🎯 Toggle skeleton overlay for hand landmarks
- 🔘 Start/Stop camera functionality
- 💡 Clean, responsive HTML/CSS interface

---

## 🧰 Tech Stack

- Frontend: HTML, CSS, JavaScript
- Backend: Flask (Python)
- Computer Vision: OpenCV
- Hand Tracking: MediaPipe

---

## 📁 Folder Structure

hand_sign_detection/
├── app.py
├── hand_gesture_utils.py
├── static/
│   ├── style.css
│   └── js/
│       └── script.js
├── templates/
│   └── index.html
└── README.md

---

## 🚀 Getting Started

### 1. Clone the Repository

git clone https://github.com/your-username/hand-sign-detection.git
cd hand-sign-detection

### 2. Install Dependencies

Make sure Python 3.8+ is installed.

pip install flask opencv-python mediapipe

### 3. Run the App

python app.py

Then open your browser and go to:  
http://127.0.0.1:5000/

---

## 🖥️ Usage

- Click Start Camera to begin streaming.
- Perform hand gestures in front of the webcam.
- Recognized gesture will display below the video.
- Toggle Skeleton Overlay to show/hide hand joints.
- Click Stop Camera to stop streaming.

---

## 📸 Sample Gestures

Gesture       | Sign Detected
--------------|----------------
👋 Waving Hand | Hello
✊ Fist         | Thank You
☝️ One Finger  | No
👍 Thumbs Up   | Okay
🖐️ Open Palm   | Stop

---

## 📦 Packaging as EXE (Optional)

To convert into an executable:

pip install auto-py-to-exe
auto-py-to-exe

- Script: app.py
- Onefile: ✅
- Add folders: templates, static

---
