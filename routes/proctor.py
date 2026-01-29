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

    # If already running, just return
    if PROCTOR_STATE["running"]:
        dbg("start_proctoring: Already running")
        return

    # Initialize state
    PROCTOR_STATE["running"] = True
    PROCTOR_STATE["violation"] = False
    
    # Initialize camera synchronously first to fail fast if busy
    # But we will manage the MAIN lifecycle in the thread
    if cap is None:
        cap = cv2.VideoCapture(0)
        dbg("start_proctoring: Camera initialized")
    
    # Initialize first frame
    if cap and cap.isOpened():
        ret, frame = cap.read()
        if ret:
            with lock:
                PROCTOR_STATE["frame"] = frame.copy()

    def run():
        global cap
        dbg("Proctor loop started")

        try:
            while PROCTOR_STATE["running"]:
                if cap is None or not cap.isOpened():
                    dbg("Proctor loop: cap is None or closed, attempting reconnect...")
                    cap = cv2.VideoCapture(0)
                    time.sleep(0.5)
                    if not cap.isOpened():
                        continue
                
                ret, frame = cap.read()
                if not ret:
                    time.sleep(0.05)
                    continue

                # Run inference
                results = model(frame, conf=0.4, verbose=False)

                for box in results[0].boxes:
                    label = model.names[int(box.cls[0])]
                    if label in ["cell phone", "laptop"]:
                        dbg(f"Violation detected: {label}")
                        PROCTOR_STATE["violation"] = True
                        # Don't stop running immediately, just flag it
                        # The client will poll /check-violation and handle the stop
                        break

                with lock:
                    PROCTOR_STATE["frame"] = frame.copy()

                time.sleep(0.1) # Reduced sleep for better responsiveness
                
        except Exception as e:
            dbg(f"Proctor loop error: {e}")
        finally:
            # CLEANUP HAPPENS HERE - SAFE AND SEQUENTIAL
            dbg("Proctor loop ending... cleaning up resources")
            if cap:
                cap.release()
                cap = None
            PROCTOR_STATE["running"] = False
            PROCTOR_STATE["frame"] = None
            dbg("Proctor loop cleanup complete")

    threading.Thread(target=run, daemon=True).start()


def stop_proctoring():
    dbg("stop_proctoring called")
    # Just signal the loop to stop.
    # The loop will handle the release() in its finally block.
    # This prevents the "release while reading" race condition.
    PROCTOR_STATE["running"] = False
    dbg("Signal sent to stop proctoring")

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
