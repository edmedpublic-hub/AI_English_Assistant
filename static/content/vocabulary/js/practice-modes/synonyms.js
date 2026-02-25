document.addEventListener("DOMContentLoaded", () => {
    // 1. Scope the search to the specific container to avoid Fill-in-Blank conflicts
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
        
        // Toggle Visibility
        if (prevBtn) prevBtn.classList.toggle("hidden", current === 0);
        
        // Mastery Gate: Next button only appears if question is solved
        if (nextBtn) {
            const isLast = (current === questions.length - 1);
            nextBtn.classList.toggle("hidden", !isMastered || isLast);
        }

        // Progress Tracking
        const solved = questions.filter(q => q.getAttribute("data-answered") === "true").length;
        const scoreDisp = document.getElementById("scoreDisplay");
        if (scoreDisp) scoreDisp.textContent = `Mastered: ${solved} / ${questions.length}`;
        
        const progBar = document.getElementById("progressFill");
        if (progBar) {
            progBar.style.width = `${(solved / questions.length) * 100}%`;
        }
    }

    function showQuestion(index) {
        questions.forEach((q, i) => q.classList.toggle("hidden", i !== index));
        current = index;
        updateUI();
    }

    // Handle User Input
    container.addEventListener("change", (e) => {
        if (e.target.type !== "radio") return;

        const qCard = e.target.closest(".question");
        const feedback = qCard.querySelector(".feedback");
        const radios = qCard.querySelectorAll('input[type="radio"]');
        
        const correct = normalize(qCard.getAttribute("data-answer"));
        const selected = normalize(e.target.value);

        // Lock radios to prevent spamming
        radios.forEach(r => r.disabled = true);

        if (selected === correct) {
            feedback.textContent = "Correct!";
            feedback.className = "feedback correct";
            qCard.setAttribute("data-answered", "true");
            
            updateUI(); // Reveal Next button

            // Auto-advance logic
            setTimeout(() => {
                if (current < questions.length - 1) {
                    showQuestion(current + 1);
                } else {
                    // Check if everything is truly mastered
                    const allDone = questions.every(q => q.getAttribute("data-answered") === "true");
                    if (allDone) {
                        container.classList.add("hidden");
                        if (completion) completion.classList.remove("hidden");
                        document.querySelector(".nav-buttons")?.classList.add("hidden");
                    }
                }
            }, 1000);
        } else {
            feedback.textContent = "Try again!";
            feedback.className = "feedback wrong";
            
            // Generate Retry Button dynamically
            if (!qCard.querySelector(".retry-action")) {
                const btn = document.createElement("button");
                btn.className = "retryBtn retry-action";
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