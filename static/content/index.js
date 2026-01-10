document.addEventListener("DOMContentLoaded", () => {
  loadTextbooks();
});

async function loadTextbooks() {
  const statusEl = document.getElementById("textbooks-status");
  const listEl = document.getElementById("textbooks-list");

  statusEl.textContent = "Loading textbooks…";
  listEl.innerHTML = "";

  try {
    const response = await fetch("/api/content/textbooks/");
    if (!response.ok) {
      throw new Error("Failed to load textbooks");
    }

    const data = await response.json();
    const textbooks = data.results || data;

    if (!textbooks.length) {
      statusEl.textContent = "No textbooks found.";
      return;
    }

    statusEl.textContent = "";

    textbooks.forEach(tb => {
      const li = document.createElement("li");
      li.className = "textbook-item";

      li.innerHTML = `
        <article class="textbook-card">
          <header class="textbook-header">
            <a href="/content/textbooks/${tb.id}/" class="textbook-title">
              ${tb.title}
            </a>
            <span class="textbook-level">${tb.class_level}</span>
          </header>

          ${tb.description ? `<p class="textbook-description">${tb.description}</p>` : ""}

          ${renderUnits(tb.units)}
        </article>
      `;

      listEl.appendChild(li);
    });

  } catch (error) {
    console.error(error);
    statusEl.innerHTML = `
      Error loading textbooks.
      <button class="retry-btn">Retry</button>
    `;

    const retryBtn = statusEl.querySelector(".retry-btn");
    retryBtn.addEventListener("click", loadTextbooks);
  }
}

function renderUnits(units = []) {
  if (!units.length) {
    return `<div class="empty-note">No units available.</div>`;
  }

  return `
    <details class="units-block">
      <summary>${units.length} units</summary>
      <ul>
        ${units.map(unit => `
          <li>
            <a href="/content/units/${unit.id}/">
              Unit ${unit.number}: ${unit.title}
            </a>

            ${renderLessons(unit.lessons)}
          </li>
        `).join("")}
      </ul>
    </details>
  `;
}

function renderLessons(lessons = []) {
  if (!lessons || !lessons.length) return "";

  return `
    <details class="lessons-block">
      <summary>${lessons.length} lessons</summary>
      <ul>
        ${lessons.map(lesson => `
          <li>
            <a href="/content/lessons/${lesson.id}/">
              Lesson ${lesson.number}: ${lesson.title}
            </a>

            <div class="lesson-meta">
              ${lesson.chunks?.length ? `<span>Chunks: ${lesson.chunks.length}</span>` : ""}
              ${lesson.vocab_items?.length ? `<span>Vocab: ${lesson.vocab_items.length}</span>` : ""}
              ${lesson.grammar_points?.length ? `<span>Grammar: ${lesson.grammar_points.length}</span>` : ""}
              ${lesson.comprehension_questions?.length ? `<span>Questions: ${lesson.comprehension_questions.length}</span>` : ""}
              ${lesson.writing_tasks?.length ? `<span>Writing: ${lesson.writing_tasks.length}</span>` : ""}
            </div>
          </li>
        `).join("")}
      </ul>
    </details>
  `;
}
