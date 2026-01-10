document.addEventListener("DOMContentLoaded", () => {
  /* =========================
     Flip Cards
  ========================== */
  // Flip effect is handled by CSS hover, but allow click-to-flip too:
  document.querySelectorAll(".card").forEach(card => {
    card.addEventListener("click", () => {
      card.classList.toggle("flipped");
    });
  });

  /* =========================
     Section Switching
  ========================== */
  const state = { fill: 0, syn: 0, ant: 0 };

  document.querySelectorAll("[data-section-btn]").forEach(btn => {
    btn.addEventListener("click", () => {
      openSection(btn.dataset.sectionBtn);
    });
  });

  function openSection(sectionId) {
    document.querySelectorAll(".practice-section").forEach(sec => {
      sec.classList.add("hidden");
    });
    const section = document.getElementById(sectionId);
    section.classList.remove("hidden");
    state[sectionId] = 0;
    showQuestion(sectionId);
  }

  function showQuestion(sectionId) {
    const questions = document
      .getElementById(sectionId)
      .querySelectorAll(".question");

    questions.forEach((q, i) => {
      q.style.display = i === state[sectionId] ? "block" : "none";
    });
  }

  /* =========================
     Answer Checking
  ========================== */
  document.body.addEventListener("change", e => {
    if (!e.target.matches("input[type=radio]")) return;

    const question = e.target.closest(".question");
    const correct = question.dataset.answer;
    const feedback = question.querySelector(".feedback");
    const resetBtn = question.querySelector(".reset-btn");
    const nextBtn = question.querySelector(".next-btn");

    if (e.target.value === correct) {
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
     Reset Question
  ========================== */
  document.body.addEventListener("click", e => {
    if (!e.target.classList.contains("reset-btn")) return;

    const question = e.target.closest(".question");
    const form = question.querySelector(".options");

    shuffle([...form.children]).forEach(el => form.appendChild(el));
    form.querySelectorAll("input").forEach(r => (r.checked = false));

    const feedback = question.querySelector(".feedback");
    feedback.textContent = "";
    feedback.className = "feedback";
  });

  /* =========================
     Next Question
  ========================== */
  document.body.addEventListener("click", e => {
    if (!e.target.classList.contains("next-btn")) return;

    const section = e.target.closest(".practice-section");
    const id = section.id;
    const questions = section.querySelectorAll(".question");

    // Debug log (optional)
    // console.log("Section:", id, "Current index:", state[id], "Total:", questions.length);

    if (state[id] < questions.length - 1) {
      state[id]++;              // move to next index
      showQuestion(id);         // show that question
    } else {
      // Only show "completed" after the last question has been displayed
      section.innerHTML = "<p class='mastered'>🎉 Section completed.</p>";
    }
  });

  /* =========================
     Utility
  ========================== */
  function shuffle(arr) {
    return arr.sort(() => Math.random() - 0.5);
  }
});