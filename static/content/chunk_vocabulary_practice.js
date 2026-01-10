document.addEventListener("DOMContentLoaded", () => {
  /* =========================
      Flip Cards
  ========================== */
  document.querySelectorAll(".card").forEach(card => {
    card.addEventListener("click", () => card.classList.toggle("flipped"));
  });

  /* =========================
      Section Switching
  ========================== */
  const state = { fill: 0, syn: 0, ant: 0 };

  document.querySelectorAll("[data-section-btn]").forEach(btn => {
    btn.addEventListener("click", () => {
      const sectionId = btn.dataset.sectionBtn;
      document.querySelectorAll(".practice-section").forEach(sec => sec.classList.add("hidden"));
      
      const section = document.getElementById(sectionId);
      section.classList.remove("hidden");
      state[sectionId] = 0; // Start at first question
      showQuestion(sectionId);
    });
  });

  function showQuestion(sectionId) {
    const section = document.getElementById(sectionId);
    const questions = section.querySelectorAll(".question");

    questions.forEach((q, i) => {
      q.style.display = (i === state[sectionId]) ? "block" : "none";
      // Clear previous inputs/feedback for this specific question
      if (i === state[sectionId]) {
        q.querySelector(".next-btn").classList.add("hidden");
        q.querySelector(".feedback").textContent = "";
        q.querySelectorAll("input").forEach(r => r.checked = false);
      }
    });
  }

  /* =========================
      Answer Checking
  ========================== */
  document.body.addEventListener("change", e => {
    if (!e.target.matches("input[type=radio]")) return;

    const question = e.target.closest(".question");
    const correct = question.dataset.answer.trim().toLowerCase();
    const feedback = question.querySelector(".feedback");
    const nextBtn = question.querySelector(".next-btn");
    const resetBtn = question.querySelector(".reset-btn");

    if (e.target.value.trim().toLowerCase() === correct) {
      feedback.textContent = "✅ Correct!";
      feedback.className = "feedback correct";
      nextBtn.classList.remove("hidden");
      resetBtn.classList.add("hidden");
    } else {
      feedback.textContent = "❌ Wrong, try again.";
      feedback.className = "feedback wrong";
      resetBtn.classList.remove("hidden");
      nextBtn.classList.add("hidden");
    }
  });

  /* =========================
      Next & Reset Buttons
  ========================== */
  document.body.addEventListener("click", e => {
    if (e.target.classList.contains("reset-btn")) {
      const question = e.target.closest(".question");
      question.querySelectorAll("input").forEach(r => r.checked = false);
      question.querySelector(".feedback").textContent = "";
      e.target.classList.add("hidden");
    }

    if (e.target.classList.contains("next-btn")) {
      const section = e.target.closest(".practice-section");
      const id = section.id;
      const questions = section.querySelectorAll(".question");

      if (state[id] < questions.length - 1) {
        state[id]++;
        showQuestion(id);
      } else {
        // Only happens AFTER the last question's Next button is clicked
        section.innerHTML = "<div class='mastery-box'><p class='mastered'>🎉 Section completed. You've mastered this set!</p><button onclick='location.reload()'>Practice Again</button></div>";
      }
    }
  });
});