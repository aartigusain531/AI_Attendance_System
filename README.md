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

**Access the application:** http://localhost:5000

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
- Check microphone permissions
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
# Install production server
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker
```bash
# Build image
docker build -t ai-attendance .

# Run container
docker run -p 5000:5000 ai-attendance
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
