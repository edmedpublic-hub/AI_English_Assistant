// reading.feedback.js
import { renderHighlighted } from "./reading.text.js";

const getFeedbackBtn = document.getElementById("get-feedback-btn");
const feedbackBox = document.getElementById("feedbackBox");

// ----------------------
// CSRF COOKIE READER
// ----------------------
function getCookie(name) {
  const cookieValue = document.cookie
    .split("; ")
    .find((row) => row.startsWith(name + "="));
  return cookieValue ? decodeURIComponent(cookieValue.split("=")[1]) : null;
}

const csrftoken = getCookie("csrftoken");

// ----------------------
// HTML ESCAPE
// ----------------------
function escapeHtml(s) {
  return (s + "").replace(/[&<>"'`=\/]/g, function (c) {
    return {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
      "/": "&#x2F;",
      "`": "&#x60;",
      "=": "&#x3D;",
    }[c];
  });
}

// ----------------------
// INITIALIZE FEEDBACK
// ----------------------
export function initFeedback() {
  if (!getFeedbackBtn) return;

  getFeedbackBtn.addEventListener("click", async () => {
    const transcript = (window.transcriptAcc || "").trim();

    if (!transcript) {
      feedbackBox.textContent = "No speech recorded.";
      return;
    }

    feedbackBox.textContent = "Analyzing...";

    // ---- PAYLOAD ----
    const payload = {
      expected: window.lessonText || "",
      spoken: transcript,
    };

    try {
      const res = await fetch("/api/reading/feedback/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          // X-CSRFToken is correctly included here for security
          "X-CSRFToken": csrftoken,
        },
        body: JSON.stringify(payload),
        credentials: "same-origin",
      });

      // ---- CHECK SERVER RESPONSE ----
      if (!res.ok) {
        let errorText = await res.text();
        feedbackBox.textContent = "Server error: " + (errorText || res.status);
        return;
      }

      const data = await res.json();
      const score = data.score || 0;
      const feedback = data.feedback || "No specific feedback.";
      const mispronouncedWords = Array.isArray(data.mispronounced)
        ? data.mispronounced
        : [];

      // ---- DISPLAY SCORE + FEEDBACK ----
      let highlightMessage = "";

      // The frontend highlighting logic is correct, but relies on backend data.
      if (mispronouncedWords.length) {
        // ---- MISPRONUNCIATION HIGHLIGHTING (If data is present) ----
        const wordsToFlag = new Set(
          mispronouncedWords.map((m) => m.word.toLowerCase())
        );

        window.displayedSentences = window.originalSentences.map((sentence) => {
          return sentence
            .split(/\b/)
            .map((token) => {
              const clean = token.replace(/[^\w']/g, "").toLowerCase();
              if (wordsToFlag.has(clean)) {
                return `<span class="mispronounced">${token}</span>`;
              }
              return escapeHtml(token);
            })
            .join("");
        });

        renderHighlighted(window.currentIndex);
        highlightMessage = " (Words highlighted above)";
      } else {
        // Add a clear message when highlighting data is empty (the current state)
        highlightMessage = " (Highlighting feature pending AI integration.)";
      }

      feedbackBox.innerHTML = `
        <div><strong>Score:</strong> ${score}%</div>
        <div><strong>Feedback:</strong> ${feedback}${highlightMessage}</div>
      `;
    } catch (err) {
      console.error(err);
      feedbackBox.textContent = "Error getting feedback.";
    }
  });
}
