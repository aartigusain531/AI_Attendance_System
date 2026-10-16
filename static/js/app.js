// =============================
// AI Attendance System
// app.js
// =============================

console.log("AI Attendance System Started...");

// -----------------------------
// Welcome Message
// -----------------------------
window.onload = function () {
    showNotification("🤖 AI Attendance System Ready", "success");
    startClock();
};

// -----------------------------
// Live Clock
// -----------------------------
function startClock() {

    const clock = document.getElementById("clock");

    if (!clock) return;

    setInterval(() => {

        const now = new Date();

        clock.innerHTML = now.toLocaleString();

    }, 1000);

}

// -----------------------------
// Notification
// -----------------------------
function showNotification(message, type = "info") {

    const notification = document.createElement("div");

    notification.className = "notification " + type;

    notification.innerHTML = message;

    document.body.appendChild(notification);

    setTimeout(() => {

        notification.classList.add("show");

    }, 100);

    setTimeout(() => {

        notification.classList.remove("show");

        setTimeout(() => {

            notification.remove();

        }, 300);

    }, 3000);

}

// -----------------------------
// Button Animation
// -----------------------------
document.querySelectorAll(".btn").forEach(button => {

    button.addEventListener("mouseenter", () => {

        button.style.transform = "scale(1.05)";

    });

    button.addEventListener("mouseleave", () => {

        button.style.transform = "scale(1)";

    });

});

// -----------------------------
// Check Backend
// -----------------------------
async function checkServer() {

    try {

        const response = await fetch("/api/info");

        if (response.ok) {

            console.log("Backend Connected");

        }

    } catch (error) {

        console.log("Backend Offline");

    }

}

checkServer();

// -----------------------------
// Voice Animation
// -----------------------------
function voiceListening() {

    showNotification("🎤 Listening...", "info");

}

// -----------------------------
// Camera Animation
// -----------------------------
function cameraStarted() {

    showNotification("📷 Camera Started", "success");

}

// -----------------------------
// Attendance Success
// -----------------------------
function attendanceSuccess(name) {

    showNotification("✅ Attendance Marked : " + name, "success");

}

// -----------------------------
// Attendance Failed
// -----------------------------
function attendanceFailed() {

    showNotification("❌ Verification Failed", "error");

}

// -----------------------------
// Register Success
// -----------------------------
function registerSuccess() {

    showNotification("🎉 Student Registered Successfully", "success");

}

// -----------------------------
// AI Loading Animation
// -----------------------------
function loadingAI() {

    let loader = document.getElementById("loader");

    if(loader){

        loader.style.display = "block";

    }

}

function stopLoadingAI(){

    let loader = document.getElementById("loader");

    if(loader){

        loader.style.display = "none";

    }

}

// -----------------------------
// Home page chatbot
// -----------------------------
function getBotReply(inputText) {

    const text = inputText.toLowerCase();

    if (!text.trim()) {
        return "Please ask a question about the app or attendance.";
    }

    if (text.includes("hello") || text.includes("hi") || text.includes("hey")) {
        return "Hello! This is the AI Attendance System. I can explain the app and tell how present/absent status is tracked.";
    }

    if (text.includes("what") && (text.includes("app") || text.includes("system") || text.includes("this"))) {
        return "This app is an AI attendance system that uses face recognition and voice recognition to identify students, mark attendance, and show live reports for each class.";
    }

    if (text.includes("how") || text.includes("works") || text.includes("feature") || text.includes("features")) {
        return "The app lets admins and teachers log in, choose a class, register students, verify faces or voices, mark attendance, and view reports for present and absent students.";
    }

    if ((text.includes("present") || text.includes("absent") || text.includes("attendance")) && (text.includes("class") || text.includes("grade") || text.includes("glass") || text.includes("student"))) {
        return "For a class or grade, students with a valid attendance record for that day are marked present, and students without a record are marked absent. The system uses face and voice verification before recording attendance.";
    }

    if (text.includes("login") || text.includes("admin") || text.includes("teacher")) {
        return "Admins and teachers can log in from the homepage. After login, they can select a class and manage attendance records.";
    }

    if (text.includes("face") || text.includes("voice") || text.includes("recognition")) {
        return "Students are identified using face recognition and voice recognition. The system confirms the identity before marking attendance.";
    }

    if (text.includes("report") || text.includes("dashboard")) {
        return "The dashboard shows attendance details, student records, and reports for the selected class or grade.";
    }

    return "I can explain the app, show how attendance works, or tell you how present and absent students are tracked. Try asking: 'What is this app?' or 'How are present and absent students marked?'";
}

function addChatMessage(message, sender = "bot") {

    const messages = document.getElementById("chatbotMessages");

    if (!messages) return;

    const messageBox = document.createElement("div");

    messageBox.className = `message ${sender === "user" ? "user-message" : "bot-message"}`;
    messageBox.textContent = message;

    messages.appendChild(messageBox);
    messages.scrollTop = messages.scrollHeight;
}

const chatbotForm = document.getElementById("chatbotForm");

if (chatbotForm) {
    chatbotForm.addEventListener("submit", function (event) {
        event.preventDefault();

        const input = document.getElementById("chatbotInput");

        if (!input) return;

        const question = input.value.trim();

        if (!question) return;

        addChatMessage(question, "user");
        input.value = "";

        const reply = getBotReply(question);

        setTimeout(() => {
            addChatMessage(reply, "bot");
        }, 250);
    });
}
