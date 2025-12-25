// comprehension_practice.js
const qTextEl = document.getElementById("questionText");
const optionsList = document.getElementById("optionsList");
const feedbackEl = document.getElementById("feedback");
const qMetaEl = document.getElementById("qMeta");
const nextBtn = document.getElementById("nextBtn");
const skipBtn = document.getElementById("skipBtn");
const backBtn = document.getElementById("backBtn");

let questionsPool = [];
let currentIndex = -1;

// Load questions JSON
async function loadQuestions() {
  try {
    const res = await fetch("data/lesson1_practice_questions.json");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    questionsPool = await res.json();
    if (!Array.isArray(questionsPool) || questionsPool.length === 0) {
      qTextEl.textContent = "No practice questions available.";
      return;
    }
    showRandomQuestion();
  } catch (err) {
    qTextEl.textContent = "Failed to load practice questions.";
    console.error(err);
  }
}

// Show question by index
function showQuestion(i) {
  const q = questionsPool[i];
  currentIndex = i;
  qMetaEl.textContent = `Type: ${q.level || "general"} • Bloom: ${
    q.bloom || "N/A"
  }`;
  qTextEl.textContent = q.question;
  feedbackEl.textContent = "";
  optionsList.innerHTML = "";

  q.options.forEach((opt, idx) => {
    const li = document.createElement("li");
    li.innerHTML = `
      <label>
        <input name="opt" type="radio" value="${idx}" />
        ${opt}
      </label>
    `;
    optionsList.appendChild(li);
  });

  // attach click handler for options
  optionsList
    .querySelectorAll("input[name='opt']")
    .forEach((input) =>
      input.addEventListener("change", () =>
        handleAnswer(parseInt(input.value, 10))
      )
    );
}

// random pick (but avoid immediate repeat)
let lastIndex = -1;
function showRandomQuestion() {
  if (questionsPool.length === 0) return;
  if (questionsPool.length === 1) return showQuestion(0);
  let idx;
  do {
    idx = Math.floor(Math.random() * questionsPool.length);
  } while (idx === lastIndex);
  lastIndex = idx;
  showQuestion(idx);
}

// handle answer: immediate feedback, no scoring
function handleAnswer(selectedIdx) {
  const q = questionsPool[currentIndex];
  const correctIdx = q.answer;
  if (selectedIdx === correctIdx) {
    feedbackEl.style.color = "green";
    feedbackEl.textContent = "✅ Correct — " + (q.explanation || "Well done.");
  } else {
    feedbackEl.style.color = "crimson";
    feedbackEl.textContent =
      "❌ Not correct. " +
      (q.explanation || "Review the passage and try again.");
  }
}

// next and skip behavior
nextBtn.addEventListener("click", () => showRandomQuestion());
skipBtn.addEventListener("click", () => showRandomQuestion());
backBtn.addEventListener("click", () => {
  window.location.href = "index.html";
});

loadQuestions();
