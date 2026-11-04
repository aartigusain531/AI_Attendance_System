const chatbotForm = document.getElementById("chatbotForm");

if (chatbotForm) {
    const chatbotInput = document.getElementById("chatbotInput");
    const chatbotMessages = document.getElementById("chatbotMessages");
    const chatbotSend = chatbotForm.querySelector("button[type='submit']");
    const chatbotReset = document.getElementById("chatbotReset");
    const chatbotSuggestions = document.querySelector(".chatbot-suggestions");

    function addChatMessage(message, sender) {
        const messageBox = document.createElement("div");
        messageBox.className = `message ${sender === "user" ? "user-message" : "bot-message"}`;
        messageBox.textContent = message;
        chatbotMessages.appendChild(messageBox);
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    }

    async function sendQuestion(question) {
        if (!question || chatbotSend.disabled) return;
        addChatMessage(question, "user");
        chatbotSend.disabled = true;
        chatbotInput.disabled = true;
        chatbotReset.disabled = true;
        chatbotSuggestions.querySelectorAll("button").forEach(button => {
            button.disabled = true;
        });

        const typingIndicator = document.createElement("div");
        typingIndicator.className = "message bot-message typing-indicator";
        typingIndicator.setAttribute("role", "status");
        typingIndicator.textContent = "Looking through system help…";
        chatbotMessages.appendChild(typingIndicator);
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;

        try {
            const response = await fetch("/api/system-assistant", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question })
            });
            const result = await response.json();
            if (!response.ok || !result.success) {
                addChatMessage(result.message || "I couldn't answer that. Please try again.", "bot");
            } else {
                addChatMessage(result.message, "bot");
            }
        } catch (error) {
            console.error("System assistant request failed:", error);
            addChatMessage("Could not connect to the system assistant. Please try again.", "bot");
        } finally {
            typingIndicator.remove();
            chatbotSend.disabled = false;
            chatbotInput.disabled = false;
            chatbotReset.disabled = false;
            chatbotSuggestions.querySelectorAll("button").forEach(button => {
                button.disabled = false;
            });
            chatbotInput.focus();
        }
    }

    chatbotForm.addEventListener("submit", event => {
        event.preventDefault();
        const question = chatbotInput.value.trim();
        if (!question) return;
        chatbotInput.value = "";
        sendQuestion(question);
    });

    chatbotSuggestions.addEventListener("click", event => {
        const button = event.target.closest("button[data-question]");
        if (!button) return;
        sendQuestion(button.dataset.question);
    });

    chatbotReset.addEventListener("click", () => {
        chatbotMessages.replaceChildren();
        addChatMessage(
            "Hi! I’m your AI Attendance System assistant. I can explain how to use the app and help troubleshoot setup, login, student registration, camera or voice verification, attendance, and reports. What can I help with?",
            "bot"
        );
        chatbotInput.value = "";
        chatbotInput.focus();
    });
}
