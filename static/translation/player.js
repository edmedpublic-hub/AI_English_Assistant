/*************************************************
 * Translation Module
 * English → Urdu
 * Human-teacher style playback (NO autoplay)
 *************************************************/

// -------------------- DOM --------------------
const englishContainer = document.getElementById("english-text");
const urduContainer = document.getElementById("urdu-text");

const btnPlay  = document.getElementById("btn-play");
const btnNext  = document.getElementById("btn-next");
const btnPause = document.getElementById("btn-pause");
const btnStop  = document.getElementById("btn-stop");

const progressBar = document.getElementById("progress-bar");
const statusMessage = document.getElementById("status-message");

// Defensive check
if (!englishContainer || !urduContainer || !btnPlay || !btnNext || !btnPause || !btnStop || !progressBar) {
  throw new Error("Player DOM elements missing. Check player.html.");
}

// -------------------- State --------------------
let englishSentences = [];
let urduSentences = [];
let currentIndex = 0;

let isPaused = false;
let isStopped = true;     // lesson starts idle
let lessonLoaded = false;

// -------------------- Status UI --------------------
function showStatus(message, type = "info", autoClear = true) {
  if (!statusMessage) return;
  statusMessage.textContent = message;
  statusMessage.className = `status ${type}`;
  if (autoClear && type !== "error") setTimeout(clearStatus, 4000);
}
function clearStatus() {
  if (!statusMessage) return;
  statusMessage.textContent = "";
  statusMessage.className = "status";
}

// -------------------- Utilities --------------------
function splitIntoSentences(text) {
  if (!text) return [];
  return text.replace(/\s+/g, " ").trim()
    .split(/(?<=[.!?۔])\s+/)
    .map(s => s.trim())
    .filter(Boolean);
}
function renderSentences() {
  englishContainer.innerHTML = "";
  urduContainer.innerHTML = "";
  englishSentences.forEach((sentence, index) => {
    englishContainer.insertAdjacentHTML("beforeend", `<span id="eng-${index}">${sentence}</span>`);
  });
  urduSentences.forEach((sentence, index) => {
    urduContainer.insertAdjacentHTML("beforeend", `<span id="urd-${index}">${sentence}</span>`);
  });
}
function highlightSentence(index) {
  document.querySelectorAll(".sentence-list span").forEach(el => el.classList.remove("active"));
  if (index >= 0) {
    document.getElementById(`eng-${index}`)?.classList.add("active");
    document.getElementById(`urd-${index}`)?.classList.add("active");
  }
}
function updateProgress() {
  const total = englishSentences.length || 1;
  const percentage = Math.min((currentIndex / total) * 100, 100);
  progressBar.style.width = `${percentage}%`;
}
function speak(text, lang) {
  return new Promise(resolve => {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang;
    utterance.rate = 1;
    utterance.onend = resolve;
    speechSynthesis.speak(utterance);
  });
}
function waitWhilePaused() {
  return new Promise(resolve => {
    const timer = setInterval(() => {
      if (!isPaused) {
        clearInterval(timer);
        resolve();
      }
    }, 120);
  });
}

// -------------------- Button/State Control --------------------
function setButtonsIdle() {
  btnPlay.disabled = false;
  btnNext.disabled = true;
  btnPause.disabled = true;
  btnStop.disabled = true;
  btnPause.textContent = "⏸ Pause";
}
function setButtonsActive() {
  btnPlay.disabled = false;
  btnNext.disabled = false;
  btnPause.disabled = false;
  btnStop.disabled = false;
}
function setButtonsStopped() {
  btnPlay.disabled = false;
  btnNext.disabled = true;
  btnPause.disabled = true;
  btnStop.disabled = true;
  btnPause.textContent = "⏸ Pause";
}

// -------------------- Playback --------------------
async function playCurrentSentence() {
  if (isStopped) return;
  if (currentIndex >= englishSentences.length) {
    showStatus("Lesson complete.", "success", false);
    highlightSentence(-1);
    progressBar.style.width = "100%";
    setButtonsStopped();
    return;
  }
  highlightSentence(currentIndex);
  updateProgress();
  if (isPaused) await waitWhilePaused();
  await speak(englishSentences[currentIndex], "en-US");
  if (isStopped) return;
  await new Promise(r => setTimeout(r, 600));
  if (isPaused) await waitWhilePaused();
  await speak(urduSentences[currentIndex], "ur-PK");
  showStatus("Sentence played.");
}

// -------------------- Backend Integration --------------------
async function loadLessonFromAPI() {
  if (lessonLoaded) return;
  const lessonId = window.LESSON_ID;
  if (!lessonId || ["None", "null", "undefined"].includes(lessonId)) {
    showStatus("Lesson ID is missing or invalid.", "error", false);
    throw new Error("Invalid LESSON_ID");
  }
  showStatus("Loading lesson…", "info", false);
  const response = await fetch(`/api/translation/lessons/${lessonId}/`);
  if (!response.ok) {
    showStatus("Failed to load lesson.", "error", false);
    throw new Error(`API error ${response.status}`);
  }
  const data = await response.json();
  englishSentences = splitIntoSentences(data.english_chunk);
  urduSentences = splitIntoSentences(data.urdu_chunk);
  currentIndex = 0;
  renderSentences();
  lessonLoaded = true;
  showStatus("Lesson ready.", "success");
  setButtonsIdle();
}

// -------------------- Controls --------------------
btnPlay.addEventListener("click", async () => {
  await loadLessonFromAPI();
  isStopped = false;
  isPaused = false;
  setButtonsActive();
  speechSynthesis.cancel();
  await playCurrentSentence();
});

btnNext.addEventListener("click", async () => {
  if (currentIndex < englishSentences.length - 1) {
    currentIndex++;
    speechSynthesis.cancel();
    await playCurrentSentence();
  } else {
    currentIndex++;
    await playCurrentSentence(); // triggers completion
  }
});

btnPause.addEventListener("click", () => {
  if (isStopped) return;
  if (!isPaused) {
    isPaused = true;
    speechSynthesis.pause();
    btnPause.textContent = "▶ Resume";
    showStatus("Paused.", "warn");
  } else {
    isPaused = false;
    speechSynthesis.resume();
    btnPause.textContent = "⏸ Pause";
    showStatus("Resumed.", "info");
  }
});

btnStop.addEventListener("click", () => {
  isStopped = true;
  isPaused = false;
  currentIndex = 0;
  speechSynthesis.cancel();
  highlightSentence(-1);
  progressBar.style.width = "0%";
  setButtonsIdle();
  showStatus("Lesson stopped.", "warn");
});

// -------------------- Keyboard Shortcuts --------------------
document.addEventListener("keydown", (event) => {
  const tag = document.activeElement?.tagName?.toLowerCase();
  if (["input","textarea","select"].includes(tag) || document.activeElement?.isContentEditable) return;
  if (event.code === "Space") { event.preventDefault(); btnPlay.click(); }
  if (event.code === "ArrowRight") btnNext.click();
  if (event.key === "s" || event.key === "S") btnStop.click();
});

// Initialise UI
setButtonsIdle();