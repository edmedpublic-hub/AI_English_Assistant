// reading.recognition.js
export const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition;

export let recognition = null;

// use a single global accumulator on window so other modules (feedback) read the same value
window.transcriptAcc = window.transcriptAcc || "";

export function initRecognition() {
  if (!SpeechRecognition) {
    alert("Speech Recognition is not supported in this browser.");
    return;
  }

  recognition = new SpeechRecognition();
  recognition.lang = "en-US";
  recognition.interimResults = false;
  recognition.continuous = true;

  recognition.onresult = (e) => {
    const transcript = e.results[e.results.length - 1][0].transcript;
    // append safely
    window.transcriptAcc = (window.transcriptAcc || "") + " " + transcript;
    console.debug("Recognition result:", transcript);
  };

  recognition.onerror = (e) => {
    console.error("Recognition error:", e);
  };

  recognition.onend = () => {
    console.debug("Recognition ended");
    // leave recognition variable intact; caller decides whether to restart
  };
}
