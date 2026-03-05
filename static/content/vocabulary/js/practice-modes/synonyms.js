// synonyms.js — Synonyms Practice

document.addEventListener("DOMContentLoaded", () => {
  const container = document.querySelector(".questions-container");
  const questions = Array.from(document.querySelectorAll(".question"));
  const nextBtn = document.getElementById("nextBtn");
  const prevBtn = document.getElementById("prevBtn");
  const completion = document.getElementById("completion");

  if (!container || questions.length === 0) return;

  let current = 0;

  const normalize = (val) => val.toString().toLowerCase().trim();

  function updateUI() {
    const activeQ = questions[current];
    const isMastered = activeQ.getAttribute("data-answered") === "true";

    if (prevBtn) prevBtn.classList.toggle("d-none", current === 0);

    if (nextBtn) {
      const isLast = current === questions.length - 1;
      nextBtn.classList.toggle("d-none", !isMastered || isLast);
    }

    const solved = questions.filter(q => q.getAttribute("data-answered") === "true").length;
    const scoreDisp = document.getElementById("scoreDisplay");
    if (scoreDisp) scoreDisp.textContent = `Mastered: ${solved} / ${questions.length}`;

    const progBar = document.getElementById("progressFill");
    if (progBar) {
      progBar.style.width = `${(solved / questions.length) * 100}%`;
      progBar.setAttribute("aria-valuenow", Math.round((solved / questions.length) * 100));
    }
  }

  function showQuestion(index) {
    questions.forEach((q, i) => q.classList.toggle("d-none", i !== index));
    current = index;
    updateUI();
  }

  container.addEventListener("change", (e) => {
    if (e.target.type !== "radio") return;

    const qCard = e.target.closest(".question");
    const feedback = qCard.querySelector(".feedback");
    const radios = qCard.querySelectorAll('input[type="radio"]');
    const correct = normalize(qCard.getAttribute("data-answer"));
    const selected = normalize(e.target.value);

    radios.forEach(r => r.disabled = true);

    if (selected === correct) {
      feedback.textContent = "✓ Correct!";
      feedback.className = "feedback text-success fw-semibold";
      qCard.setAttribute("data-answered", "true");
      updateUI();

      setTimeout(() => {
        if (current < questions.length - 1) {
          showQuestion(current + 1);
        } else {
          const allDone = questions.every(q => q.getAttribute("data-answered") === "true");
          if (allDone) {
            container.classList.add("d-none");
            document.querySelector(".nav-buttons")?.classList.add("d-none");
            if (completion) completion.classList.remove("d-none");
          }
        }
      }, 1000);
    } else {
      feedback.textContent = "✗ Try again!";
      feedback.className = "feedback text-danger fw-semibold";

      if (!qCard.querySelector(".retry-action")) {
        const btn = document.createElement("button");
        btn.className = "btn btn-sm btn-outline-secondary mt-2 retry-action";
        btn.textContent = "Retry";
        btn.onclick = () => {
          radios.forEach(r => { r.disabled = false; r.checked = false; });
          feedback.textContent = "";
          btn.remove();
        };
        qCard.appendChild(btn);
      }
    }
  });

  if (nextBtn) nextBtn.onclick = () => current < questions.length - 1 && showQuestion(current + 1);
  if (prevBtn) prevBtn.onclick = () => current > 0 && showQuestion(current - 1);

  showQuestion(0);
});