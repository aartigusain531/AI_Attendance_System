import base64
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, session
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
import io
import random
import smtplib
from email.message import EmailMessage
import os
import shutil
import subprocess
import tempfile
import cv2
import numpy as np
import face_recognition
from scipy.io import wavfile
import json
from sqlalchemy import text

try:
    import imageio_ffmpeg
except ImportError:
    imageio_ffmpeg = None

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
    Teacher,
    init_database
)

from models.attendance import AttendanceManager
from assistant.attendance_assistant import answer_attendance_question
from assistant.system_assistant import answer_system_question

# ==========================================
# Create Flask App
# ==========================================
app = Flask(__name__)

# Registration submits several base64 voice samples in one form.
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024


@app.after_request
def add_media_security_headers(response):
    response.headers["Permissions-Policy"] = "camera=(self), microphone=(self)"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"success": False, "message": "Request entity too large. Reduce upload size or increase MAX_CONTENT_LENGTH."}), 413


@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"})


@app.route("/readyz")
def readyz():
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({"status": "ready"})
    except Exception:
        return jsonify({"status": "not ready"}), 503

# ==========================================
# Configuration
# ==========================================
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = config.SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = config.SQLALCHEMY_TRACK_MODIFICATIONS

# Initialize Database
init_database(app)

otp_store = {}


def reload_known_faces():
    global known_face_encodings, known_face_names
    known_face_encodings, known_face_names = load_face_encodings()


