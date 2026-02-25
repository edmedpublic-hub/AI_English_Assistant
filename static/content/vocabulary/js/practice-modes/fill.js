// content/chunk_vocab_fill.js
// Mastery Logic: "Next" button remains hidden until the correct answer is mastered.

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
    // Previous is always available except on Q1
    prevBtn.classList.toggle("hidden", current === 0);

    // CRITICAL CHANGE: Next button is HIDDEN by default 
    // It only shows if the current question is already mastered
    const isMastered = questions[current].dataset.answered === "true";
    const isLast = current === total - 1;
    
    // Show Next only if mastered AND not the last question
    nextBtn.classList.toggle("hidden", !isMastered || isLast);

    const solvedCount = questions.filter(q => q.dataset.answered === "true").length;
    if (scoreDisplay) scoreDisplay.textContent = `Mastered: ${solvedCount} / ${total}`;
    
    if (progressFill) {
      const percent = Math.round((solvedCount / total) * 100);
      progressFill.style.width = `${percent}%`;
    }
  }

  function showQuestion(index) {
    if (autoAdvanceTimeout) clearTimeout(autoAdvanceTimeout);
    
    questions.forEach((q, i) => {
      q.classList.toggle("hidden", i !== index);
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
      // If they are on the last one but missed earlier ones, loop back
      const firstMissing = questions.findIndex(q => q.dataset.answered !== "true");
      if (firstMissing !== -1) showQuestion(firstMissing);
    }
  }

  function finishQuiz() {
    if (questionsContainer) questionsContainer.classList.add("hidden");
    document.querySelector(".nav-buttons")?.classList.add("hidden");
    if (completion) {
      completion.classList.remove("hidden");
      completion.focus();
    }
  }

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
      feedback.textContent = "Correct!";
      feedback.className = "feedback correct";
      question.dataset.answered = "true";
      
      // Reveal the Next button immediately upon correct answer
      updateUI(); 

      autoAdvanceTimeout = setTimeout(() => {
        handleNavigationFlow();
      }, 1200);
    } else {
      feedback.textContent = "Try again!";
      feedback.className = "feedback wrong";
      
      if (!question.querySelector(".retryBtn")) {
        const retryBtn = document.createElement("button");
        retryBtn.type = "button";
        retryBtn.className = "retryBtn";
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

  showQuestion(0);
});