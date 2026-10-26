def answer_system_question(question):
    text = question.casefold()

    answers = (
        (
            ("camera permission", "microphone permission", "permission", "https"),
            "Choose Start Attendance and approve the browser's camera and microphone prompts. Browsers require HTTPS for these permissions, except on localhost. If you previously blocked access, use the site-controls icon beside the address bar to allow Camera and Microphone, then reload.",
        ),
        (
            (
                "about this system", "about the app", "what is this system",
                "what is this app", "what does this system",
            ),
            "This is an AI attendance web app. It uses face recognition to identify a registered student, then checks a short voice sample before recording attendance. Admins and teachers can manage classes and review attendance from the dashboard.",
        ),
        (
            ("feature", "features", "what can", "capabilities"),
            "The system supports admin and teacher accounts, grade selection, student registration, face recognition, voice verification, automatic attendance marking, daily attendance summaries, and a date-based attendance calendar.",
        ),
        (
            ("face", "camera"),
            "The attendance page asks for camera access, then checks the camera feed against registered face data. Camera access is granted by your browser after you approve its permission prompt.",
        ),
        (
            ("voice", "microphone", "audio"),
            "After a face is recognized, the attendance flow records a short voice sample and verifies it against registered voice samples. Microphone access is granted by your browser after you approve its permission prompt.",
        ),
        (
            ("present", "absent", "mark attendance", "how attendance", "attendance work"),
            "To take attendance, open Start Attendance, allow camera and microphone access, and let the system verify the student's face and voice. A successful verification records attendance for the selected grade and date. The dashboard shows students with records as present and those without a record as absent.",
        ),
        (
            ("login", "account", "teacher", "admin", "grade", "class"),
            "Admins sign in with the Admin Login page and can manage teacher accounts and grade assignments. Teachers use Teacher Login, then select one of their assigned grades. The dashboard and attendance records are scoped to the selected grade.",
        ),
        (
            ("register", "enroll", "add student"),
            "Student registration is available from the dashboard for an authorized account. The registration flow saves the student's details, face image, and voice sample so they can be recognized during attendance.",
        ),
        (
            ("dashboard", "report", "calendar", "history", "record"),
            "The dashboard shows the selected grade's student roster and today's attendance summary. Use the Attendance Calendar to select a date and review who was present or absent. Student-specific attendance details require an authorized account.",
        ),
        (
            ("data", "database", "privacy", "stored", "save"),
            "The app stores student and attendance records in its configured database and keeps face images and voice samples in its local data folders. This built-in help chatbot uses the app's own guidance and does not send your question to an external AI service.",
        ),
        (
            ("error", "not working", "troubleshoot", "problem", "failed"),
            "For camera or microphone problems, check the browser's site permissions, use HTTPS or localhost, and make sure another app is not using the device. If recognition fails, confirm that the student is registered with usable face and voice samples.",
        ),
    )

    for keywords, answer in answers:
        if any(keyword in text for keyword in keywords):
            return answer

    return (
        "I can help explain this attendance system, including face and voice verification, "
        "camera and microphone permissions, accounts and grade access, student registration, "
        "attendance marking, reports, and troubleshooting. Ask me about one of those topics. "
        "Student-specific records are available only to authorized accounts."
    )
