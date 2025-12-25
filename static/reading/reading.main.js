import { populateVoices, initTextReader, synth } from "./reading.text.js";
import { initListening } from "./reading.listen.js";
import { initFeedback } from "./reading.feedback.js";

// DOM
const titleEl = document.getElementById("lessonTitle");
const textEl = document.getElementById("lessonText");
const listContainer = document.getElementById("lesson-list");

// ---------------- LOAD LESSON ----------------
async function loadLesson(id = 1) {
  try {
    const res = await fetch(`/api/reading/lessons/${id}/`);
    if (!res.ok) throw new Error("Lesson not found");

    const lesson = await res.json();

    titleEl.textContent = lesson.title;

    const raw = lesson.content || "";
    const paragraphs = raw
      .split("\n")
      .filter((p) => p.trim() !== "")
      .map((p) => `<p>${p}</p>`)
      .join("");

    textEl.innerHTML = paragraphs;

    // Store for feedback/listening
    window.originalSentences = raw
      .replace(/\n+/g, " ")
      .split(/(?<=[.!?])\s+/)
      .filter((s) => s.trim() !== "");

    window.displayedSentences = [...window.originalSentences];
    window.lessonText = raw;
  } catch (err) {
    console.error("Error loading lesson:", err);
  }
}

// ---------------- LOAD LESSON LIST ----------------
async function loadLessonList() {
  if (!listContainer) return;

  try {
    const res = await fetch("/api/reading/lessons/");
    if (!res.ok) throw new Error("Could not load lessons");

    const lessons = await res.json();

    if (!Array.isArray(lessons) || lessons.length === 0) {
      listContainer.textContent = "No lessons available yet.";
      return;
    }

    listContainer.innerHTML = "";

    lessons.forEach((lesson) => {
      const link = document.createElement("a");
      link.href = `/reading/${lesson.id}/`;
      link.textContent = lesson.title || `Lesson ${lesson.id}`;
      listContainer.appendChild(link);
      listContainer.appendChild(document.createElement("br"));
    });
  } catch {
    listContainer.textContent = "Could not load lessons.";
  }
}

// ---------------- INIT APP ----------------
document.addEventListener("DOMContentLoaded", () => {
  // Load list on reading.html
  loadLessonList();

  // Load individual lesson on reading_detail.html
  const pageLessonId = document.body.getAttribute("data-lesson-id");
  if (pageLessonId) {
    loadLesson(pageLessonId);
  }

  // Speech synthesis voices
  populateVoices();
  synth.onvoiceschanged = populateVoices;

  // Initialize modules
  initTextReader();
  initListening();
  initFeedback();
});
