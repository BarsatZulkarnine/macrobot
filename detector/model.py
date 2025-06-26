import cv2
import os
from ultralytics import YOLO

# Load YOLOv8 model once
model = YOLO("yolov8n.pt")  # 'n' = nano, use yolov8s.pt for better accuracy

def detect_human(image_path):
    # # Load Haar cascades for face and upper body
    # face_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    # torso_cascade_path = cv2.data.haarcascades + 'haarcascade_upperbody.xml'

    # if not os.path.exists(face_cascade_path) or not os.path.exists(torso_cascade_path):
    #     print("Haar cascade files not found")
    #     return False

    # face_cascade = cv2.CascadeClassifier(face_cascade_path)
    # torso_cascade = cv2.CascadeClassifier(torso_cascade_path)

    # img = cv2.imread(image_path)
    # if img is None:
    #     print("Failed to load image:", image_path)
    #     return False

    # gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
    # torsos = torso_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    # return len(faces) > 0 or len(torsos) > 0

    
    img = cv2.imread(image_path)
    if img is None:
        print("Failed to load image:", image_path)
        return False

    results = model(img)[0]
    for box in results.boxes:
        cls = int(box.cls[0])
        if model.names[cls] == "person":
            return True

    return False
