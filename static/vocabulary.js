// vocabulary.js

// ----------- GLOBAL VARIABLES -----------
let vocabulary = [];
let currentIndex = 0;
let selectedVoice = null;

// Detect lesson_id from URL
// URL pattern expected: /vocabulary/<lesson_id>/
function getLessonIdFromURL() {
  const parts = window.location.pathname.split("/").filter(Boolean);
  const vocabIndex = parts.indexOf("vocabulary");
  if (vocabIndex !== -1 && parts[vocabIndex + 1]) {
    return parts[vocabIndex + 1];
  }
  return null;
}

const lessonId = getLessonIdFromURL();

// ----------- FETCH VOCABULARY FROM BACKEND -----------
async function loadVocabulary() {
  if (!lessonId) {
    alert("Lesson ID missing in URL.");
    return;
  }

  try {
    const response = await fetch(`/api/lessons/${lessonId}/vocab/`);

    if (!response.ok) {
      throw new Error("Failed to load vocabulary");
    }

    vocabulary = await response.json();

    if (!Array.isArray(vocabulary) || vocabulary.length === 0) {
      document.getElementById("word").textContent = "No vocabulary found.";
      return;
    }

    showCard(currentIndex);
  } catch (error) {
    console.error("Error loading vocabulary:", error);
  }
}

// ----------- DISPLAY CARD -----------
function showCard(index) {
  const item = vocabulary[index];

  document.getElementById("word").textContent = item.word || "N/A";
  document.getElementById("urdu").textContent = "Urdu: " + (item.urdu || "N/A");
  document.getElementById("meaning").textContent =
    "Meaning: " + (item.meaning || "N/A");
  document.getElementById("synonyms").textContent =
    "Synonyms: " + (item.synonyms || "N/A");
  document.getElementById("antonyms").textContent =
    "Antonyms: " + (item.antonyms || "N/A");
  document.getElementById("example").textContent =
    "Example: " + (item.example || "N/A");
}

// ----------- BUTTON CONTROLS -----------
document.getElementById("prevBtn").addEventListener("click", () => {
  if (currentIndex > 0) {
    currentIndex--;
    showCard(currentIndex);
  }
});

document.getElementById("nextBtn").addEventListener("click", () => {
  if (currentIndex < vocabulary.length - 1) {
    currentIndex++;
    showCard(currentIndex);
  }
});

// ----------- TEXT-TO-SPEECH -----------
function loadVoices() {
  const voices = speechSynthesis.getVoices();
  const voiceSelect = document.getElementById("voiceSelect");

  voiceSelect.innerHTML = ""; // clear

  voices.forEach((voice) => {
    const option = document.createElement("option");
    option.value = voice.name;
    option.textContent = `${voice.name} (${voice.lang})`;

    // Select English voice by default
    if (voice.lang.startsWith("en") && !selectedVoice) {
      selectedVoice = voice;
      option.selected = true;
    }

    voiceSelect.appendChild(option);
  });

  // Save selected voice
  voiceSelect.addEventListener("change", () => {
    selectedVoice = voices.find((v) => v.name === voiceSelect.value);
  });
}

speechSynthesis.onvoiceschanged = loadVoices;

// Speak Button
document.getElementById("speakBtn").addEventListener("click", () => {
  if (!vocabulary.length) return;

  const item = vocabulary[currentIndex];
  const utterance = new SpeechSynthesisUtterance(
    `${item.word}. Meaning: ${item.meaning}. Example: ${item.example}`
  );

  if (selectedVoice) {
    utterance.voice = selectedVoice;
  }

  speechSynthesis.speak(utterance);
});

// ----------- INIT -----------
window.onload = () => {
  loadVoices();
  loadVocabulary();
};
