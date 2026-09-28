# AI Attendance System - Pure Python Flask Application

**100% Python Application** - Built with Flask, OpenCV, and Face Recognition

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation

```bash
# Navigate to project directory
cd AI_Attendance_System

# Install dependencies
python3 -m pip install -r requirements.txt --break-system-packages

# Run the application
python3 app.py
```

**Access the application:** https://localhost:5001

The server listens on `0.0.0.0` on fixed local port `5001`. Local development
uses Flask's temporary HTTPS certificate so camera and microphone access also
works from another device on the same network. Open the `https://` address
printed by the launcher and accept the browser's certificate warning once.
Set `ENABLE_HTTPS=0` only when HTTPS is terminated by a reverse proxy or
hosting platform.

---

## 📋 Features

✅ **Admin Authentication** - Secure login system  
✅ **Student Registration** - Register students with face and voice  
✅ **Face Recognition** - Automatic student identification  
✅ **Voice Recognition** - Voice-based verification  
✅ **Attendance Marking** - Automatic and manual attendance  
✅ **Dashboard** - Real-time attendance statistics  
✅ **Reports** - Generate attendance reports  
✅ **OTP Authentication** - Email-based OTP verification  

---

## 📁 Project Structure

```
AI_Attendance_System/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── utils.py              # Python utility functions
├── requirements.txt      # Python dependencies
├── setup.py              # Python package setup
│
├── models/
│   ├── database.py       # SQLAlchemy models
│   ├── attendance.py     # Attendance management
│   ├── face.py           # Face recognition
│   ├── voice.py          # Voice recognition
│   └── train_face.py     # Face model training
│
├── templates/            # Flask HTML templates
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   └── attendance.html
│
├── static/
│   ├── css/style.css     # Styling
│   └── js/app.js         # Client-side logic
│
└── dataset/
    ├── faces/            # Face images
    └── voices/           # Voice samples
```

---

## 🔧 Configuration

Edit `config.py` to customize:

```python
# Database
DATABASE_NAME = "attendance.db"

# Flask
SECRET_KEY = "AI_Attendance_System_2026"

# Face Recognition
FACE_TOLERANCE = 0.45
MODEL_TYPE = "hog"  # Use "cnn" for GPU

# Voice Recognition
SAMPLE_RATE = 16000
VOICE_MATCH_THRESHOLD = 0.7

# SMTP (Email)
SMTP_SERVER = os.getenv("SMTP_SERVER", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
```

---

## 📊 API Endpoints

### Admin Routes
- `GET /` - Dashboard home
- `GET /login` - Admin login
- `POST /login` - Login verification
- `GET /logout` - Logout
- `GET /dashboard` - Admin dashboard

### Student Routes
- `GET /register` - Registration form
- `POST /register` - Register student
- `GET /attendance` - Attendance page

### API Endpoints
- `POST /api/otp/send` - Send OTP
- `POST /api/otp/verify` - Verify OTP
- `POST /api/recognize_face` - Face recognition
- `POST /api/recognize_voice` - Voice recognition
- `POST /api/mark_attendance` - Mark attendance
- `POST /api/delete_student` - Delete student
- `GET /api/info` - API information

---

## 🗄️ Database

Automatically creates SQLite database (`attendance.db`) with:
- **Students** - Student information
- **Attendance** - Attendance records
- **Admins** - Admin accounts

---

## 🔐 Setup Admin Account

```bash
python3 setup_admin.py
```

Default credentials:
- Username: `admin`
- Password: `admin123`

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Kill process on port 5000
sudo fuser -k 5000/tcp

# Or run on different port
python3 app.py --port 5001
```

### Import Errors
```bash
# Reinstall dependencies
python3 -m pip install -r requirements.txt --break-system-packages --force-reinstall
```

### Camera/Microphone Issues
- Ensure webcam is connected
- Use Chrome's address bar lock icon to set Camera and Microphone to **Allow**, then reload.
- `localhost` works over HTTP. A phone or another computer must use HTTPS; plain `http://192.168.x.x:5000` is blocked by Chrome by design.
- On the server computer, open `https://localhost:5001` and accept the development certificate warning. On another device, open `https://<server-ip>:5001` using the server's LAN IP, accept the warning, then allow Camera and Microphone. If the page does not load, allow TCP port 5001 through the server firewall. For Google Cloud Run, keep `ENABLE_HTTPS=0`; Cloud Run provides HTTPS at its public URL.
- Camera and microphone permission cannot be silently forced by a website. Chrome requires the user to approve it for privacy and security.
- Update OpenCV: `pip install opencv-python --upgrade`

---

## 📱 Development

### Running in Debug Mode
```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
python3 app.py
```

### Testing
```bash
python3 -m pytest tests/
```

---

## 🚀 Deployment

### Production Setup
```bash
# Install dependencies, including Gunicorn
python3 -m pip install -r requirements.txt

# Run with Gunicorn
PORT=5000 gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 180 app:app
```

### Google Cloud Run

Cloud Run is the recommended Google deployment target:

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/ai-attendance
gcloud run deploy ai-attendance \
    --image gcr.io/YOUR_PROJECT_ID/ai-attendance \
    --region YOUR_REGION \
    --allow-unauthenticated \
    --set-env-vars SECRET_KEY="REPLACE_WITH_A_LONG_RANDOM_VALUE",ENABLE_HTTPS=0
```

Cloud Run's local filesystem is temporary. SQLite, uploaded faces, voices,
and reports are suitable for local development only. For production, set
`DATABASE_URL` to managed PostgreSQL/Cloud SQL and move dataset/report files
to durable object storage or a mounted persistent volume. The application
reads `DATABASE_URL`, `DATASET_FOLDER`, `UPLOAD_FOLDER`, and `REPORT_FOLDER`
from the environment.

Cloud Run supplies `PORT` automatically. The included `Dockerfile` starts
Gunicorn on that port and exposes `/healthz` and `/readyz`.

### Docker
```bash
# Build image
docker build -t ai-attendance .

# Run container
docker run --env PORT=8080 -p 5000:8080 ai-attendance
```

---

## 📝 Requirements

- **Flask** - Web framework
- **Flask-SQLAlchemy** - Database ORM
- **OpenCV** - Computer vision
- **face_recognition** - Face detection
- **scipy** - Audio processing
- **Pillow** - Image processing
- **sounddevice** - Audio input

Full list: See `requirements.txt`

---

## 📄 License

MIT License - See LICENSE file

---

## 👨‍💻 Author

**Piyush** - AI Attendance System Developer

---

## 💡 Tips

- Use **"hog"** model for CPU (faster)
- Use **"cnn"** model for GPU (more accurate)
- Train faces regularly for better recognition
- Store voice samples in WAV format
- Backup database regularly

---

## ✅ Checklist

- [ ] Install Python 3.8+
- [ ] Install dependencies
- [ ] Run setup_admin.py
- [ ] Start Flask app
- [ ] Access http://localhost:5000
- [ ] Login with admin credentials
- [ ] Register test student
- [ ] Test face/voice recognition

---

**Questions?** Check the logs in terminal for detailed error messages.
