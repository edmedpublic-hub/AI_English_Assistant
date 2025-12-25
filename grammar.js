const titleEl = document.getElementById("concept-title");
const definitionEl = document.getElementById("definition");
const exampleEl = document.getElementById("example");

const prevBtn = document.getElementById("prevBtn");
const nextBtn = document.getElementById("nextBtn");
const speakBtn = document.getElementById("speakBtn");
const voiceSelect = document.getElementById("voiceSelect");

let grammarData = [];
let currentIndex = 0;
let voices = [];

// Load grammar concepts
fetch("data/lesson1_grammar.json")
  .then((response) => response.json())
  .then((data) => {
    grammarData = data.concepts;
    displayConcept(currentIndex);
  })
  .catch((err) => console.error("Error loading grammar:", err));

// Display grammar concept
function displayConcept(index) {
  if (grammarData.length === 0) return;
  const concept = grammarData[index];
  titleEl.textContent = concept.title;
  definitionEl.textContent = concept.definition;
  exampleEl.textContent = "Example: " + concept.example;
}

// Navigation buttons
prevBtn.addEventListener("click", () => {
  if (currentIndex > 0) {
    currentIndex--;
    displayConcept(currentIndex);
  }
});

nextBtn.addEventListener("click", () => {
  if (currentIndex < grammarData.length - 1) {
    currentIndex++;
    displayConcept(currentIndex);
  }
});

// Load voices for speech synthesis
function loadVoices() {
  voices = window.speechSynthesis.getVoices();
}
window.speechSynthesis.onvoiceschanged = loadVoices;

// Speak current grammar concept
speakBtn.addEventListener("click", () => {
  if (grammarData.length === 0) return;
  const concept = grammarData[currentIndex];
  const utterance = new SpeechSynthesisUtterance(
    `${concept.title}. ${concept.definition}. Example: ${concept.example}`
  );

  const selectedVoice =
    voiceSelect.value === "female"
      ? voices.find((v) => v.name.toLowerCase().includes("female")) ||
        voices.find((v) => v.name.toLowerCase().includes("zira"))
      : voices.find((v) => v.name.toLowerCase().includes("male")) ||
        voices.find((v) => v.name.toLowerCase().includes("david"));

  if (selectedVoice) utterance.voice = selectedVoice;
  utterance.lang = "en-GB";
  utterance.rate = 1;
  utterance.pitch = 1;
  window.speechSynthesis.speak(utterance);
});