def ffmpeg_decode_audio(raw_bytes, target_sr=16000):
    try:
        ffmpeg_executable = (
            imageio_ffmpeg.get_ffmpeg_exe()
            if imageio_ffmpeg
            else "ffmpeg"
        )
        result = subprocess.run(
            [
                ffmpeg_executable,
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
    except Exception as error:
        print(f"Audio decode failed. Install ffmpeg or imageio-ffmpeg: {error}")
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


def hz_to_mel(freq):
    return 2595.0 * np.log10(1.0 + freq / 700.0)


def mel_to_hz(mel):
    return 700.0 * (10.0**(mel / 2595.0) - 1.0)


def mel_filterbank(n_fft_bins, n_mels, sample_rate, fmin=0.0, fmax=None):
    if fmax is None:
        fmax = sample_rate / 2.0

    mel_points = np.linspace(hz_to_mel(fmin), hz_to_mel(fmax), n_mels + 2)
    hz_points = mel_to_hz(mel_points)
    bin_points = np.floor((n_fft_bins - 1) * hz_points / sample_rate).astype(int)

    filter_bank = np.zeros((n_mels, n_fft_bins), dtype=np.float32)
    for m in range(1, n_mels + 1):
        left = bin_points[m - 1]
        center = bin_points[m]
        right = bin_points[m + 1]

        if left == center or center == right:
            continue

        for k in range(left, center):
            filter_bank[m - 1, k] = (k - left) / (center - left)
        for k in range(center, right):
            filter_bank[m - 1, k] = (right - k) / (right - center)

    return filter_bank


def voice_features(audio, sample_rate, length_seconds=3, n_mels=40):
    audio = normalize_audio(audio)
    if len(audio) == 0:
        return None

    target_samples = int(sample_rate * length_seconds)
    if len(audio) < target_samples:
        audio = np.pad(audio, (0, target_samples - len(audio)))
    else:
        audio = audio[:target_samples]

    n_fft = 512
    hop_length = int(sample_rate * 0.010)
    win_length = int(sample_rate * 0.025)
    if win_length <= 0:
        win_length = 256
    window = np.hanning(win_length)

    pad_amount = n_fft - (len(audio) - win_length) % hop_length
    if pad_amount != n_fft:
        audio = np.pad(audio, (0, pad_amount))

    num_frames = 1 + (len(audio) - win_length) // hop_length
    frames = np.lib.stride_tricks.as_strided(
        audio,
        shape=(num_frames, win_length),
        strides=(audio.strides[0] * hop_length, audio.strides[0]),
        writeable=False
    )

    frames = frames * window
    spectrum = np.abs(np.fft.rfft(frames, n=n_fft, axis=1))**2
    mel_fb = mel_filterbank(spectrum.shape[1], n_mels, sample_rate)
    mel_spec = np.dot(spectrum, mel_fb.T)
    log_mel = np.log(mel_spec + 1e-10)

    features = np.mean(log_mel, axis=0)
    features = (features - np.mean(features)) / (np.std(features) + 1e-9)
    return features


def generate_otp(length=6):
    return str(random.randint(10 ** (length - 1), (10 ** length) - 1)).zfill(length)


def send_otp_email(email_address, otp):
    if not config.SMTP_SERVER:
        print(f"OTP for {email_address}: {otp}")
        return True

    try:
        msg = EmailMessage()
        msg["Subject"] = "Your OTP Code"
        msg["From"] = config.OTP_EMAIL_FROM
        msg["To"] = email_address
        msg.set_content(
            f"Your OTP code is {otp}. It will expire in {config.OTP_TTL_MINUTES} minutes."
        )

        with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
            if config.SMTP_USE_TLS:
                server.starttls()
            if config.SMTP_USERNAME and config.SMTP_PASSWORD:
                server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as exc:
        print("OTP email failed:", exc)
        return False


def save_otp(email_address, otp):
    otp_store[email_address.lower()] = {
        "code": otp,
        "expires_at": datetime.utcnow() + timedelta(minutes=config.OTP_TTL_MINUTES)
    }


def verify_otp(email_address, otp):
    key = email_address.lower()
    entry = otp_store.get(key)
    if not entry:
        return False
    if datetime.utcnow() > entry["expires_at"]:
        otp_store.pop(key, None)
        return False
    if str(otp) != str(entry["code"]):
        return False
    otp_store.pop(key, None)
    return True


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
    checked_files = 0

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
        checked_files += 1
        if sim > best_sim:
            best_sim = sim
            best_roll = extract_roll_from_voice_filename(filename)

    threshold = getattr(config, "VOICE_MATCH_THRESHOLD", 0.7)
    # Debug: show matching summary when no acceptable match found
    if best_roll is None or best_sim < threshold:
        try:
            print(f"[DEBUG] match_voice: checked_files={checked_files} best_roll={best_roll} best_sim={best_sim:.4f} threshold={threshold}")
        except Exception:
            pass
        return None, None

    return best_roll, best_sim

# ==========================================
# Home Page
# ==========================================
TEACHER_GRADES = [
    "LKG", "UKG", "1st", "2nd", "3rd", "4th", "5th", "6th",
    "7th", "8th", "9th", "10th", "11th", "12th"
]


@app.route("/")
def home():
    return render_template("index.html")


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if (
            not session.get("admin_logged_in")
            or session.get("admin_username") != "admin"
        ):
            session.pop("admin_logged_in", None)
            session.pop("admin_username", None)
            flash("Please log in as admin to access this page.", "warning")
            return redirect(url_for("login", next=request.path))
        if not session.get("teacher_grade") and request.endpoint != "teacher_grade":
            return redirect(url_for("teacher_grade", next=request.path))
        return f(*args, **kwargs)

    return decorated_function


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        is_admin = (
            session.get("admin_logged_in")
            and session.get("admin_username") == "admin"
        )
        if not is_admin and not session.get("teacher_logged_in"):
            session.pop("admin_logged_in", None)
            session.pop("admin_username", None)
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)

    return decorated_function


def grade_access_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        is_guest_attendance = (
            session.get("guest_attendance") is True
            and session.get("teacher_grade") in TEACHER_GRADES
        )
        public_grade = request.args.get("grade") or request.form.get("grade")
        if (
            not session.get("teacher_logged_in")
            and not (
                session.get("admin_logged_in")
                and session.get("admin_username") == "admin"
            )
            and request.args.get("public") == "1"
            and public_grade in TEACHER_GRADES
        ):
            session["teacher_grade"] = public_grade
            session["guest_attendance"] = True
            return f(*args, **kwargs)

        if (
            not session.get("teacher_logged_in")
            and not (
                session.get("admin_logged_in")
                and session.get("admin_username") == "admin"
            )
            and not is_guest_attendance
        ):
            session.pop("admin_logged_in", None)
            session.pop("admin_username", None)
            session.pop("guest_attendance", None)
            if request.endpoint == "attendance_page":
                return redirect(url_for("home"))
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login", next=request.path))

        if session.get("teacher_logged_in"):
            teacher = db.session.get(Teacher, session.get("teacher_id"))
            if not teacher:
                session.clear()
                flash("Your teacher account is unavailable. Please log in again.", "danger")
                return redirect(url_for("teacher_login"))
            if session.get("teacher_grade") not in (teacher.assigned_grades or []):
                session.pop("teacher_grade", None)
                return redirect(url_for("teacher_grade", next=request.path))

        if not session.get("teacher_grade"):
            return redirect(url_for("teacher_grade", next=request.path))
        return f(*args, **kwargs)

    return decorated_function


# ==========================================
# Admin Login
# ==========================================
@app.route("/login", methods=["GET", "POST"])
def login():
    return handle_login("Admin")


@app.route("/teacher-login", methods=["GET", "POST"])
def teacher_login():
    return handle_login("Teacher")


def handle_login(login_role):
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if login_role == "Admin":
            account = Admin.query.filter_by(username="admin").first() if username == "admin" else None
            if account:
                stored_password = account.password or ""
                password_matches = (
                    stored_password == password or check_password_hash(stored_password, password)
                )
            else:
                password_matches = False

            if password_matches:
                session.clear()
                session["admin_logged_in"] = True
                session["admin_username"] = account.username
        else:
            account = (
                Teacher.query.filter_by(username=username).first()
                if username.casefold() != "admin"
                else None
            )
            password_matches = bool(
                account and check_password_hash(account.password or "", password)
            )

            if password_matches and account:
                if not account.assigned_grades:
                    flash("No grades are assigned to your account. Please contact the administrator.", "warning")
                    return render_template("login.html", login_role=login_role)

                session.clear()
                session["teacher_logged_in"] = True
                session["teacher_id"] = account.id
                session["teacher_username"] = account.username

        if password_matches:
            session.pop("teacher_grade", None)
            flash("Login successful.", "success")
            return redirect(url_for("teacher_grade", next=request.args.get("next")))

        flash("Invalid username or password.", "danger")

    return render_template("login.html", login_role=login_role)


@app.route("/teacher-grade", methods=["GET", "POST"])
@login_required
def teacher_grade():
    next_url = request.args.get("next") or request.form.get("next")
    is_admin = bool(
        session.get("admin_logged_in")
        and session.get("admin_username") == "admin"
    )
    if is_admin:
        available_grades = TEACHER_GRADES
    else:
        teacher = db.session.get(Teacher, session.get("teacher_id"))
        if not teacher:
            session.clear()
            flash("Your teacher account is unavailable. Please log in again.", "danger")
            return redirect(url_for("teacher_login"))
        available_grades = teacher.assigned_grades or []

    if request.method == "POST":
        selected_grade = request.form.get("grade", "").strip()
        if selected_grade not in available_grades:
            flash("Please select a valid grade.", "danger")
            return render_template(
                "teacher_grade.html",
                grades=available_grades,
                next_url=next_url,
                is_admin=is_admin
            )

        session["teacher_grade"] = selected_grade
        return redirect(next_url or url_for("dashboard"))

    return render_template(
        "teacher_grade.html",
        grades=available_grades,
        next_url=next_url,
        is_admin=is_admin
    )


@app.route("/admin/teachers", methods=["GET", "POST"])
@admin_required
def admin_teachers():
    if request.method == "POST":
        action = request.form.get("action", "add_teacher")
        if action == "delete_teacher":
            teacher_id = request.form.get("teacher_id", type=int)
            teacher = db.session.get(Teacher, teacher_id) if teacher_id else None
            if not teacher:
                flash("Teacher account not found.", "danger")
                return redirect(url_for("admin_teachers"))

            username = teacher.username
            db.session.delete(teacher)
            db.session.commit()
            flash(f"Teacher account {username} deleted.", "success")
            return redirect(url_for("admin_teachers"))

        selected_grades = request.form.getlist("grades")
        if any(grade not in TEACHER_GRADES for grade in selected_grades):
            flash("One or more selected grades are invalid.", "danger")
            return redirect(url_for("admin_teachers"))

        assigned_grades = [
            grade for grade in TEACHER_GRADES if grade in selected_grades
        ]

        if action == "assign_grades":
            teacher_id = request.form.get("teacher_id", type=int)
            teacher = db.session.get(Teacher, teacher_id) if teacher_id else None
            if not teacher:
                flash("Teacher account not found.", "danger")
                return redirect(url_for("admin_teachers"))

            teacher.assigned_grades = assigned_grades
            db.session.commit()
            flash(f"Grade assignments saved for {teacher.username}.", "success")
            return redirect(url_for("admin_teachers"))

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            flash("Teacher username and password are required.", "danger")
            return redirect(url_for("admin_teachers"))
        if len(username) > 100:
            flash("Teacher username must be 100 characters or fewer.", "danger")
            return redirect(url_for("admin_teachers"))
        normalized_username = username.casefold()
        username_in_use = (
            normalized_username == "admin"
            or db.session.query(Teacher.id).filter(
                db.func.lower(Teacher.username) == normalized_username
            ).first() is not None
            or db.session.query(Admin.id).filter(
                db.func.lower(Admin.username) == normalized_username
            ).first() is not None
        )
        if username_in_use:
            flash("That username is already in use.", "danger")
            return redirect(url_for("admin_teachers"))

        teacher = Teacher(
            username=username,
            password=generate_password_hash(password),
            assigned_grades=assigned_grades
        )
        db.session.add(teacher)
        db.session.commit()
        flash(f"Teacher account {username} created.", "success")
        return redirect(url_for("admin_teachers"))

    teachers = Teacher.query.order_by(Teacher.username).all()
    return render_template(
        "manage_teachers.html",
        teachers=teachers,
        grades=TEACHER_GRADES
    )


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/api/otp/send", methods=["POST"])
def send_otp_api():
    data = request.get_json(silent=True) or {}
    api_key = data.get("api_key", "")
    email_address = (data.get("email") or "").strip()

    if api_key != config.OTP_API_KEY:
        return jsonify({"success": False, "message": "Invalid OTP API key."}), 401

    if not email_address:
        return jsonify({"success": False, "message": "Email is required."}), 400

    otp = generate_otp()
    save_otp(email_address, otp)

    sent = send_otp_email(email_address, otp)
    if not sent:
        return jsonify({"success": False, "message": "Unable to send OTP email."}), 500

    return jsonify({
        "success": True,
        "message": "OTP sent successfully.",
        "expires_in_minutes": config.OTP_TTL_MINUTES
    })


@app.route("/api/otp/verify", methods=["POST"])
def verify_otp_api():
    data = request.get_json(silent=True) or {}
    api_key = data.get("api_key", "")
    email_address = (data.get("email") or "").strip()
    otp = (data.get("otp") or "").strip()

    if api_key != config.OTP_API_KEY:
        return jsonify({"success": False, "message": "Invalid OTP API key."}), 401

    if not email_address or not otp:
        return jsonify({"success": False, "message": "Email and OTP are required."}), 400

    if verify_otp(email_address, otp):
        return jsonify({"success": True, "message": "OTP verified successfully."})

    return jsonify({"success": False, "message": "Invalid or expired OTP."}), 400

# ==========================================
# Dashboard
# ==========================================
@app.route("/dashboard")
@grade_access_required
def dashboard():
    teacher_grade = session["teacher_grade"]
    students = Student.query.filter_by(year=teacher_grade).all()
    student_ids = [student.id for student in students]

    total_students = len(students)

    total_attendance = Attendance.query.filter(
        Attendance.student_id.in_(student_ids)
    ).count() if student_ids else 0

    today = datetime.today().date()

    today_attendance = Attendance.query.filter(
        Attendance.date == today,
        Attendance.student_id.in_(student_ids)
    ).count() if student_ids else 0

    attendance = Attendance.query.filter(
        Attendance.student_id.in_(student_ids)
    ).order_by(Attendance.created_at.desc()).all() if student_ids else []

    return render_template(
        "dashboard.html",
        total_students=total_students,
        total_attendance=total_attendance,
        today_attendance=today_attendance,
        students=students,
        attendance=attendance,
        teacher_grade=teacher_grade
    )


@app.route("/api/attendance-assistant", methods=["POST"])
@admin_required
def attendance_assistant_api():
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"success": False, "message": "Please send a JSON object with a question."}), 400
    question = data.get("question")
    if not isinstance(question, str):
        question = ""
    question = question.strip()
    if not question:
        return jsonify({"success": False, "message": "Please enter a question."}), 400
    if len(question) > 300:
        return jsonify({"success": False, "message": "Please keep your question under 300 characters."}), 400
    try:
        message = answer_attendance_question(question, session["teacher_grade"])
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400
    return jsonify({"success": True, "message": message})


