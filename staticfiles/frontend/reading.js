// -------- DOM --------
document.addEventListener("DOMContentLoaded", () => {
  loadLesson();
});

const titleEl = document.getElementById("lessonTitle");
const textEl = document.getElementById("lessonText");
const voiceSelect = document.getElementById("voiceSelect");

const readBtn = document.getElementById("readBtn");
const pauseBtn = document.getElementById("pauseBtn");
const resumeBtn = document.getElementById("resumeBtn");
const stopBtn = document.getElementById("stopBtn");

const startRecordBtn = document.getElementById("startRecordBtn");
const stopRecordBtn = document.getElementById("stopRecordBtn");
const getFeedbackBtn = document.getElementById("getFeedbackBtn");
const feedbackBox = document.getElementById("feedbackBox");

// -------- state --------
let originalSentences = []; // canonical array of sentences
let displayedSentences = []; // copy for annotations
let currentIndex = 0;
let isReading = false;
let isPaused = false;
let voices = [];

const synth = window.speechSynthesis;
const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
let recording = false;
let transcriptAcc = "";

// -------- helpers --------
function cleanWord(w) {
  return (w || "").replace(/[^\w']/g, "").toLowerCase();
}

function levenshtein(a, b) {
  if (!a) return b.length;
  if (!b) return a.length;
  const m = a.length,
    n = b.length;
  const dp = Array.from({ length: n + 1 }, () => Array(m + 1).fill(0));
  for (let i = 0; i <= n; i++) dp[i][0] = i;
  for (let j = 0; j <= m; j++) dp[0][j] = j;
  for (let i = 1; i <= n; i++)
    for (let j = 1; j <= m; j++) {
      const cost = a[j - 1] === b[i - 1] ? 0 : 1;
      dp[i][j] = Math.min(
        dp[i - 1][j] + 1,
        dp[i][j - 1] + 1,
        dp[i - 1][j - 1] + cost
      );
    }
  return dp[n][m];
}

function soundex(word) {
  const w = cleanWord(word);
  if (!w) return "";
  const a = w.split("");
  const f = a.shift();
  const codes = {
    a: "",
    e: "",
    i: "",
    o: "",
    u: "",
    h: "",
    w: "",
    y: "",
    b: "1",
    f: "1",
    p: "1",
    v: "1",
    c: "2",
    g: "2",
    j: "2",
    k: "2",
    q: "2",
    s: "2",
    x: "2",
    z: "2",
    d: "3",
    t: "3",
    l: "4",
    m: "5",
    n: "5",
    r: "6",
  };
  let res = (f || "").toUpperCase();
  let prev = codes[f] || "";
  for (const ch of a) {
    const code = codes[ch] || "";
    if (code !== prev) res += code;
    prev = code;
  }
  return res.padEnd(4, "0").slice(0, 4);
}

// -------- voices --------
function populateVoices() {
  voices = synth.getVoices() || [];
  const prev = voiceSelect.value;
  voiceSelect.innerHTML = "";
  voices.forEach((v, i) => {
    const opt = document.createElement("option");
    opt.value = i;
    opt.textContent = `${v.name} (${v.lang})`;
    voiceSelect.appendChild(opt);
  });
  if (prev && voiceSelect.querySelector(`option[value="${prev}"]`))
    voiceSelect.value = prev;
}
synth.onvoiceschanged = populateVoices;
populateVoices();

// -------- load lesson json (array of paragraphs) --------
async function loadLesson() {
  try {
    const lessonId = document.body.dataset.lessonId || 1;

    const response = await fetch(
      `http://127.0.0.1:8000/api/reading/lessons/${lessonId}/`
    );
    const data = await response.json();

    // Set title and full text
    titleEl.innerText = data.title;
    textEl.innerText = data.content;

    // --- NEW: split into sentences ---
    originalSentences = data.content
      .split(/(?<=[.!?])\s+/) // split after punctuation
      .map((s) => s.trim())
      .filter((s) => s.length > 0);

    displayedSentences = originalSentences.slice();

    // Render without highlight yet
    renderHighlighted(-1);
  } catch (error) {
    console.error("Error loading lesson:", error);
  }
}

// -------- render highlighted --------
function renderHighlighted(index) {
  if (!displayedSentences || displayedSentences.length === 0) {
    textEl.innerHTML = "";
    return;
  }
  const html = displayedSentences
    .map((s, i) =>
      i === index ? `<span class="highlight">${s}</span>` : `<span>${s}</span>`
    )
    .join(" ");
  textEl.innerHTML = html;
}

// -------- TTS sentence-by-sentence --------
function speakSentence(i) {
  if (!originalSentences || i >= originalSentences.length) {
    isReading = false;
    currentIndex = 0;
    renderHighlighted(-1);
    return;
  }
  currentIndex = i;
  renderHighlighted(i);
  const text = originalSentences[i];
  const u = new SpeechSynthesisUtterance(text);
  const sel = parseInt(voiceSelect.value, 10) || 0;
  if (voices[sel]) u.voice = voices[sel];
  u.lang = "en-GB";
  u.rate = 1;
  u.pitch = 1;
  u.onend = () => {
    if (!isPaused && isReading) speakSentence(i + 1);
  };
  u.onerror = (e) => {
    console.error("TTS error", e);
    if (!isPaused && isReading) speakSentence(i + 1);
  };
  synth.speak(u);
}

// controls
readBtn.addEventListener("click", () => {
  if (!originalSentences || originalSentences.length === 0) return;
  synth.cancel();
  displayedSentences = originalSentences.slice();
  isReading = true;
  isPaused = false;
  currentIndex = 0;
  // small delay for cancel to take effect on some browsers
  setTimeout(() => speakSentence(0), 60);
});

pauseBtn.addEventListener("click", () => {
  if (synth.speaking && !synth.paused) {
    try {
      synth.pause();
      isPaused = true;
    } catch (e) {
      synth.cancel();
      isPaused = true;
    }
  }
});

resumeBtn.addEventListener("click", () => {
  if (isPaused) {
    try {
      synth.resume();
      isPaused = false;
    } catch (e) {
      isPaused = false;
      synth.cancel();
      setTimeout(() => speakSentence(currentIndex), 60);
    }
  }
});

stopBtn.addEventListener("click", () => {
  synth.cancel();
  isReading = false;
  isPaused = false;
  currentIndex = 0;
  displayedSentences = originalSentences.slice();
  renderHighlighted(-1);
});

// -------- SpeechRecognition setup --------
if (!SpeechRecognition) {
  feedbackBox.innerText =
    "SpeechRecognition not supported. Use Chrome or Edge.";
  startRecordBtn.disabled = true;
} else {
  recognition = new SpeechRecognition();
  recognition.lang = "en-GB";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onstart = () => {
    recording = true;
    transcriptAcc = "";
    startRecordBtn.disabled = true;
    stopRecordBtn.disabled = false;
    getFeedbackBtn.disabled = true;
    feedbackBox.innerText = "Recording... Read the highlighted sentence aloud.";
  };

  recognition.onresult = (ev) => {
    const part = ev.results[0][0].transcript || "";
    transcriptAcc += (transcriptAcc ? " " : "") + part;
  };

  recognition.onend = () => {
    recording = false;
    startRecordBtn.disabled = false;
    stopRecordBtn.disabled = true;
    getFeedbackBtn.disabled = false;
    feedbackBox.innerText =
      "Recording stopped. Click Get Feedback to evaluate.";
  };

  recognition.onerror = (e) => {
    recording = false;
    startRecordBtn.disabled = false;
    stopRecordBtn.disabled = true;
    getFeedbackBtn.disabled = false;
    feedbackBox.innerText = "Recognition error: " + (e.error || e.message);
    console.warn("recognition error", e);
  };
}

// student controls wiring
startRecordBtn.addEventListener("click", () => {
  if (!originalSentences || originalSentences.length === 0) {
    feedbackBox.innerText = "No lesson loaded.";
    return;
  }
  // ensure a sentence is highlighted
  renderHighlighted(currentIndex);
  transcriptAcc = "";
  try {
    recognition.start();
  } catch (e) {
    try {
      recognition.stop();
    } catch (_) {}
    recognition.start();
  }
});

stopRecordBtn.addEventListener("click", () => {
  if (recognition && recording) {
    try {
      recognition.stop();
    } catch (e) {
      console.warn(e);
    }
  }
});

getFeedbackBtn.addEventListener("click", () => {
  if (recognition && recording) {
    try {
      recognition.stop();
    } catch (e) {
      console.warn(e);
    }
  }
  const captured = (transcriptAcc || "").trim();
  if (!captured) {
    feedbackBox.innerText =
      "No speech captured. Use Student Start and read again.";
    return;
  }
  provideFeedbackForSentence(currentIndex, captured);
});

// feedback logic
function provideFeedbackForSentence(index, studentText) {
  const correct = originalSentences[index] || "";
  const correctWords = correct.split(/\s+/).map(cleanWord).filter(Boolean);
  const studentWords = studentText.split(/\s+/).map(cleanWord).filter(Boolean);

  let correctCount = 0;
  const annotated = correctWords.map((cw, i) => {
    const sw = studentWords[i] || "";
    if (cw === sw && cw !== "") {
      correctCount++;
      return cw;
    }
    if (soundex(cw) && soundex(cw) === soundex(sw) && cw !== "") {
      correctCount++;
      return cw;
    }
    const dist = levenshtein(cw, sw);
    const maxLen = Math.max(cw.length, sw.length, 1);
    const similarity = 1 - dist / maxLen;
    if (similarity >= 0.6) {
      correctCount++;
      return cw;
    }
    return `<span class="mispronounced">${cw}</span>`;
  });

  const accuracy = correctWords.length
    ? ((correctCount / correctWords.length) * 100).toFixed(2)
    : "0.00";
  displayedSentences[index] = annotated.join(" ");
  renderHighlighted(index);
  feedbackBox.innerHTML = `Accuracy: ${accuracy}%\nCaptured: "${studentText}"`;
}

// initial load
loadLesson();
