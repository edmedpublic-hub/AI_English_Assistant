document.addEventListener("DOMContentLoaded", () => {
  const questions = document.querySelectorAll(".question");
  let current = 0;
  let score = 0;

  const prevBtn = document.getElementById("prevBtn");
  const nextBtn = document.getElementById("nextBtn");

  const scoreDisplay = document.querySelector(".score-display");

  function updateScore() {
    scoreDisplay.textContent = `Score: ${score}/${questions.length}`;
  }

  function showQuestion(index) {
    questions.forEach(q => q.classList.add("hidden"));
    questions[index].classList.remove("hidden");

    prevBtn.disabled = index === 0;
    nextBtn.disabled = index === questions.length - 1;

    updateScore();
  }

  showQuestion(current);

  nextBtn.addEventListener("click", () => {
    if (current < questions.length - 1) {
      current++;
      showQuestion(current);
    }
  });

  prevBtn.addEventListener("click", () => {
    if (current > 0) {
      current--;
      showQuestion(current);
    }
  });

  document.querySelectorAll(".options input[type=radio]").forEach(input => {
    input.addEventListener("change", e => {
      const question = e.target.closest(".question");
      const correct = question.dataset.answer.trim().toLowerCase();
      const feedback = question.querySelector(".feedback");

      const chosen = e.target.value.trim().toLowerCase();

      if (chosen === correct) {
        feedback.textContent = "Correct";
        feedback.className = "feedback correct";

        if (!question.dataset.answered) {
          score++;
          question.dataset.answered = "true";
        }

        updateScore();

      } else {
        feedback.textContent = "Wrong";
        feedback.className = "feedback wrong";
      }
    });
  });
});
