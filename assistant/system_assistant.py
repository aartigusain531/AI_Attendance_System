"""Local help for setup, use, and troubleshooting of the attendance system."""

from assistant.attendance_assistant import get_general_answer


_ANSWERS = (
    (
        (
            "what is this system", "what is this app", "about this system",
            "about the app", "what does this system",
        ),
        "This is a Flask-based AI attendance web app. It registers students, "
        "uses face recognition and voice verification during camera attendance, "
        "and lets authorized admins and teachers review grade-based attendance "
        "records and reports.",
    ),
    (
        ("feature", "features", "what can", "capabilities", "what do you do"),
        "The system includes admin and teacher accounts, grade assignment, "
        "student registration, face and voice verification, camera-based "
        "attendance, teacher photo attendance, a grade dashboard, and a "
        "date-based attendance calendar. I can explain any of these or help "
        "troubleshoot a problem.",
    ),
    (
        ("camera permission", "camera access", "allow camera", "https"),
        "Open Start Attendance and allow Camera when your browser asks. Camera "
        "access requires HTTPS, except on localhost. If you blocked it earlier, "
        "open the site-controls icon beside the address bar, allow Camera, and "
        "reload the page. Close other apps that may be using the camera.",
    ),
    (
        ("microphone permission", "microphone access", "allow microphone", "mic"),
        "Admin camera attendance also needs microphone access for voice "
        "verification. Allow Microphone in the browser prompt. If it was blocked, "
        "change the permission from the site-controls icon beside the address "
        "bar and reload. Microphone access requires HTTPS, except on localhost.",
    ),
    (
        ("face", "camera", "recognition"),
        "For camera attendance, the app compares the camera image with registered "
        "face data. Make sure the student is registered, the face is well lit and "
        "visible, and the camera permission is allowed. Teachers can also mark "
        "attendance by uploading student photos from their dashboard.",
    ),
    (
        ("voice", "audio"),
        "The admin camera attendance flow asks for a short voice sample after "
        "face recognition. The student needs a usable voice sample saved during "
        "registration. Check microphone permission, reduce background noise, and "
        "try again. Teacher photo attendance does not use this camera-and-voice flow.",
    ),
    (
        (
            "how attendance works", "how attendance work", "mark attendance",
            "take attendance", "attendance process",
        ),
        "Admins select a grade and use Start Attendance with camera and "
        "microphone verification. Teachers sign in, select an assigned grade, "
        "and can upload one or more student photos from the dashboard. Successful "
        "checks create attendance records for that grade and date.",
    ),
    (
        ("teacher", "admin", "login", "sign in", "account", "password"),
        "Admins use Admin Login and can manage teacher accounts and their grade "
        "assignments. Teachers use Teacher Login, then choose one of their "
        "assigned grades. Each dashboard and its student records are limited to "
        "the selected grade. The admin username is admin; teacher accounts are "
        "created by the admin from Manage Teachers.",
    ),
    (
        ("grade", "class", "change grade"),
        "The available grades are LKG, UKG, and 1st through 12th. Admins can "
        "select a grade; teachers can select only grades assigned to their "
        "account. Use Change Grade on the dashboard to switch between grades "
        "you are authorized to access.",
    ),
    (
        (
            "register student", "student registration", "enroll", "add student",
            "new student",
        ),
        "Sign in with an authorized account and open student registration from "
        "the dashboard. Enter the student's details and capture the requested "
        "face and voice samples. Use a clear, well-lit face image and a quiet "
        "voice recording so the student can be verified later.",
    ),
    (
        ("dashboard", "report", "calendar", "history", "records"),
        "The dashboard shows the roster and attendance summary for the selected "
        "grade. Open Attendance Calendar to choose a date and review attendance. "
        "Teachers can upload single or multiple student photos from their "
        "dashboard; student-specific records are available only after signing "
        "in with access to that grade.",
    ),
    (
        ("database", "data", "privacy", "stored", "save", "where"),
        "Student and attendance records are stored in the application's "
        "configured database (SQLite by default). Face images and voice samples "
        "are kept in the app's local data folders. This help bot uses local "
        "guidance and does not send questions or attendance data to an external "
        "AI service. Live student details require an authorized account and grade.",
    ),
    (
        ("install", "installation", "start the app", "run the app", "setup"),
        "Use Python 3.11 for the pinned computer-vision packages. From the "
        "project directory, create and activate a virtual environment, install "
        "requirements.txt, then run `python app.py`. Open the HTTPS localhost "
        "address printed by the server (usually https://localhost:5001) and "
        "accept the local certificate warning. See README.md for full setup steps.",
    ),
    (
        ("error", "not working", "troubleshoot", "problem", "failed", "issue"),
        "I can help troubleshoot. For camera or microphone issues, allow the "
        "browser permission, use HTTPS or localhost, and close other apps using "
        "the device. For recognition failures, check that the student is "
        "registered with clear face and voice samples. For login or data issues, "
        "confirm the selected grade and account access. Tell me the page, what "
        "you tried, and the exact error message for more specific help.",
    ),
)


def answer_system_question(question):
    general_answer = get_general_answer(question)
    if general_answer:
        return general_answer

    text = question.casefold()
    for keywords, answer in _ANSWERS:
        if any(keyword in text for keyword in keywords):
            return answer

    return (
        "I can help with setup, login and grade access, student registration, "
        "face or voice verification, attendance, reports, privacy, and "
        "troubleshooting. Ask a question about one of these, or describe the "
        "page you are on and the exact error. For live student attendance, sign "
        "in with an account authorized for the selected grade."
    )
