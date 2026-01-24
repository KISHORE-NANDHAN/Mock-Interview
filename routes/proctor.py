import cv2
from ultralytics import YOLO
import threading
import time
from flask import Blueprint, Response

proctor_bp = Blueprint("proctor", __name__)
model = YOLO("yolov8n.pt")

PROCTOR_STATE = {
    "running": False,
    "violation": False,
    "frame": None
}

lock = threading.Lock()
cap = None


def start_proctoring():
    global cap

    if PROCTOR_STATE["running"]:
        return

    cap = cv2.VideoCapture(0)
    PROCTOR_STATE["running"] = True
    PROCTOR_STATE["violation"] = False

    # Initialize first frame
    ret, frame = cap.read()
    if ret:
        with lock:
            PROCTOR_STATE["frame"] = frame.copy()

    def run():
        global cap

        while PROCTOR_STATE["running"]:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.05)
                continue

            results = model(frame, conf=0.4, verbose=False)

            for box in results[0].boxes:
                label = model.names[int(box.cls[0])]
                if label in ["cell phone", "laptop"]:
                    PROCTOR_STATE["violation"] = True
                    PROCTOR_STATE["running"] = False
                    break

            with lock:
                PROCTOR_STATE["frame"] = frame.copy()

            time.sleep(0.2)

    threading.Thread(target=run, daemon=True).start()


def stop_proctoring():
    global cap
    if not PROCTOR_STATE["running"]:
        return
        
    PROCTOR_STATE["running"] = False
    
    # Release camera in a separate thread to prevent blocking the main request
    def release_cam(c):
        if c:
            c.release()
            
    threading.Thread(target=release_cam, args=(cap,)).start()
    cap = None


def gen_frames():
    while PROCTOR_STATE.get("running"):
        with lock:
            frame = PROCTOR_STATE.get("frame")

        if frame is None:
            time.sleep(0.1)
            continue

        success, buffer = cv2.imencode(".jpg", frame)
        if not success:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            buffer.tobytes() +
            b"\r\n"
        )



@proctor_bp.route("/proctor-feed")
def proctor_feed():
    return Response(
        gen_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )
