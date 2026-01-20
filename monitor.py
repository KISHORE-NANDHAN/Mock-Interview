import cv2
from ultralytics import YOLO
import time

# ---------------- LOAD YOLO MODEL ----------------
model = YOLO("yolov8n.pt")  # change path if needed

# ---------------- VIOLATION FLAGS ----------------
exam_running = True
violation_detected = False

# ---------------- CAMERA MONITORING ----------------
cap = cv2.VideoCapture(0)  # Open default camera

if not cap.isOpened():
    print("❌ Cannot access camera")
    exit()

print("🔒 Camera monitoring started. Press 'q' to quit.")

while exam_running:
    ret, frame = cap.read()
    if not ret:
        print("❌ Failed to read from camera")
        break

    # YOLO Detection
    results = model(frame)
    detections = results[0].boxes.data.cpu().numpy()
    detected_labels = []

    for det in detections:
        x1, y1, x2, y2, conf, cls = det
        label = model.names[int(cls)]
        detected_labels.append(label)

        # Draw bounding box and label
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        cv2.putText(frame, label, (int(x1), int(y1)-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Show the frame in OpenCV window
    cv2.imshow("Exam Monitoring", frame)

    # 🚨 Violation logic
    if "cell phone" in detected_labels or "laptop" in detected_labels:
        violation_detected = True
        exam_running = False
        print("🚫 Unauthorized object detected! Exam auto-stopped.")

    # Press 'q' to quit manually
    if cv2.waitKey(1) & 0xFF == ord('q'):
        exam_running = False

# ---------------- CLEANUP ----------------
cap.release()
cv2.destroyAllWindows()

# ---------------- LOG VIOLATION ----------------
if violation_detected:
    with open("violation.flag", "w") as f:
        f.write("VIOLATION")
# -----------------------------------------------------
if violation_detected:
    print("Exam auto-submitted due to violation!")
else:
    print("Monitoring ended normally.")

if violation_detected:
    with open("violation.flag", "w") as f:
        f.write("VIOLATION")
