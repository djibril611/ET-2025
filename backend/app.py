# backend/app.py
import os
import time
import cv2
import numpy as np
from threading import Thread
from flask import Flask, render_template, Response, jsonify
import face_recognition
from utils.door_control import open_door

# ── Flask setup: serve static files at site-root ─────────────────────────────
app = Flask(
    __name__,
    template_folder='../frontend',   # index.html
    static_folder='../frontend',     # css / js / videos
    static_url_path=''               # serve as “/styles.css”, not “/static/styles.css”
)

# ── simple ping for connectivity tests ──────────────────────────────────────
@app.route('/ping')
def ping():
    return {'status': 'ok'}, 200

# ── load authorised faces at startup ────────────────────────────────────────
KNOWN_ENCODINGS, KNOWN_NAMES = [], []
faces_dir = 'authorized_faces'
if os.path.isdir(faces_dir):
    for person in os.listdir(faces_dir):
        folder = os.path.join(faces_dir, person)
        for img_file in os.listdir(folder):
            img_path = os.path.join(folder, img_file)
            image    = face_recognition.load_image_file(img_path)
            enc      = face_recognition.face_encodings(image)
            if enc:
                KNOWN_ENCODINGS.append(enc[0])
                KNOWN_NAMES.append(person)
print(f'[Startup] Loaded {len(KNOWN_NAMES)} encodings: {set(KNOWN_NAMES)}')

# ── camera setup ────────────────────────────────────────────────────────────
camera = cv2.VideoCapture(0)           # default webcam

def gen_frames():
    while True:
        ok, frame = camera.read()
        if not ok:
            break
        _, buf = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# ── main recognise endpoint (tries up to 5 s) ───────────────────────────────
@app.route('/recognize', methods=['POST'])
def recognize():
    MAX_SEC     = 5          # total time window
    FRAME_DELAY = 0.15       # ~7 fps
    deadline    = time.time() + MAX_SEC
    name        = "Unknown"

    while time.time() < deadline:
        ok, frame = camera.read()
        if not ok:
            return jsonify({'status': 'error'}), 500

        rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        encs = face_recognition.face_encodings(rgb)

        if encs and KNOWN_ENCODINGS:
            distances = face_recognition.face_distance(KNOWN_ENCODINGS, encs[0])
            best = np.argmin(distances)
            if distances[best] < 0.45:
                name = KNOWN_NAMES[best]
                break

        time.sleep(FRAME_DELAY)

    if name != "Unknown":
        Thread(target=open_door).start()
        return jsonify({
            'status': 'granted',
            'name': name,
            'video': f'/videos/welcome_{name}.mp4'
        })
    else:
        return jsonify({'status': 'denied'})

# ── root route serves the SPA front-end ─────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

# ── release the webcam on shutdown ──────────────────────────────────────────
import atexit
@atexit.register
def cleanup():
    camera.release()
    print('[Shutdown] Camera released.')

# ── run ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
