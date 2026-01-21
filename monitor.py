import cv2
from ultralytics import YOLO
import os
import time

# ---------------- PATH FIX (CRITICAL) ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIOLATION_FLAG = os.path.join(BASE_DIR, "violation.flag")

# ---------------- LOAD YOLO MODEL ----------------
model = YOLO(os.path.join(BASE_DIR, "yolov8n.pt"))

# ---------------- FLAGS ----------------
exam_running = True
violation_detected = False

# ---------------- CAMERA ----------------
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Cannot access camera")
    exit()

print("🔒 Camera monitoring started")

while exam_running:
    ret, frame = cap.read()
    if not ret:
        print("❌ Camera frame read failed")
        break

    results = model(frame, verbose=False)
    detections = results[0].boxes.data.cpu().numpy()
    detected_labels = []

    for det in detections:
        _, _, _, _, conf, cls = det
        label = model.names[int(cls)]
        detected_labels.append(label)

    # 🚨 VIOLATION CHECK
    if "cell phone" in detected_labels or "laptop" in detected_labels:
        violation_detected = True
        exam_running = False
        print("🚫 Violation detected:", detected_labels)

    time.sleep(0.05)  # CPU safety

# ---------------- CLEANUP ----------------
cap.release()

# ---------------- WRITE FLAG (ONCE) ----------------
if violation_detected:
    with open(VIOLATION_FLAG, "w") as f:
        f.write("VIOLATION")
    print("🚨 violation.flag created at:", VIOLATION_FLAG)
else:
    print("✅ Monitoring ended normally")
