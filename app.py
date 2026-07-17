
import base64
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, session
from datetime import datetime
import io
import os
import shutil
import subprocess
import tempfile
import cv2
import numpy as np
import face_recognition
from scipy.io import wavfile
import json

# Import Config
import config

# Load trained face encodings for recognition
from models.face import known_face_encodings, known_face_names, load_face_encodings
from models.train_face import train_faces

# Import Database
from models.database import (
    db,
    Student,
    Attendance,
    Admin,
    init_database
)

from models.attendance import AttendanceManager

# ==========================================
# Create Flask App
# ==========================================
app = Flask(__name__)

# ==========================================
# Configuration
# ==========================================
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = config.SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = config.SQLALCHEMY_TRACK_MODIFICATIONS

# Initialize Database
init_database(app)

def reload_known_faces():
    global known_face_encodings, known_face_names
    known_face_encodings, known_face_names = load_face_encodings()


def ffmpeg_decode_audio(raw_bytes, target_sr=16000):
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                "pipe:0",
                "-ac",
                "1",
                "-ar",
                str(target_sr),
                "-f",
                "wav",
                "pipe:1"
            ],
            input=raw_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        with io.BytesIO(result.stdout) as stream:
            return wavfile.read(stream)
    except Exception:
        return None, None


def load_audio_bytes(raw_bytes, target_sr=16000):
    try:
        with io.BytesIO(raw_bytes) as stream:
            return wavfile.read(stream)
    except Exception:
        return ffmpeg_decode_audio(raw_bytes, target_sr=target_sr)


def normalize_audio(audio):
    if audio.dtype == np.int16:
        audio = audio.astype(np.float32) / 32768.0
    elif audio.dtype == np.int32:
        audio = audio.astype(np.float32) / 2147483648.0
    elif audio.dtype == np.uint8:
        audio = (audio.astype(np.float32) - 128) / 128.0
    else:
        audio = audio.astype(np.float32)

    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)

    if np.max(np.abs(audio)) > 0:
        audio = audio / np.max(np.abs(audio))

    return audio


def resample_audio(audio, orig_sr, target_sr):
    if orig_sr == target_sr:
        return audio
    duration = len(audio) / orig_sr
    target_length = int(round(duration * target_sr))
    if target_length <= 0:
        return np.array([], dtype=np.float32)
    return np.interp(
        np.linspace(0, len(audio) - 1, target_length),
        np.arange(len(audio)),
        audio
    )


def voice_features(audio, sample_rate, length_seconds=3):
    audio = normalize_audio(audio)
    if len(audio) == 0:
        return None

    target_samples = int(sample_rate * length_seconds)
    if len(audio) < target_samples:
        audio = np.pad(audio, (0, target_samples - len(audio)))
    else:
        audio = audio[:target_samples]

    window = np.hanning(len(audio))
    spectrum = np.abs(np.fft.rfft(audio * window))
    norm = np.linalg.norm(spectrum)
    return spectrum / (norm + 1e-9)


def match_voice(voice_bytes):
    # Use cosine similarity on normalized spectral features.
    # Higher similarity (closer to 1.0) is better.
    target_sr = config.SAMPLE_RATE
    sample_rate, audio = load_audio_bytes(voice_bytes)
    if sample_rate is None or audio is None:
        return None, None

    # Resample & extract features to target sample rate
    audio = resample_audio(normalize_audio(audio), sample_rate, target_sr)
    query_spec = voice_features(audio, target_sr)
    if query_spec is None:
        return None, None

    def extract_roll_from_voice_filename(filename):
        base = os.path.splitext(filename)[0]
        if "_" in base:
            prefix, suffix = base.rsplit("_", 1)
            if suffix.isdigit():
                return prefix
        return base

    best_roll = None
    best_sim = -1.0

    for filename in os.listdir(config.VOICE_DATASET):
        voice_path = os.path.join(config.VOICE_DATASET, filename)
        if not os.path.isfile(voice_path):
            continue

        try:
            with open(voice_path, "rb") as f:
                stored_bytes = f.read()
            stored_sr, stored_audio = load_audio_bytes(stored_bytes)
        except Exception:
            continue

        if stored_sr is None or stored_audio is None:
            continue

        stored_audio = resample_audio(normalize_audio(stored_audio), stored_sr, target_sr)
        stored_spec = voice_features(stored_audio, target_sr)
        if stored_spec is None:
            continue

        # Since features are normalized, dot product is cosine similarity
        sim = float(np.dot(query_spec, stored_spec))
        if sim > best_sim:
            best_sim = sim
            best_roll = extract_roll_from_voice_filename(filename)

    threshold = getattr(config, "VOICE_MATCH_THRESHOLD", 0.7)
    if best_roll is None or best_sim < threshold:
        return None, None

    return best_roll, best_sim