@app.route("/api/system-assistant", methods=["POST"])
def system_assistant_api():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"success": False, "message": "Please send a JSON object with a question."}), 400

    question = data.get("question")
    if not isinstance(question, str):
        question = ""
    question = question.strip()
    if not question:
        return jsonify({"success": False, "message": "Please enter a question."}), 400
    if len(question) > 300:
        return jsonify({"success": False, "message": "Please keep your question under 300 characters."}), 400

    live_data_terms = (
        "who is present", "who is absent", "list students", "student list",
        "attendance history", "attendance records", "how many students",
        "is present", "is absent", "roll number",
    )
    if any(term in question.casefold() for term in live_data_terms):
        is_admin = (
            session.get("admin_logged_in")
            and session.get("admin_username") == "admin"
        )
        teacher = (
            db.session.get(Teacher, session.get("teacher_id"))
            if session.get("teacher_logged_in")
            else None
        )
        grade = session.get("teacher_grade")
        has_grade_access = (
            grade in TEACHER_GRADES
            and (
                is_admin
                or (teacher and grade in (teacher.assigned_grades or []))
            )
        )
        if has_grade_access:
            try:
                message = answer_attendance_question(question, grade)
            except ValueError as error:
                return jsonify({"success": False, "message": str(error)}), 400
            return jsonify({"success": True, "message": message})
        return jsonify({
            "success": True,
            "message": "Student-specific attendance information is protected. Sign in as an admin or teacher and select an authorized grade to ask about live records.",
        })

    return jsonify({"success": True, "message": answer_system_question(question)})


