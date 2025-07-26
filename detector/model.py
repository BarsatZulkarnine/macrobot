import cv2
import mediapipe as mp
import numpy as np
from ultralytics import YOLO
import tensorflow as tf
from PIL import Image
import torch

class HumanDetector:
    def __init__(self):
        """Initialize all the pre-built models for human detection"""
        
        # MediaPipe for pose detection and body parts
        self.mp_pose = mp.solutions.pose
        self.mp_hands = mp.solutions.hands
        self.mp_face = mp.solutions.face_detection
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Initialize pose detector
        self.pose = self.mp_pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            enable_segmentation=True,
            min_detection_confidence=0.5
        )
        
        # Initialize hand detector
        self.hands = self.mp_hands.Hands(
            static_image_mode=True,
            max_num_hands=2,
            min_detection_confidence=0.5
        )
        
        # Initialize face detector
        self.face_detection = self.mp_face.FaceDetection(
            model_selection=0,
            min_detection_confidence=0.5
        )
        
        # YOLO for person detection (you can download yolov8n.pt)
        try:
            self.yolo_model = YOLO('yolov8n.pt')  # Will auto-download if not present
        except:
            print("YOLO model not available, will skip YOLO detection")
            self.yolo_model = None
        
        # OpenCV's DNN for person detection (alternative to YOLO)
        self.setup_opencv_dnn()
    
    def setup_opencv_dnn(self):
        """Setup OpenCV DNN with pre-trained models"""
        try:
            # You can download these files from OpenCV's repository
            self.net = cv2.dnn.readNetFromDarknet(
                'yolov3.cfg',  # Configuration file
                'yolov3.weights'  # Pre-trained weights
            )
            self.output_layers = self.net.getUnconnectedOutLayersNames()
        except:
            print("OpenCV DNN model files not found, will skip DNN detection")
            self.net = None

def detect_human(image_path):
    """
    Enhanced human detection using multiple pre-built ML models
    
    Returns:
    dict: Comprehensive detection results including:
        - has_human: Boolean indicating if any human is detected
        - detection_methods: List of methods that detected humans
        - body_parts: Dict of detected body parts
        - pose_info: Information about pose/orientation
        - confidence_scores: Confidence scores from different models
    """
    
    detector = HumanDetector()
    
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        return {"error": "Could not load image", "has_human": False}
    
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    results = {
        "has_human": False,
        "detection_methods": [],
        "body_parts": {
            "face": False,
            "hands": False,
            "full_body": False,
            "pose_landmarks": []
        },
        "pose_info": {
            "upright": False,
            "lying_down": False,
            "sitting": False,
            "orientation": "unknown"
        },
        "confidence_scores": {},
        "bounding_boxes": []
    }
    
    # 1. MediaPipe Pose Detection
    pose_results = detector.pose.process(rgb_image)
    if pose_results.pose_landmarks:
        results["has_human"] = True
        results["detection_methods"].append("MediaPipe Pose")
        results["body_parts"]["full_body"] = True
        results["body_parts"]["pose_landmarks"] = pose_results.pose_landmarks.landmark
        
        # Analyze pose orientation
        landmarks = pose_results.pose_landmarks.landmark
        
        # Check if person is upright (shoulders above hips)
        left_shoulder = landmarks[11]
        right_shoulder = landmarks[12]
        left_hip = landmarks[23]
        right_hip = landmarks[24]
        
        avg_shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
        avg_hip_y = (left_hip.y + right_hip.y) / 2
        
        if avg_shoulder_y < avg_hip_y - 0.1:  # Shoulder significantly above hip
            results["pose_info"]["upright"] = True
            results["pose_info"]["orientation"] = "upright"
        elif abs(avg_shoulder_y - avg_hip_y) < 0.2:  # Similar level
            results["pose_info"]["lying_down"] = True
            results["pose_info"]["orientation"] = "lying_down"
        else:
            results["pose_info"]["sitting"] = True
            results["pose_info"]["orientation"] = "sitting"
    
    # 2. MediaPipe Hand Detection
    hand_results = detector.hands.process(rgb_image)
    if hand_results.multi_hand_landmarks:
        results["has_human"] = True
        results["detection_methods"].append("MediaPipe Hands")
        results["body_parts"]["hands"] = True
        results["confidence_scores"]["hands"] = len(hand_results.multi_hand_landmarks)
    
    # 3. MediaPipe Face Detection
    face_results = detector.face_detection.process(rgb_image)
    if face_results.detections:
        results["has_human"] = True
        results["detection_methods"].append("MediaPipe Face")
        results["body_parts"]["face"] = True
        results["confidence_scores"]["face"] = face_results.detections[0].score[0]
    
    # 4. YOLO Detection (if available)
    if detector.yolo_model:
        try:
            yolo_results = detector.yolo_model(image_path)
            for result in yolo_results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Class 0 is 'person' in COCO dataset
                        if int(box.cls) == 0 and box.conf > 0.5:
                            results["has_human"] = True
                            results["detection_methods"].append("YOLO")
                            results["confidence_scores"]["yolo"] = float(box.conf)
                            results["bounding_boxes"].append({
                                "method": "YOLO",
                                "box": box.xyxy[0].tolist(),
                                "confidence": float(box.conf)
                            })
        except Exception as e:
            print(f"YOLO detection failed: {e}")
    
    # 5. OpenCV DNN Detection (if available)
    if detector.net:
        try:
            height, width = image.shape[:2]
            
            # Create blob from image
            blob = cv2.dnn.blobFromImage(image, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
            detector.net.setInput(blob)
            outputs = detector.net.forward(detector.output_layers)
            
            # Process detections
            for output in outputs:
                for detection in output:
                    scores = detection[5:]
                    class_id = np.argmax(scores)
                    confidence = scores[class_id]
                    
                    # Class 0 is 'person' in COCO dataset
                    if class_id == 0 and confidence > 0.5:
                        results["has_human"] = True
                        results["detection_methods"].append("OpenCV DNN")
                        results["confidence_scores"]["opencv_dnn"] = float(confidence)
                        
                        # Get bounding box
                        center_x = int(detection[0] * width)
                        center_y = int(detection[1] * height)
                        w = int(detection[2] * width)
                        h = int(detection[3] * height)
                        x = int(center_x - w / 2)
                        y = int(center_y - h / 2)
                        
                        results["bounding_boxes"].append({
                            "method": "OpenCV DNN",
                            "box": [x, y, x + w, y + h],
                            "confidence": float(confidence)
                        })
        except Exception as e:
            print(f"OpenCV DNN detection failed: {e}")
    
    # Remove duplicates from detection methods
    results["detection_methods"] = list(set(results["detection_methods"]))
    
    return results

# Usage examples:
if __name__ == "__main__":
    # Example usage
    image_path = "path/to/your/image.jpg"
    detection_result = detect_human(image_path)
    
    print(f"Human detected: {detection_result['has_human']}")
    print(f"Detection methods: {detection_result['detection_methods']}")
    print(f"Body parts found: {detection_result['body_parts']}")
    print(f"Pose information: {detection_result['pose_info']}")
    print(f"Confidence scores: {detection_result['confidence_scores']}")

# Simple function that returns just True/False (backwards compatible)
def detect_human_simple(image_path):
    """Simple version that just returns True/False"""
    result = detect_human(image_path)
    return result.get('has_human', False)