let questions = [];
let score = 0;
let attempts = 0;

// Load JSON from data folder
fetch("./data/lesson1_grammar_test.json")
  .then((res) => res.json())
  .then((data) => {
    questions = data;
    renderQuestions();
  })
  .catch((err) => console.error("Error loading questions:", err));

const container = document.getElementById("question-container");
const submitBtn = document.getElementById("submit-btn");
const retryBtn = document.getElementById("retry-btn");
const resultEl = document.getElementById("result");

const modal = document.getElementById("modal");
const redirectModal = document.getElementById("redirect-modal");

document.getElementById("confirm-yes").onclick = handleSubmit;
document.getElementById("confirm-no").onclick = () =>
  modal.classList.add("hidden");
document.getElementById("go-practice").onclick = () => {
  // Make sure this path points to your practice page
  window.location.href = "grammar_practice.html";
};
document.getElementById("stay-here").onclick = () => {
  redirectModal.classList.add("hidden");
  retryTest();
};

submitBtn.onclick = () => modal.classList.remove("hidden");
retryBtn.onclick = retryTest;

// --- CRITICAL CHANGE: Render Radio Inputs and Labels ---
function renderQuestions() {
  container.innerHTML = "";
  questions.forEach((q, qIndex) => {
    const qDiv = document.createElement("div");
    qDiv.classList.add("question-block");
    // Add data attribute for easier DOM lookup during scoring
    qDiv.dataset.questionId = qIndex;

    const qText = document.createElement("p");
    qText.innerHTML = `<strong>${qIndex + 1}. ${q.question}</strong>`;
    qDiv.appendChild(qText);

    q.options.forEach((opt, optIndex) => {
      const radioId = `q${qIndex}-opt${optIndex}`;
      const radioName = `question-${qIndex}`; // Unique name per question

      // 1. Create the hidden radio input
      const radioInput = document.createElement("input");
      radioInput.type = "radio";
      radioInput.id = radioId;
      radioInput.name = radioName;
      radioInput.value = opt; // Set the option text as the value
      radioInput.required = true; // Ensure an option is selected

      // 2. Create the visible LABEL (styled with the 'option' class)
      const label = document.createElement("label");
      label.setAttribute("for", radioId);
      label.classList.add("option");
      label.textContent = opt;

      // Optional: Re-select previously selected option if retrying
      if (q.selectedValue === opt) {
        radioInput.checked = true;
        label.classList.add("selected");
      }

      // Event listener to immediately toggle the 'selected' class on the label
      radioInput.addEventListener("change", () => {
        // Remove 'selected' from all labels in this block
        qDiv
          .querySelectorAll("label.option")
          .forEach((l) => l.classList.remove("selected"));
        // Add 'selected' to the current label
        label.classList.add("selected");
      });

      qDiv.appendChild(radioInput);
      qDiv.appendChild(label);
    });

    container.appendChild(qDiv);
  });
  // Re-show submit button after rendering
  submitBtn.classList.remove("hidden");
  retryBtn.classList.add("hidden");
}

// selectOption is no longer needed as the event listener is added
// directly to the radio input's 'change' event in renderQuestions().

function handleSubmit() {
  modal.classList.add("hidden");
  calculateScore();
}

// --- CRITICAL CHANGE: Calculate Score by Reading Checked Radio Values ---
function calculateScore() {
  score = 0;
  const questionBlocks = container.querySelectorAll(".question-block");
  let allAnswered = true;

  questionBlocks.forEach((block, qIndex) => {
    // Use querySelector to find the currently checked radio input for this question group name
    const selectedInput = block.querySelector(
      `input[name="question-${qIndex}"]:checked`
    );
    const q = questions[qIndex];

    // Save the selected value for retrying
    q.selectedValue = selectedInput ? selectedInput.value : null;

    if (!selectedInput) {
      allAnswered = false;
      // Optionally, highlight unanswered questions here
    } else if (selectedInput.value === q.answer) {
      score++;
    }
  });

  // Add validation check
  if (!allAnswered) {
    alert("Please answer all questions before submitting.");
    modal.classList.remove("hidden"); // Reopen the modal or handle error differently
    return;
  }

  const percent = (score / questions.length) * 100;

  // Display result
  let resultMessage = percent >= 80 ? "Excellent! 🎉" : "Good. 👍";
  if (percent < 60) {
    resultMessage = "Needs Review. 😔";
  }

  resultEl.textContent = `${resultMessage} Your Score: ${score}/${
    questions.length
  } (${percent.toFixed(1)}%)`;

  // Disable inputs after submission
  container
    .querySelectorAll('input[type="radio"]')
    .forEach((input) => (input.disabled = true));

  submitBtn.classList.add("hidden");
  retryBtn.classList.remove("hidden");

  if (percent < 60) {
    attempts++;
    // Redirect logic only after two failed attempts
    if (attempts >= 2) {
      redirectModal.classList.remove("hidden");
    }
  }
}

function retryTest() {
  score = 0;
  // Clear any temporary selection values for a true retry
  questions.forEach((q) => {
    q.selectedValue = null;
  });
  renderQuestions();
  resultEl.textContent = "";
  // attempts is intentionally NOT reset here, so the redirect modal can still appear
}