# ==========================================
# Register Student (Admin Only)
# ==========================================
@app.route("/register", methods=["GET", "POST"])
@admin_required
def register():
    # NOTE: Admin authentication removed for registration to allow student
    # registration without signing in. If you want to restrict this, re-add
    # the admin session check and enable the login flow.

    if request.method == "POST":

        name = request.form.get("name")
        roll = request.form.get("roll")
        department = request.form.get("department")
        year = session["teacher_grade"]
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
@admin_required
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
@grade_access_required
def recognize_face():
    data = request.get_json() or {}
    image_data = data.get("image")

    teacher_grade = session.get("teacher_grade")
    if not teacher_grade:
        return jsonify({
            "recognized": False,
            "message": "Select a grade before starting face recognition."
        }), 403

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
        candidate_indices = [
            index for index, roll_number in enumerate(known_face_names)
            if (student := Student.query.filter_by(roll_number=roll_number).first())
            and student.year == teacher_grade
        ]

        if not candidate_indices:
            return jsonify({
                "recognized": False,
                "message": "No registered faces found for the selected grade."
            })

        candidate_encodings = [known_face_encodings[index] for index in candidate_indices]
        distances = face_recognition.face_distance(candidate_encodings, face_encoding)

        if len(distances) == 0:
            return jsonify({"recognized": False, "message": "No known faces available."})

        best_candidate_idx = int(np.argmin(distances))
        best_distance = float(distances[best_candidate_idx])

        if best_distance > config.FACE_TOLERANCE:
            return jsonify({"recognized": False, "message": "Face not recognized."})

        roll_number = known_face_names[candidate_indices[best_candidate_idx]]
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
@grade_access_required
def attendance_page():
    if request.args.get("public") == "1":
        requested_grade = request.args.get("grade") or "11th"
        if requested_grade in TEACHER_GRADES:
            session["teacher_grade"] = requested_grade
            session["guest_attendance"] = True
    return render_template("attendance.html")

