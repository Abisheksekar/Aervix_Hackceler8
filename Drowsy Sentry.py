import cv2
import time
import mediapipe as mp
import math
import os
import RPi.GPIO as GPIO
import subprocess
import telepot

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(12, GPIO.OUT)

# Path to save yawning detected videos
video_save_path = '/home/pi/drowsy_video'
if not os.path.exists(video_save_path):
    os.makedirs(video_save_path)

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"
bot = telepot.Bot(TELEGRAM_BOT_TOKEN)

# Initialize Mediapipe Face Mesh
mp_drawing = mp.solutions.drawing_utils
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, min_detection_confidence=0.5)

# Eye and Mouth Landmarks
LEFT_EYE_LANDMARKS = [362, 385, 387, 263, 373, 380]
RIGHT_EYE_LANDMARKS = [33, 160, 158, 133, 153, 144]
MOUTH_LANDMARKS = [13, 14, 78, 308]

# Function to calculate Euclidean distance
def euclidean_distance(point1, point2):
    return math.sqrt((point1.x - point2.x) ** 2 + (point1.y - point2.y) ** 2)

# Function to detect yawning using MAR
def mouth_aspect_ratio(mouth_landmarks):
    vertical = euclidean_distance(mouth_landmarks[0], mouth_landmarks[1])
    horizontal = euclidean_distance(mouth_landmarks[2], mouth_landmarks[3])
    return vertical / horizontal

# Function to calculate EAR
def eye_aspect_ratio(eye_landmarks):
    vertical_1 = euclidean_distance(eye_landmarks[1], eye_landmarks[5])
    vertical_2 = euclidean_distance(eye_landmarks[2], eye_landmarks[4])
    horizontal = euclidean_distance(eye_landmarks[0], eye_landmarks[3])
    
    return (vertical_1 + vertical_2) / (2.0 * horizontal) if horizontal != 0 else 0.0

# EAR and MAR Thresholds
EYE_CLOSURE_THRESHOLD = 0.25  # Adjusted for drowsiness detection
EYE_CLOSURE_FRAMES = 60  # 2 seconds at 30 FPS
MAR_THRESHOLD = 0.6  # Yawning detection
MAR_FRAMES = 60  # 2 seconds at 30 FPS

eye_closed_frames = 0
yawn_frames = 0
drowsiness_detected = False

def record_and_send_video():
    video_filename = os.path.join(video_save_path, "drowsy_alert.mp4")
    
    # Record 2-sec video
    command = f"ffmpeg -f v4l2 -t 2 -i /dev/video0 {video_filename}"
    subprocess.run(command, shell=True)
    
    # Send via Telegram
    bot.sendVideo(CHAT_ID, video=open(video_filename, "rb"))

# Start video capture
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

while cap.isOpened():
    ret, img = cap.read()
    if not ret:
        print('Webcam Read Error')
        break
    
    results = face_mesh.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            mp_drawing.draw_landmarks(img, face_landmarks, mp_face_mesh.FACEMESH_CONTOURS)
            
            # Get eye and mouth landmarks
            left_eye = [face_landmarks.landmark[i] for i in LEFT_EYE_LANDMARKS]
            right_eye = [face_landmarks.landmark[i] for i in RIGHT_EYE_LANDMARKS]
            mouth = [face_landmarks.landmark[i] for i in MOUTH_LANDMARKS]
            
            # Calculate EAR and MAR
            left_EAR = eye_aspect_ratio(left_eye)
            right_EAR = eye_aspect_ratio(right_eye)
            avg_EAR = (left_EAR + right_EAR) / 2.0
            mar = mouth_aspect_ratio(mouth)
            
            # Display EAR and MAR values
            cv2.putText(img, f"EAR: {avg_EAR:.2f}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            cv2.putText(img, f"MAR: {mar:.2f}", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            
            # Detect Yawning
            if mar > MAR_THRESHOLD:
                yawn_frames += 1
                if yawn_frames >= MAR_FRAMES:
                    cv2.putText(img, "YAWNING DETECTED!", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                    GPIO.output(12, GPIO.HIGH)
                    record_and_send_video()
                    yawn_frames = 0
            else:
                yawn_frames = 0
            
            # Detect Drowsy Eyes
            if avg_EAR < EYE_CLOSURE_THRESHOLD:
                eye_closed_frames += 1
                if eye_closed_frames >= EYE_CLOSURE_FRAMES:
                    cv2.putText(img, "DROWSY EYES DETECTED!", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                    GPIO.output(12, GPIO.HIGH)
                    record_and_send_video()
                    eye_closed_frames = 0
            else:
                eye_closed_frames = 0
            
    cv2.imshow('Drowsiness Detection', img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
GPIO.cleanup()
