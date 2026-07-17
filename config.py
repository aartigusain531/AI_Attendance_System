import os

# ==============================
# Project Base Directory
# ==============================
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# ==============================
# Database
# ==============================
DATABASE_NAME = "attendance.db"
DATABASE_PATH = os.path.join(BASE_DIR, DATABASE_NAME)

SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_PATH}"
SQLALCHEMY_TRACK_MODIFICATIONS = False

# ==============================
# Secret Key
# ==============================
SECRET_KEY = "AI_Attendance_System_2026"

# ==============================
# Dataset Paths
# ==============================
DATASET_FOLDER = os.path.join(BASE_DIR, "dataset")

FACE_DATASET = os.path.join(DATASET_FOLDER, "faces")
VOICE_DATASET = os.path.join(DATASET_FOLDER, "voices")

# ==============================
# Upload Folder
# ==============================
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

# ==============================
# Reports Folder
# ==============================
REPORT_FOLDER = os.path.join(BASE_DIR, "reports")

# ==============================
# Static Folder
# ==============================
STATIC_FOLDER = os.path.join(BASE_DIR, "static")

# ==============================
# Camera Settings
# ==============================
CAMERA_INDEX = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

# ==============================
# Face Recognition Settings
# ==============================
FACE_TOLERANCE = 0.45
MODEL_TYPE = "hog"      # Use "cnn" if you have a GPU

# ==============================
# Voice Settings
# ==============================
SAMPLE_RATE = 16000
CHANNELS = 1
VOICE_DURATION = 5
VOICE_MATCH_THRESHOLD = 0.7

# ==============================
# Attendance Settings
# ==============================
ALLOW_ONE_ATTENDANCE_PER_DAY = True

# ==============================
# Create Missing Folders
# ==============================
folders = [
    FACE_DATASET,
    VOICE_DATASET,
    UPLOAD_FOLDER,
    REPORT_FOLDER,
]

for folder in folders:
    os.makedirs(folder, exist_ok=True)