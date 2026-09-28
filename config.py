import os

# ==============================
# Project Base Directory
# ==============================
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# ==============================
# Database
# ==============================
DATABASE_NAME = os.getenv("DATABASE_NAME", "attendance.db")
DATABASE_PATH = os.path.join(BASE_DIR, DATABASE_NAME)

# Use SQLite locally and a managed database (for example Cloud SQL) in Google
# Cloud. SQLAlchemy 2 expects the PostgreSQL driver prefix when DATABASE_URL
# is supplied by a hosting provider.
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

SQLALCHEMY_DATABASE_URI = DATABASE_URL or f"sqlite:///{DATABASE_PATH}"
SQLALCHEMY_TRACK_MODIFICATIONS = False

# ==============================
# Secret Key
# ==============================
SECRET_KEY = os.getenv("SECRET_KEY", "local-development-secret-change-me")

# Fixed port used by the local Flask server.
PORT = 5001

# For local development, default to plain HTTP so browsers can connect without
# a self-signed certificate warning. Set ENABLE_HTTPS=1 only when you want to
# serve with Flask's temporary certificate on localhost.
ENABLE_HTTPS = os.getenv("ENABLE_HTTPS", "0").lower() in {"1", "true", "yes"}

# ==============================
# Dataset Paths
# ==============================
DATASET_FOLDER = os.getenv("DATASET_FOLDER", os.path.join(BASE_DIR, "dataset"))

FACE_DATASET = os.path.join(DATASET_FOLDER, "faces")
VOICE_DATASET = os.path.join(DATASET_FOLDER, "voices")

# ==============================
# Upload Folder
# ==============================
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", os.path.join(BASE_DIR, "uploads"))

# ==============================
# Reports Folder
# ==============================
REPORT_FOLDER = os.getenv("REPORT_FOLDER", os.path.join(BASE_DIR, "reports"))

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
VOICE_MATCH_THRESHOLD = 0.6

# ==============================
# Attendance Settings
# ==============================
ALLOW_ONE_ATTENDANCE_PER_DAY = True

# ==============================
# OTP Settings
# ==============================
OTP_API_KEY = os.getenv("OTP_API_KEY", "otp-api-key-2026")
OTP_TTL_MINUTES = int(os.getenv("OTP_TTL_MINUTES", "10"))
OTP_EMAIL_FROM = os.getenv("OTP_EMAIL_FROM", "noreply@localhost")
SMTP_SERVER = os.getenv("SMTP_SERVER", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "True").lower() == "true"

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