# ==========================================
# Home Page
# ==========================================
@app.route("/")
def home():
    return render_template("index.html")

# ==========================================
# Admin Login (disabled)
@app.route("/login", methods=["GET", "POST"])
def login():
    # Admin sign-in has been disabled. Redirect to home with a notice.
    flash("Admin sign-in has been disabled.", "warning")
    return redirect(url_for("home"))

# Logout route removed as login system has been removed.

# ==========================================
# Dashboard
# ==========================================
@app.route("/dashboard")
def dashboard():
    # Dashboard accessible without login (login system removed)
    total_students = Student.query.count()

    total_attendance = Attendance.query.count()

    today = datetime.today().date()

    today_attendance = Attendance.query.filter_by(date=today).count()

    students = Student.query.all()

    attendance = Attendance.query.order_by(
        Attendance.created_at.desc()
    ).all()

    return render_template(
        "dashboard.html",
        total_students=total_students,
        total_attendance=total_attendance,
        today_attendance=today_attendance,
        students=students,
        attendance=attendance
    )

# ==========================================
# Register Student (Admin Only)
# ==========================================
@app.route("/register", methods=["GET", "POST"])
def register():
    # NOTE: Admin authentication removed for registration to allow student
    # registration without signing in. If you want to restrict this, re-add
    # the admin session check and enable the login flow.

    if request.method == "POST":

        name = request.form.get("name")
        roll = request.form.get("roll")
        department = request.form.get("department")
        year = request.form.get("year")
        phone = request.form.get("phone")
        email = request.form.get("email")

        image_data = request.form.get("image")
        voice_data = request.form.get("voice")

        print("=" * 50)
        print("Image received:", image_data is not None)
        print("Voice received:", voice_data is not None)

        if image_data:
            print(image_data[:50])

        if voice_data:
            print(voice_data[:50])

        print("=" * 50)

        existing = Student.query.filter_by(
            roll_number=roll
        ).first()

        if existing:
            flash("Student already exists!", "danger")
            return redirect(url_for("register"))

        # Create folders
        face_folder = os.path.join(config.FACE_DATASET, roll)
        os.makedirs(face_folder, exist_ok=True)

        voice_folder = config.VOICE_DATASET
        os.makedirs(voice_folder, exist_ok=True)

        face_file = os.path.join(face_folder, "face.jpg")
        voice_file = None

        # Save face
        if image_data:
            try:
                header, encoded = image_data.split(",", 1)
                with open(face_file, "wb") as f:
                    f.write(base64.b64decode(encoded))
                print("Face Saved")
            except Exception as e:
                print("Face Save Error:", e)

        # Save voice(s)
        saved_voice_file = None
        voices_json = request.form.get("voices")
        if voices_json:
            try:
                samples = json.loads(voices_json)
                idx = 1
                for s in samples:
                    try:
                        header, encoded = s.split(",", 1)
                        mime = header.split(";", 1)[0].split(":", 1)[1]
                        extension = {
                            "audio/wav": "wav",
                            "audio/webm": "webm",
                            "audio/ogg": "ogg"
                        }.get(mime, "webm")
                        voice_file_path = os.path.join(voice_folder, f"{roll}_{idx}.{extension}")
                        with open(voice_file_path, "wb") as f:
                            f.write(base64.b64decode(encoded))
                        if idx == 1:
                            saved_voice_file = os.path.basename(voice_file_path)
                        idx += 1
                    except Exception:
                        continue
                print("Voice samples saved")
            except Exception as e:
                print("Voice Save Error:", e)
        elif voice_data:
            try:
                header, encoded = voice_data.split(",", 1)
                mime = header.split(";", 1)[0].split(":", 1)[1]
                extension = {
                    "audio/wav": "wav",
                    "audio/webm": "webm",
                    "audio/ogg": "ogg"
                }.get(mime, "webm")
                voice_file = os.path.join(voice_folder, f"{roll}.{extension}")
                with open(voice_file, "wb") as f:
                    f.write(base64.b64decode(encoded))
                saved_voice_file = os.path.basename(voice_file)
                print("Voice Saved")
            except Exception as e:
                print("Voice Save Error:", e)

        student = Student(
            name=name,
            roll_number=roll,
            department=department,
            year=year,
            phone=phone,
            email=email,
            face_folder=face_folder,
            voice_file=saved_voice_file
        )

        db.session.add(student)
        db.session.commit()

        try:
            train_faces()
            reload_known_faces()
        except Exception as e:
            print("Face retraining failed after registration:", e)
            flash("Student registered, but face model retraining failed. You may need to retrain manually.", "warning")
        else:
            flash("Student Registered Successfully! Face model updated.", "success")

        return redirect(url_for("dashboard"))

    return render_template("register.html")