@app.route("/attendance_calendar")
@grade_access_required
def attendance_calendar_page():
    return render_template("attendance_calendar.html")

# ==========================================
# Attendance API
# ==========================================
@app.route("/api/attendance")
@grade_access_required
def attendance_api():

    students = Student.query.filter_by(year=session["teacher_grade"]).all()
    student_ids = [student.id for student in students]
    attendance = Attendance.query.filter(
        Attendance.student_id.in_(student_ids)
    ).order_by(
        Attendance.created_at.desc()
    ).all() if student_ids else []

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
@grade_access_required
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

    teacher_grade = session.get("teacher_grade")
    students = Student.query.filter_by(year=teacher_grade).order_by(
        Student.roll_number
    ).all()
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
@grade_access_required
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
    if student.year != session["teacher_grade"]:
        return jsonify({"recognized": False, "message": "Voice does not match a student in the selected grade."}), 403

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
@grade_access_required
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
    if not student or student.year != session["teacher_grade"]:
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
@grade_access_required
def mark_attendance_override():
    data = request.get_json() or {}
    roll = data.get("roll_number")
    if not roll:
        return jsonify({"success": False, "message": "roll_number required"}), 400
    student = Student.query.filter_by(roll_number=roll).first()
    if not student or student.year != session["teacher_grade"]:
        return jsonify({"success": False, "message": "student not found"}), 404

    success, message = AttendanceManager.mark_attendance(student.roll_number, identifier="roll")
    status_code = 200 if success else 400
    return jsonify({"success": success, "message": message}), status_code


