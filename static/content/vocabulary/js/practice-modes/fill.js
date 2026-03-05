// fill.js — Fill in the Blanks Practice
// Mastery Logic: Next button hidden until correct answer selected

document.addEventListener("DOMContentLoaded", () => {
  const wrapper = document.querySelector(".quiz-wrapper");
  const questions = Array.from(document.querySelectorAll(".question"));
  const prevBtn = document.getElementById("prevBtn");
  const nextBtn = document.getElementById("nextBtn");
  const scoreDisplay = document.getElementById("scoreDisplay");
  const progressFill = document.getElementById("progressFill");
  const completion = document.getElementById("completion");
  const questionsContainer = document.querySelector(".questions-container");

  if (!wrapper || questions.length === 0) return;

  const total = questions.length;
  let current = 0;
  let autoAdvanceTimeout = null;

  function normalize(text) {
    return (text || "").toLowerCase().trim();
  }

  function updateUI() {
    // Prev button: hidden on first question
    prevBtn.classList.toggle("d-none", current === 0);

    // Next button: only show if current question is mastered and not last
    const isMastered = questions[current].dataset.answered === "true";
    const isLast = current === total - 1;
    nextBtn.classList.toggle("d-none", !isMastered || isLast);

    // Score display
    const solvedCount = questions.filter(q => q.dataset.answered === "true").length;
    if (scoreDisplay) scoreDisplay.textContent = `Mastered: ${solvedCount} / ${total}`;

    // Progress bar
    if (progressFill) {
      const percent = Math.round((solvedCount / total) * 100);
      progressFill.style.width = `${percent}%`;
      progressFill.setAttribute("aria-valuenow", percent);
    }
  }

  function showQuestion(index) {
    if (autoAdvanceTimeout) clearTimeout(autoAdvanceTimeout);

    // Use d-none to show/hide questions
    questions.forEach((q, i) => {
      q.classList.toggle("d-none", i !== index);
    });

    current = index;
    updateUI();

    const radio = questions[current].querySelector('input[type="radio"]:not([disabled])');
    if (radio) radio.focus();
  }

  function handleNavigationFlow() {
    const solvedCount = questions.filter(q => q.dataset.answered === "true").length;

    if (solvedCount === total) {
      finishQuiz();
    } else if (current < total - 1) {
      showQuestion(current + 1);
    } else {
      // Loop back to first unanswered question
      const firstMissing = questions.findIndex(q => q.dataset.answered !== "true");
      if (firstMissing !== -1) showQuestion(firstMissing);
    }
  }

  function finishQuiz() {
    if (questionsContainer) questionsContainer.classList.add("d-none");
    document.querySelector(".nav-buttons")?.classList.add("d-none");
    if (completion) {
      completion.classList.remove("d-none");
      completion.focus();
    }
  }

  // Answer selection handler
  questionsContainer.addEventListener("change", (e) => {
    const input = e.target;
    if (input.tagName !== "INPUT" || input.type !== "radio") return;

    const question = input.closest(".question");
    const feedback = question.querySelector(".feedback");
    const correctValue = normalize(question.dataset.answer);
    const chosenValue = normalize(input.value);
    const radios = question.querySelectorAll('input[type="radio"]');

    radios.forEach(r => r.disabled = true);

    if (chosenValue === correctValue) {
      feedback.textContent = "✓ Correct!";
      feedback.className = "feedback text-success fw-semibold";
      question.dataset.answered = "true";
      updateUI();

      autoAdvanceTimeout = setTimeout(() => {
        handleNavigationFlow();
      }, 1200);
    } else {
      feedback.textContent = "✗ Try again!";
      feedback.className = "feedback text-danger fw-semibold";

      if (!question.querySelector(".retryBtn")) {
        const retryBtn = document.createElement("button");
        retryBtn.type = "button";
        retryBtn.className = "btn btn-sm btn-outline-secondary mt-2 retryBtn";
        retryBtn.textContent = "Retry Question";
        retryBtn.onclick = () => {
          radios.forEach(r => { r.disabled = false; r.checked = false; });
          feedback.textContent = "";
          feedback.className = "feedback";
          retryBtn.remove();
        };
        question.appendChild(retryBtn);
      }
    }
  });

  nextBtn.addEventListener("click", () => {
    if (current < total - 1) showQuestion(current + 1);
  });

  prevBtn.addEventListener("click", () => {
    if (current > 0) showQuestion(current - 1);
  });

  // Initialize
  showQuestion(0);
});