# ==========================================
# Reset faces, voices and student data
@app.route("/reset", methods=["POST"])
def reset_data():
    try:
        # Delete face folders but keep the parent directory
        for student_dir in os.listdir(config.FACE_DATASET):
            student_path = os.path.join(config.FACE_DATASET, student_dir)
            if os.path.isdir(student_path):
                shutil.rmtree(student_path)
            elif os.path.isfile(student_path):
                os.remove(student_path)

        # Delete voice files
        for voice_file in os.listdir(config.VOICE_DATASET):
            voice_path = os.path.join(config.VOICE_DATASET, voice_file)
            if os.path.isfile(voice_path):
                os.remove(voice_path)

        # Remove student and attendance records
        Attendance.query.delete()
        Student.query.delete()
        db.session.commit()

        # Remove face recognition model file if present
        model_path = os.path.join("models", "face_encodings.pkl")
        if os.path.exists(model_path):
            os.remove(model_path)

        flash("All saved faces, voices and student records have been cleared.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Unable to reset data: {e}", "danger")

    return redirect(url_for("home"))

# ==========================================
# Static media routes
@app.route("/faces/<roll>/<filename>")
def serve_face_image(roll, filename):
    return send_from_directory(
        os.path.join(config.FACE_DATASET, roll),
        filename
    )


@app.route("/voices/<filename>")
def serve_voice_file(filename):
    return send_from_directory(
        config.VOICE_DATASET,
        filename
    )

# ==========================================
# Face recognition API for auto-fill
@app.route("/api/recognize_face", methods=["POST"])
def recognize_face():
    data = request.get_json() or {}
    image_data = data.get("image")

    if not image_data:
        return jsonify({"recognized": False, "message": "No image data provided."}), 400

    try:
        header, encoded = image_data.split(",", 1)
        image_bytes = base64.b64decode(encoded)
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img is None:
            raise ValueError("Invalid image data")

        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_img)
        face_encodings = face_recognition.face_encodings(rgb_img, face_locations)

        if not face_encodings:
            return jsonify({"recognized": False, "message": "No face detected."})

        face_encoding = face_encodings[0]
        distances = face_recognition.face_distance(known_face_encodings, face_encoding)

        if len(distances) == 0:
            return jsonify({"recognized": False, "message": "No known faces available."})

        best_idx = int(np.argmin(distances))
        best_distance = float(distances[best_idx])

        if best_distance > config.FACE_TOLERANCE:
            return jsonify({"recognized": False, "message": "Face not recognized."})

        roll_number = known_face_names[best_idx]
        student = Student.query.filter_by(roll_number=roll_number).first()

        if student:
            return jsonify({
                "recognized": True,
                "student": {
                    "name": student.name,
                    "roll_number": student.roll_number,
                    "department": student.department,
                    "year": student.year,
                    "phone": student.phone,
                    "email": student.email
                }
            })

        return jsonify({"recognized": True, "roll_number": roll_number, "message": "Face recognized but no student record exists."})
    except Exception as e:
        return jsonify({"recognized": False, "message": str(e)}), 500

# ==========================================
# Attendance Page
# ==========================================
@app.route("/attendance")
def attendance_page():
    return render_template("attendance.html")


@app.route("/attendance_calendar")
def attendance_calendar_page():
    return render_template("attendance_calendar.html")

# ==========================================
# Attendance API
# ==========================================
@app.route("/api/attendance")
def attendance_api():

    attendance = Attendance.query.order_by(
        Attendance.created_at.desc()
    ).all()

    data = []

    for item in attendance:

        student = Student.query.get(item.student_id)

        data.append({
            "name": student.name,
            "roll": student.roll_number,
            "department": student.department,
            "date": str(item.date),
            "time": str(item.time),
            "status": item.status
        })

    return jsonify(data)