@app.route("/api/mark_attendance", methods=["POST"])
@grade_access_required
def mark_attendance_api():
    data = request.get_json() or {}
    roll_number = data.get("roll_number")
    student_name = data.get("name")
    voice_data = data.get("voice")

    if not roll_number and not student_name:
        return jsonify({"success": False, "message": "roll_number or name is required."}), 400

    if not voice_data:
        return jsonify({"success": False, "message": "Voice sample is required for verification."}), 400

    teacher_grade = session.get("teacher_grade")
    if roll_number:
        student = Student.query.filter_by(roll_number=roll_number).first()
        if not student or student.year != teacher_grade:
            return jsonify({
                "success": False,
                "message": "Student does not belong to the selected grade."
            }), 403

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
        if student.year != teacher_grade:
            return jsonify({
                "success": False,
                "message": "Voice does not match a student in the selected grade."
            }), 403

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
@grade_access_required
def students_api():

    students = Student.query.filter_by(year=session["teacher_grade"]).all()

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
@admin_required
def delete_student_api():
    data = request.get_json() or {}
    roll_number = data.get("roll_number")
    teacher_grade = session.get("teacher_grade")

    if not roll_number:
        return jsonify({"success": False, "message": "roll_number is required."}), 400
    if not teacher_grade:
        return jsonify({"success": False, "message": "Select a class before deleting a student."}), 403

    try:
        student = Student.query.filter_by(
            roll_number=roll_number,
            year=teacher_grade
        ).first()
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
        debug=os.getenv("FLASK_DEBUG", "0").lower() in {"1", "true", "yes"},
        host="0.0.0.0",
        port=config.PORT,
        ssl_context="adhoc" if config.ENABLE_HTTPS else None
    )