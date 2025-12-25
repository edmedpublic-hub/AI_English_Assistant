const BASE_URL = "http://127.0.0.1:8000";

// DOM elements
const textbookSelect = document.getElementById("textbookSelect");
const unitSelect = document.getElementById("unitSelect");
const lessonSelect = document.getElementById("lessonSelect");
const goBtn = document.getElementById("goBtn");
const extractGrammarBtn = document.getElementById("extractGrammarBtn");
const grammarResults = document.getElementById("grammarResults");

// -------------------------
// LOAD TEXTBOOKS
// -------------------------
async function loadTextbooks() {
  try {
    const res = await fetch(`${BASE_URL}/api/textbooks/`);
    const data = await res.json();

    textbookSelect.innerHTML = `<option value="">Select textbook</option>`;

    data.forEach((book) => {
      textbookSelect.innerHTML += `<option value="${book.id}">${book.name}</option>`;
    });
  } catch (error) {
    console.error("❌ Error fetching textbooks:", error);
  }
}

loadTextbooks();

// -------------------------
// WHEN TEXTBOOK IS SELECTED
// -------------------------
textbookSelect.addEventListener("change", async () => {
  const bookId = textbookSelect.value;

  unitSelect.disabled = true;
  lessonSelect.disabled = true;
  goBtn.disabled = true;
  extractGrammarBtn.disabled = true;

  if (!bookId) return;

  try {
    const res = await fetch(`${BASE_URL}/api/textbooks/${bookId}/units/`);
    const data = await res.json();

    unitSelect.innerHTML = `<option value="">Select unit</option>`;
    lessonSelect.innerHTML = `<option value="">Select unit first</option>`;

    data.forEach((unit) => {
      unitSelect.innerHTML += `<option value="${unit.id}">${unit.title}</option>`;
    });

    unitSelect.disabled = false;
  } catch (error) {
    console.error("❌ Error loading units:", error);
  }
});

// -------------------------
// WHEN UNIT IS SELECTED
// -------------------------
unitSelect.addEventListener("change", async () => {
  const unitId = unitSelect.value;

  lessonSelect.disabled = true;
  goBtn.disabled = true;
  extractGrammarBtn.disabled = true;

  if (!unitId) return;

  try {
    const res = await fetch(`${BASE_URL}/api/units/${unitId}/lessons/`);
    const data = await res.json();

    lessonSelect.innerHTML = `<option value="">Select lesson</option>`;

    data.forEach((lesson) => {
      lessonSelect.innerHTML += `<option value="${lesson.id}">${lesson.title}</option>`;
    });

    lessonSelect.disabled = false;
  } catch (error) {
    console.error("❌ Error loading lessons:", error);
  }
});

// -------------------------
// WHEN LESSON IS SELECTED
// -------------------------
lessonSelect.addEventListener("change", () => {
  const selected = lessonSelect.value !== "";
  goBtn.disabled = !selected;
  extractGrammarBtn.disabled = !selected;
});

// -------------------------
// GO TO WRITING TASK
// -------------------------
goBtn.addEventListener("click", () => {
  const lessonId = lessonSelect.value;
  window.location.href = `sentence_writing.html?lesson=${lessonId}`;
});

// -------------------------
// 🔥 EXTRACT GRAMMAR BUTTON
// -------------------------
extractGrammarBtn.addEventListener("click", async () => {
  const lessonId = lessonSelect.value;

  grammarResults.innerHTML = `<p>⏳ Extracting grammar... Please wait.</p>`;

  try {
    const res = await fetch(
      `${BASE_URL}/api/lessons/${lessonId}/extract-grammar/`,
      { method: "POST" }
    );

    const data = await res.json();

    if (!data.grammar_points || data.grammar_points.length === 0) {
      grammarResults.innerHTML = `<p>No grammar points found.</p>`;
      return;
    }

    // Render grammar cards
    grammarResults.innerHTML = "";
    data.grammar_points.forEach((gp) => {
      grammarResults.innerHTML += `
        <div class="grammar-card">
          <h3>${gp.title}</h3>
          <p>${gp.explanation}</p>
          <div class="example-box">
            <strong>Example:</strong> ${gp.example}
          </div>
        </div>
      `;
    });
  } catch (error) {
    console.error("❌ Grammar extraction failed:", error);
    grammarResults.innerHTML = `<p>Error extracting grammar.</p>`;
  }
});