@app.route("/api/attendance_for_date")
def attendance_for_date():
    # Expects ?date=YYYY-MM-DD, defaults to today
    date_str = request.args.get("date")
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
    else:
        target_date = datetime.utcnow().date()

    students = Student.query.order_by(Student.roll_number).all()
    results = []
    for s in students:
        att = Attendance.query.filter_by(student_id=s.id, date=target_date).first()
        if att:
            results.append({
                "id": s.id,
                "name": s.name,
                "roll": s.roll_number,
                "department": s.department,
                "present": True,
                "time": str(att.time),
                "status": att.status
            })
        else:
            results.append({
                "id": s.id,
                "name": s.name,
                "roll": s.roll_number,
                "department": s.department,
                "present": False,
                "time": None,
                "status": "Absent"
            })

    return jsonify({"date": str(target_date), "data": results})


@app.route("/api/recognize_voice", methods=["POST"])
def recognize_voice():
    data = request.get_json() or {}
    voice_data = data.get("voice")

    if not voice_data:
        return jsonify({"recognized": False, "message": "Voice data is required."}), 400

    try:
        header, encoded = voice_data.split(",", 1)
        voice_bytes = base64.b64decode(encoded)
    except Exception:
        return jsonify({"recognized": False, "message": "Invalid voice data."}), 400

    roll_number, score = match_voice(voice_bytes)
    if not roll_number:
        return jsonify({"recognized": False, "message": "Voice not recognized."})

    student = Student.query.filter_by(roll_number=roll_number).first()
    if not student:
        return jsonify({"recognized": False, "message": "Matched voice but student record missing."})

    success, message = AttendanceManager.mark_attendance(student.roll_number, identifier="roll")
    return jsonify({
        "recognized": True,
        "student": {
            "name": student.name,
            "roll_number": student.roll_number,
            "department": student.department,
            "year": student.year,
            "phone": student.phone,
            "email": student.email
        },
        "attendance_marked": success,
        "message": message,
        "score": score
    })


@app.route("/api/voice_best_match", methods=["POST"])
def voice_best_match():
    data = request.get_json() or {}
    voice_data = data.get("voice")
    if not voice_data:
        return jsonify({"error": "voice required"}), 400
    try:
        header, encoded = voice_data.split(",", 1)
        voice_bytes = base64.b64decode(encoded)
    except Exception:
        return jsonify({"error": "invalid voice data"}), 400

    # compute best match even if below threshold
    target_sr = config.SAMPLE_RATE
    sample_rate, audio = load_audio_bytes(voice_bytes)
    if sample_rate is None or audio is None:
        return jsonify({"error": "unable to decode audio"}), 400

    audio = resample_audio(normalize_audio(audio), sample_rate, target_sr)
    query_spec = voice_features(audio, target_sr)
    if query_spec is None:
        return jsonify({"error": "no features"}), 400

    best_match = None
    best_sim = -1.0
    for filename in os.listdir(config.VOICE_DATASET):
        path = os.path.join(config.VOICE_DATASET, filename)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "rb") as f:
                stored_bytes = f.read()
            sr, stored_audio = load_audio_bytes(stored_bytes)
            if sr is None or stored_audio is None:
                continue
            stored_audio = resample_audio(normalize_audio(stored_audio), sr, target_sr)
            stored_spec = voice_features(stored_audio, target_sr)
            if stored_spec is None:
                continue
            sim = float(np.dot(query_spec, stored_spec))
            if sim > best_sim:
                best_sim = sim
                best_match = filename
        except Exception:
            continue

    if not best_match:
        return jsonify({"matched": False}), 200

    def extract_roll_from_voice_filename(filename):
        base = os.path.splitext(filename)[0]
        if "_" in base:
            prefix, suffix = base.rsplit("_", 1)
            if suffix.isdigit():
                return prefix
        return base

    roll = extract_roll_from_voice_filename(best_match)
    student = Student.query.filter_by(roll_number=roll).first()
    if not student:
        return jsonify({"matched": False}), 200

    return jsonify({
        "matched": True,
        "student": {
            "name": student.name,
            "roll_number": student.roll_number,
            "department": student.department
        },
        "score": best_sim
    })


