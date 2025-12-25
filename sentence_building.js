let data = {};
let currentTask = "";
let currentIndex = 0;
let currentSet = [];

document.addEventListener("DOMContentLoaded", () => {
  loadData();

  const taskSelect = document.getElementById("task-select");
  taskSelect.addEventListener("change", handleTaskSelection);

  document.getElementById("check-btn").addEventListener("click", checkAnswer);
  document
    .getElementById("next-btn")
    .addEventListener("click", loadNextQuestion);
});

function loadData() {
  fetch("data/lesson1_sentence_building.json")
    .then((res) => res.json())
    .then((json) => {
      data = json;
    })
    .catch((err) => console.error("Error loading JSON:", err));
}

function handleTaskSelection() {
  currentTask = this.value;

  if (!currentTask) {
    document.getElementById("task-area").classList.add("hidden");
    return;
  }

  currentSet = [...data[currentTask]];
  currentIndex = 0;

  document.getElementById("task-area").classList.remove("hidden");
  loadQuestion();
}

function loadQuestion() {
  const task = currentSet[currentIndex];

  document.getElementById("instruction").textContent = task.instruction;
  document.getElementById("question").textContent = task.question;
  document.getElementById("answer").value = "";
  document.getElementById("feedback").textContent = "";
  document.getElementById("next-btn").classList.add("hidden");
}

function checkAnswer() {
  const userAns = document.getElementById("answer").value.trim();
  const correctAns = currentSet[currentIndex].answer.trim();

  const feedback = document.getElementById("feedback");

  if (!userAns) {
    feedback.textContent = "Please type your answer.";
    feedback.className = "feedback incorrect";
    return;
  }

  if (userAns.toLowerCase() === correctAns.toLowerCase()) {
    feedback.textContent = "Excellent! Your sentence is correct.";
    feedback.className = "feedback correct";
  } else {
    feedback.textContent =
      "Not correct. A possible correct version is:\n" + correctAns;
    feedback.className = "feedback incorrect";
  }

  document.getElementById("next-btn").classList.remove("hidden");
}

function loadNextQuestion() {
  currentIndex++;
  if (currentIndex >= currentSet.length) {
    alert("You have completed this task!");
    return;
  }
  loadQuestion();
}
