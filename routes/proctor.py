import cv2
from ultralytics import YOLO
import threading
import time
from flask import Blueprint, Response
import datetime

proctor_bp = Blueprint("proctor", __name__)
model = YOLO("yolov8n.pt")

PROCTOR_STATE = {
    "running": False,
    "violation": False,
    "frame": None
}

lock = threading.Lock()
cap = None

def dbg(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("debug/proctor_debug.log", "a") as f:
        f.write(f"[{timestamp}] [PROCTOR] {msg}\n")

def start_proctoring():
    global cap
    dbg("start_proctoring called")

    if PROCTOR_STATE["running"]:
        dbg("start_proctoring: Already running")
        return

    cap = cv2.VideoCapture(0)
    PROCTOR_STATE["running"] = True
    PROCTOR_STATE["violation"] = False
    dbg("start_proctoring: Camera initialized, state set to running")

    # Initialize first frame
    ret, frame = cap.read()
    if ret:
        with lock:
            PROCTOR_STATE["frame"] = frame.copy()

    def run():
        global cap
        dbg("Proctor loop started")

        while PROCTOR_STATE["running"]:
            if cap is None:
                dbg("Proctor loop: cap is None, breaking")
                break
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.05)
                continue

            results = model(frame, conf=0.4, verbose=False)

            for box in results[0].boxes:
                label = model.names[int(box.cls[0])]
                if label in ["cell phone", "laptop"]:
                    dbg(f"Violation detected: {label}")
                    PROCTOR_STATE["violation"] = True
                    PROCTOR_STATE["running"] = False
                    break

            with lock:
                PROCTOR_STATE["frame"] = frame.copy()

            time.sleep(0.2)
        dbg("Proctor loop ended")

    threading.Thread(target=run, daemon=True).start()


def stop_proctoring():
    global cap
    dbg("stop_proctoring called")
    if not PROCTOR_STATE["running"]:
        dbg("stop_proctoring: Not running, ignoring")
        return
        
    PROCTOR_STATE["running"] = False
    dbg("stop_proctoring: State set to False")
    
    # Release camera in a separate thread to prevent blocking the main request
    def release_cam(c):
        dbg("release_cam: Starting release")
        if c:
            c.release()
            dbg("release_cam: Camera released")
        else:
            dbg("release_cam: No camera to release")
            
    threading.Thread(target=release_cam, args=(cap,)).start()
    cap = None


def gen_frames():
    dbg("gen_frames generator started")
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
    dbg("gen_frames generator ended")



@proctor_bp.route("/proctor-feed")
def proctor_feed():
    dbg("proctor_feed route accessed")
    return Response(
        gen_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )
