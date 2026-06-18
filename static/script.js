document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chat-form");
    const userInput = document.getElementById("user-input");
    const messagesList = document.getElementById("messages-list");
    const welcomeScreen = document.getElementById("welcome-screen");
    const resetBtn = document.getElementById("reset-btn");
    const sendBtn = document.getElementById("send-btn");

    // Scroll to bottom helper
    const scrollToBottom = () => {
        messagesList.scrollTop = messagesList.scrollHeight;
    };

    // Format LLM plain text response to HTML (bolding, spacing, lists)
    const formatResponse = (text) => {
        // Escape basic HTML
        let escaped = text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");

        // Bold text replacement (**text**)
        escaped = escaped.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

        // Split lines and parse lists
        const lines = escaped.split("\n");
        let result = [];
        let inList = false;
        let listType = null; // 'ul' or 'ol'

        lines.forEach(lineRaw => {
            const line = lineRaw.trim();
            if (!line) {
                if (inList) {
                    result.push(listType === 'ol' ? "</ol>" : "</ul>");
                    inList = false;
                    listType = null;
                }
                result.push("<br>");
                return;
            }

            // Check numbered list (e.g. 1. Item)
            const olMatch = line.match(/^(\d+)\.\s+(.*)/);
            // Check bullet list (e.g. - Item or * Item)
            const ulMatch = line.match(/^[-*]\s+(.*)/);

            if (olMatch) {
                if (inList && listType !== 'ol') {
                    result.push("</ul>");
                    inList = false;
                }
                if (!inList) {
                    result.push("<ol>");
                    inList = true;
                    listType = 'ol';
                }
                result.push(`<li>${olMatch[2]}</li>`);
            } else if (ulMatch) {
                if (inList && listType !== 'ul') {
                    result.push("</ol>");
                    inList = false;
                }
                if (!inList) {
                    result.push("<ul>");
                    inList = true;
                    listType = 'ul';
                }
                result.push(`<li>${ulMatch[1]}</li>`);
            } else {
                if (inList) {
                    result.push(listType === 'ol' ? "</ol>" : "</ul>");
                    inList = false;
                    listType = null;
                }
                result.push(`<p>${line}</p>`);
            }
        });

        if (inList) {
            result.push(listType === 'ol' ? "</ol>" : "</ul>");
        }

        // Clean up empty lines/duplicates
        return result.join("").replace(/(<br>)+/g, "<br>");
    };

    // Add a message item to the list
    const appendMessage = (sender, content) => {
        // Hide welcome screen if active
        if (welcomeScreen && welcomeScreen.style.display !== "none") {
            welcomeScreen.style.display = "none";
        }

        const messageEl = document.createElement("div");
        messageEl.classList.add("message", sender);

        const avatarEl = document.createElement("div");
        avatarEl.classList.add("avatar");

        if (sender === "user") {
            avatarEl.innerHTML = `
                <svg class="avatar-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                    <circle cx="12" cy="7" r="4"/>
                </svg>
            `;
        } else {
            avatarEl.innerHTML = `
                <svg class="avatar-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                </svg>
            `;
        }

        const contentEl = document.createElement("div");
        contentEl.classList.add("message-content");
        contentEl.innerHTML = sender === "user" ? `<p>${content}</p>` : formatResponse(content);

        messageEl.appendChild(avatarEl);
        messageEl.appendChild(contentEl);
        messagesList.appendChild(messageEl);

        scrollToBottom();
    };

    // Typing indicator component
    let typingIndicatorEl = null;

    const showTypingIndicator = () => {
        if (typingIndicatorEl) return;

        typingIndicatorEl = document.createElement("div");
        typingIndicatorEl.classList.add("message", "assistant");

        const avatarEl = document.createElement("div");
        avatarEl.classList.add("avatar");
        avatarEl.innerHTML = `
            <svg class="avatar-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
        `;

        const contentEl = document.createElement("div");
        contentEl.classList.add("message-content");
        contentEl.innerHTML = `
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;

        typingIndicatorEl.appendChild(avatarEl);
        typingIndicatorEl.appendChild(contentEl);
        messagesList.appendChild(typingIndicatorEl);

        scrollToBottom();
    };

    const removeTypingIndicator = () => {
        if (typingIndicatorEl) {
            typingIndicatorEl.remove();
            typingIndicatorEl = null;
        }
    };

    // Send chat logic
    const handleSend = async (messageText) => {
        const text = messageText.trim();
        if (!text) return;

        appendMessage("user", text);
        userInput.value = "";
        userInput.focus();

        // Disable inputs
        userInput.disabled = true;
        sendBtn.disabled = true;

        showTypingIndicator();

        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ message: text }),
            });

            if (!response.ok) {
                throw new Error("HTTP connection error");
            }

            const data = await response.json();
            removeTypingIndicator();

            if (data.response) {
                appendMessage("assistant", data.response);
            } else if (data.error) {
                appendMessage("assistant", "⚠️ Error: " + data.error);
            }
        } catch (error) {
            removeTypingIndicator();
            appendMessage("assistant", "⚠️ Connection failed. Make sure Python server is running.");
            console.error(error);
        } finally {
            userInput.disabled = false;
            sendBtn.disabled = false;
            userInput.focus();
        }
    };

    // Handle form submit
    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        handleSend(userInput.value);
    });

    // Handle Reset Button
    resetBtn.addEventListener("click", async () => {
        if (confirm("Are you sure you want to reset the conversation history?")) {
            try {
                const response = await fetch("/api/reset", { method: "POST" });
                if (response.ok) {
                    // Remove all chat message elements
                    const messages = messagesList.querySelectorAll(".message");
                    messages.forEach(msg => msg.remove());
                    // Restore welcome screen
                    if (welcomeScreen) {
                        welcomeScreen.style.display = "flex";
                    }
                }
            } catch (err) {
                alert("Failed to reset session history.");
                console.error(err);
            }
        }
    });

    // Handle Quick Action Buttons
    document.querySelectorAll(".quick-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const prompt = btn.getAttribute("data-prompt");
            if (prompt) {
                handleSend(prompt);
            }
        });
    });

    // Handle Welcome Screen Starter Cards
    document.querySelectorAll(".starter-card").forEach(card => {
        card.addEventListener("click", () => {
            const prompt = card.getAttribute("data-prompt");
            if (prompt) {
                handleSend(prompt);
            }
        });
    });

    // Focus input on load
    userInput.focus();
});
