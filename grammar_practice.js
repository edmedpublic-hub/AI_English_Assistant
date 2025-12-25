let currentIndex = 0;
let questions = [];

fetch("data/lesson1_grammar_practice.json")
  .then((response) => response.json())
  .then((data) => {
    questions = data;
    showQuestion();
  })
  .catch((error) => console.error("Error loading grammar questions:", error));

const questionContainer = document.getElementById("question");
const optionsContainer = document.getElementById("options");
const nextBtn = document.getElementById("nextBtn");
const feedbackContainer = document.getElementById("feedback");

function showQuestion() {
  feedbackContainer.textContent = "";
  nextBtn.style.display = "none";

  const q = questions[currentIndex];
  questionContainer.textContent = q.question;
  optionsContainer.innerHTML = "";

  q.options.forEach((option) => {
    const btn = document.createElement("button");
    btn.textContent = option;
    btn.className = "option-btn";
    btn.addEventListener("click", () => checkAnswer(option, q.answer, btn));
    optionsContainer.appendChild(btn);
  });
}

function checkAnswer(selected, correct, btn) {
  const buttons = document.querySelectorAll(".option-btn");
  buttons.forEach((b) => (b.disabled = true));

  if (selected === correct) {
    btn.classList.add("correct");
    feedbackContainer.textContent = "✅ Correct! Well done.";
  } else {
    btn.classList.add("incorrect");
    feedbackContainer.textContent = `❌ Incorrect. The correct answer is "${correct}".`;
  }

  nextBtn.style.display = "block";
}

nextBtn.addEventListener("click", () => {
  currentIndex++;
  if (currentIndex < questions.length) {
    showQuestion();
  } else {
    document.querySelector(".container").innerHTML =
      "<h2>Grammar Practice</h2><p>🎉 Great job! You've completed this practice session.</p>";
  }
});
