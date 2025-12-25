const quizContainer = document.getElementById("quiz-container");
const submitBtn = document.getElementById("submitBtn");
const retakeBtn = document.getElementById("retakeBtn");
const scoreEl = document.getElementById("score");
const resultSection = document.getElementById("result-section");
const feedbackContainer = document.getElementById("detailed-feedback");

let quizData = [];
let selectedAnswers = {};

// Load questions from JSON
fetch("data/comprehension_questions.json")
  .then((res) => res.json())
  .then((data) => {
    quizData = shuffle(data).slice(0, 10); // 10 random questions
    renderQuiz();
  })
  .catch((err) => console.error("Error loading quiz:", err));

// Display questions
function renderQuiz() {
  quizContainer.innerHTML = "";
  quizData.forEach((q, i) => {
    const questionDiv = document.createElement("div");
    questionDiv.classList.add("question");
    questionDiv.innerHTML = `
      <p><strong>${i + 1}. ${q.question}</strong></p>
      <div class="options">
        ${q.options
          .map(
            (opt, j) => `
          <label>
            <input type="radio" name="q${i}" value="${opt}">
            ${opt}
          </label>`
          )
          .join("")}
      </div>`;
    quizContainer.appendChild(questionDiv);
  });
}

// Shuffle helper
function shuffle(arr) {
  return arr.sort(() => Math.random() - 0.5);
}

// Handle Submit
submitBtn.addEventListener("click", () => {
  const answers = document.querySelectorAll("input[type='radio']:checked");
  if (answers.length < quizData.length) {
    alert("Please attempt all questions!");
    return;
  }

  let score = 0;
  feedbackContainer.innerHTML = "";

  answers.forEach((ans, i) => {
    const question = quizData[i];
    const userAnswer = ans.value;
    const isCorrect = userAnswer === question.answer;
    if (isCorrect) score++;

    const feedback = document.createElement("p");
    feedback.innerHTML = `<strong>${i + 1}. ${question.question}</strong><br>
      Your answer: <span class="${
        isCorrect ? "correct" : "incorrect"
      }">${userAnswer}</span><br>
      Correct answer: ${question.answer}`;
    feedbackContainer.appendChild(feedback);
  });

  const percentage = ((score / quizData.length) * 100).toFixed(0);
  scoreEl.textContent = `Score: ${score}/${quizData.length} (${percentage}%)`;

  resultSection.style.display = "block";
  submitBtn.style.display = "none";
  retakeBtn.style.display = "inline-block";

  // Save result in localStorage
  localStorage.setItem("lastTestScore", percentage);
});

// Retake Test
retakeBtn.addEventListener("click", () => {
  resultSection.style.display = "none";
  submitBtn.style.display = "inline-block";
  retakeBtn.style.display = "none";
  quizData = shuffle(quizData);
  renderQuiz();
});
