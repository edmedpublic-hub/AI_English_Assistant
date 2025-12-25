let questions = [];
let currentQuestionIndex = 0;
let score = 0;
let answered = {};

async function loadQuestions() {
  const res = await fetch("data/lesson1_comprehension.json");
  questions = await res.json();
  showQuestion();
}

function showQuestion() {
  const q = questions[currentQuestionIndex];
  document.getElementById("question-text").textContent = `${
    currentQuestionIndex + 1
  }. ${q.question}`;

  const optionsList = document.getElementById("options-list");
  optionsList.innerHTML = "";
  q.options.forEach((opt, i) => {
    const li = document.createElement("li");
    li.innerHTML = `
      <label>
        <input type="radio" name="option" value="${i}">
        ${opt}
      </label>
    `;
    optionsList.appendChild(li);
  });

  document.getElementById("feedback").textContent = "";
}

function checkAnswer() {
  const selected = document.querySelector("input[name='option']:checked");
  if (!selected) return alert("Please select an answer before submitting.");

  const answerIndex = parseInt(selected.value);
  const correctIndex = questions[currentQuestionIndex].answer;
  const feedback = document.getElementById("feedback");

  if (answerIndex === correctIndex) {
    feedback.textContent = "✅ Correct!";
    feedback.style.color = "green";
    if (!answered[currentQuestionIndex]) score++;
  } else {
    feedback.textContent = "❌ Incorrect.";
    feedback.style.color = "red";
  }
  answered[currentQuestionIndex] = true;
}

function nextQuestion() {
  if (currentQuestionIndex < questions.length - 1) {
    currentQuestionIndex++;
    showQuestion();
  } else {
    showResult();
  }
}

function prevQuestion() {
  if (currentQuestionIndex > 0) {
    currentQuestionIndex--;
    showQuestion();
  }
}

function showResult() {
  document.getElementById(
    "result"
  ).textContent = `Your score: ${score} / ${questions.length}`;
}

document.getElementById("next-btn").addEventListener("click", nextQuestion);
document.getElementById("prev-btn").addEventListener("click", prevQuestion);
document.getElementById("submit-btn").addEventListener("click", checkAnswer);

loadQuestions();
