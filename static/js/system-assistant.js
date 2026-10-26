const chatbotForm = document.getElementById("chatbotForm");

if (chatbotForm) {
    const chatbotInput = document.getElementById("chatbotInput");
    const chatbotMessages = document.getElementById("chatbotMessages");
    const chatbotSend = chatbotForm.querySelector("button[type='submit']");

    function addChatMessage(message, sender) {
        const messageBox = document.createElement("div");
        messageBox.className = `message ${sender === "user" ? "user-message" : "bot-message"}`;
        messageBox.textContent = message;
        chatbotMessages.appendChild(messageBox);
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    }

    chatbotForm.addEventListener("submit", async event => {
        event.preventDefault();
        const question = chatbotInput.value.trim();
        if (!question) return;

        addChatMessage(question, "user");
        chatbotInput.value = "";
        chatbotSend.disabled = true;

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
            chatbotSend.disabled = false;
            chatbotInput.focus();
        }
    });
}
