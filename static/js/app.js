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