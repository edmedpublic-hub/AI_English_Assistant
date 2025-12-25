(() => {
  const BASE_URL = "http://127.0.0.1:8000";
  const params = new URLSearchParams(location.search);
  const lessonId = params.get("lesson") || "";

  const backBtn = document.getElementById("backBtn");
  const runBtn = document.getElementById("runBtn");
  const statusEl = document.getElementById("status");
  const resultsEl = document.getElementById("results");
  const lessonIdEl = document.getElementById("lessonId");

  // ------------------------------
  // INITIAL SETUP
  // ------------------------------
  lessonIdEl.textContent = lessonId || "-";

  if (!lessonId) {
    showStatus(
      "No lesson specified. Please open this page from the lesson selector.",
      true
    );
    runBtn.disabled = true;
  }

  backBtn.addEventListener("click", () => {
    window.location.href = "lesson_selector.html";
  });

  // ------------------------------
  // STATUS HELPERS
  // ------------------------------
  function showStatus(text, isError = false) {
    statusEl.classList.remove("hidden");
    statusEl.textContent = text;
    statusEl.style.background = isError ? "#ffe6e6" : "#e8f0ff";
  }

  function clearStatus() {
    statusEl.classList.add("hidden");
    statusEl.textContent = "";
  }

  // ------------------------------
  // CARD BUILDER
  // ------------------------------
  function createCard(point, idx) {
    const card = document.createElement("div");
    card.className = "card";

    const head = document.createElement("div");
    head.className = "card-head";

    const title = document.createElement("div");
    title.className = "card-title";
    title.textContent = `${idx + 1}. ${point.title}`;

    const toggle = document.createElement("button");
    toggle.className = "card-toggle";
    toggle.innerHTML = "▾";

    head.appendChild(title);
    head.appendChild(toggle);
    card.appendChild(head);

    const body = document.createElement("div");
    body.className = "card-body";

    const expl = document.createElement("p");
    expl.textContent = point.explanation || "";

    const example = document.createElement("div");
    example.className = "example";
    example.innerHTML = `<strong>Example:</strong> ${point.example || ""}`;

    body.appendChild(expl);
    body.appendChild(example);

    card.appendChild(body);

    toggle.addEventListener("click", () => {
      body.classList.toggle("open");
      toggle.innerHTML = body.classList.contains("open") ? "▴" : "▾";
    });

    return card;
  }

  // ------------------------------
  // FETCH GRAMMAR FROM BACKEND
  // ------------------------------
  async function fetchGrammar() {
    if (!lessonId) return;

    showStatus("Extracting grammar... Please wait.");

    try {
      const res = await fetch(
        `${BASE_URL}/api/lessons/${lessonId}/extract-grammar/`,
        {
          method: "POST",
        }
      );

      if (!res.ok) {
        showStatus(`Server error: ${res.status}`, true);
        return;
      }

      const data = await res.json();
      clearStatus();

      if (!data || !data.grammar_points) {
        showStatus("No grammar points returned.", true);
        return;
      }

      resultsEl.innerHTML = ""; // Clear previous results

      data.grammar_points.forEach((p, i) => {
        const card = createCard(p, i);
        resultsEl.appendChild(card);
      });

      showStatus("Grammar extracted successfully!");
    } catch (error) {
      showStatus("Network error. Backend not reachable.", true);
      console.error(error);
    }
  }

  // Run extraction
  runBtn.addEventListener("click", fetchGrammar);
})();