@app.route("/api/mark_attendance_override", methods=["POST"])
def mark_attendance_override():
    data = request.get_json() or {}
    roll = data.get("roll_number")
    if not roll:
        return jsonify({"success": False, "message": "roll_number required"}), 400
    student = Student.query.filter_by(roll_number=roll).first()
    if not student:
        return jsonify({"success": False, "message": "student not found"}), 404

    success, message = AttendanceManager.mark_attendance(student.roll_number, identifier="roll")
    status_code = 200 if success else 400
    return jsonify({"success": success, "message": message}), status_code


@app.route("/api/mark_attendance", methods=["POST"])
def mark_attendance_api():
    data = request.get_json() or {}
    roll_number = data.get("roll_number")
    student_name = data.get("name")
    voice_data = data.get("voice")

    if not roll_number and not student_name:
        return jsonify({"success": False, "message": "roll_number or name is required."}), 400

    if not voice_data:
        return jsonify({"success": False, "message": "Voice sample is required for verification."}), 400

    try:
        header, encoded = voice_data.split(",", 1)
        voice_bytes = base64.b64decode(encoded)
    except Exception:
        return jsonify({"success": False, "message": "Invalid voice data."}), 400

    if len(voice_bytes) < 1000:
        return jsonify({"success": False, "message": "Voice sample too short."}), 400

    # If roll_number provided we expected face recognition already matched the student.
    # Verify the provided voice sample belongs to the same roll before marking attendance.
    score = None
    if roll_number:
        matched_roll, score = match_voice(voice_bytes)
        if not matched_roll:
            return jsonify({"success": False, "message": "Voice did not match any registered student."}), 400

        if matched_roll != str(roll_number):
            return jsonify({
                "success": False,
                "message": "Voice does not match the detected face. Attendance rejected."
            }), 400

        success, message = AttendanceManager.mark_attendance(roll_number, identifier="roll")
    else:
        # When only name is provided, perform voice match and then mark attendance by name
        matched_roll, score = match_voice(voice_bytes)
        if not matched_roll:
            return jsonify({"success": False, "message": "Voice did not match any registered student."}), 400

        student = Student.query.filter_by(roll_number=matched_roll).first()
        if not student:
            return jsonify({"success": False, "message": "Matched voice but student record missing."}), 400

        success, message = AttendanceManager.mark_attendance(student.roll_number, identifier="roll")

    status_code = 200 if success else 400
    resp = {"success": success, "message": message}
    if score is not None:
        resp["score"] = score
    return jsonify(resp), status_code

# ==========================================
# Student API
# ==========================================
@app.route("/api/students")
def students_api():

    students = Student.query.all()

    data = []

    for student in students:

        data.append({
            "id": student.id,
            "name": student.name,
            "roll": student.roll_number,
            "department": student.department,
            "year": student.year
        })

    return jsonify(data)

# ==========================================
# Delete Student
# ==========================================
@app.route("/api/delete_student", methods=["POST"])
def delete_student_api():
    data = request.get_json() or {}
    roll_number = data.get("roll_number")

    if not roll_number:
        return jsonify({"success": False, "message": "roll_number is required."}), 400

    try:
        student = Student.query.filter_by(roll_number=roll_number).first()
        if not student:
            return jsonify({"success": False, "message": "Student not found."}), 404

        # Delete all attendance records for this student
        Attendance.query.filter_by(student_id=student.id).delete()

        # Delete face folder
        face_folder = os.path.join(config.FACE_DATASET, roll_number)
        if os.path.isdir(face_folder):
            shutil.rmtree(face_folder)

        # Delete all voice files for this student
        for filename in os.listdir(config.VOICE_DATASET):
            base = os.path.splitext(filename)[0]
            if "_" in base:
                prefix = base.rsplit("_", 1)[0]
                if prefix == roll_number:
                    voice_path = os.path.join(config.VOICE_DATASET, filename)
                    if os.path.isfile(voice_path):
                        os.remove(voice_path)

        # Delete student record
        db.session.delete(student)
        db.session.commit()

        # Retrain face model
        try:
            train_faces()
            reload_known_faces()
        except Exception as e:
            print(f"Face retraining after deletion failed: {e}")

        return jsonify({"success": True, "message": f"Student {roll_number} deleted successfully."}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

# ==========================================
# About API
# ==========================================
@app.route("/api/info")
def info():

    return jsonify({

        "Project": "AI Attendance System",

        "Version": "1.0",

        "Developer": "Piyush",

        "Technology": "Flask + OpenCV + Face Recognition + Voice Recognition"

    })

# ==========================================
# Run Server
# ==========================================
if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )