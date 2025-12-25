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

// Defensive check (prevents silent failures)
if (!englishContainer || !urduContainer || !btnPlay || !btnNext || !btnPause || !btnStop) {
  throw new Error("Player DOM elements missing. Check player.html.");
}

// -------------------- State --------------------
let englishSentences = [];
let urduSentences = [];
let currentIndex = 0;
let isPaused = false;
let isStopped = false;
let lessonLoaded = false;

// -------------------- Utilities --------------------
function splitIntoSentences(text) {
  if (!text) return [];
  return text
    .replace(/\s+/g, " ")
    .trim()
    .split(/(?<=[.!?۔])\s+/)
    .map(s => s.trim())
    .filter(Boolean);
}

function renderSentences() {
  englishContainer.innerHTML = "";
  urduContainer.innerHTML = "";

  englishSentences.forEach((sentence, index) => {
    const span = document.createElement("span");
    span.textContent = sentence;
    span.id = `eng-${index}`;
    englishContainer.appendChild(span);
  });

  urduSentences.forEach((sentence, index) => {
    const span = document.createElement("span");
    span.textContent = sentence;
    span.id = `urd-${index}`;
    urduContainer.appendChild(span);
  });
}

function highlightSentence(index) {
  document
    .querySelectorAll(".sentence-list span")
    .forEach(el => el.classList.remove("active"));

  if (index < 0) return;

  document.getElementById(`eng-${index}`)?.classList.add("active");
  document.getElementById(`urd-${index}`)?.classList.add("active");
}

function updateProgress() {
  const total = englishSentences.length || 1;
  const percentage = (currentIndex / total) * 100;
  progressBar.style.width = `${percentage}%`;
}

// -------------------- Speech --------------------
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
    }, 100);
  });
}

// -------------------- Teacher Playback (CORE) --------------------
async function playCurrentSentence() {
  if (isStopped || currentIndex >= englishSentences.length) return;

  highlightSentence(currentIndex);
  updateProgress();

  if (isPaused) await waitWhilePaused();
  await speak(englishSentences[currentIndex], "en-US");

  if (isStopped) return;

  // Natural teacher pause
  await new Promise(r => setTimeout(r, 600));

  if (isPaused) await waitWhilePaused();
  await speak(urduSentences[currentIndex], "ur-PK");
}

// -------------------- Backend Integration --------------------
async function loadLessonFromAPI() {
  if (lessonLoaded) return;

  const lessonId = window.LESSON_ID;
  console.log("LESSON_ID:", lessonId);
  console.log("FETCH URL:", `/api/translation/lessons/${lessonId}/`);


  if (!lessonId || ["None", "null", "undefined"].includes(lessonId)) {
    alert("Lesson ID missing or invalid.");
    throw new Error("Invalid LESSON_ID");
  }

  const response = await fetch(`/api/translation/lessons/${lessonId}/`);
  if (!response.ok) {
    alert("Failed to load lesson.");
    throw new Error(`API error ${response.status}`);
  }

  const data = await response.json();

  englishSentences = splitIntoSentences(data.english_chunk);
  urduSentences = splitIntoSentences(data.urdu_chunk);

  if (englishSentences.length !== urduSentences.length) {
    console.warn("Sentence count mismatch", {
      english: englishSentences.length,
      urdu: urduSentences.length,
    });
  }

  renderSentences();
  lessonLoaded = true;
}

// -------------------- Controls --------------------
btnPlay.addEventListener("click", async () => {
  speechSynthesis.cancel();
  isStopped = false;
  isPaused = false;

  await loadLessonFromAPI();
  await playCurrentSentence();
});

btnNext.addEventListener("click", async () => {
  if (currentIndex < englishSentences.length - 1) {
    currentIndex++;
    speechSynthesis.cancel();
    await playCurrentSentence();
  } else {
    highlightSentence(-1);
    progressBar.style.width = "100%";
  }
});

btnPause.addEventListener("click", () => {
  if (!isStopped) {
    isPaused = true;
    speechSynthesis.pause();
  }
});

btnStop.addEventListener("click", () => {
  isStopped = true;
  isPaused = false;
  speechSynthesis.cancel();
  highlightSentence(-1);
  progressBar.style.width = "0%";
});
