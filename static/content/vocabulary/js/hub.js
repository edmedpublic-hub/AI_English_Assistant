// hub.js — Vocabulary Hub Slideshow

document.addEventListener("DOMContentLoaded", function () {
  const cards = Array.from(document.querySelectorAll(".slideshow-card"));
  if (!cards.length) return;

  let currentIndex = 0;

  const prevBtn = document.querySelector(".prev-btn");
  const nextBtn = document.querySelector(".next-btn");
  const currentCardSpan = document.querySelector(".current-card");
  const currentCountSpan = document.querySelector(".current-count");
  const progressBar = document.querySelector(".progress-bar");
  const totalCardsSpan = document.querySelector(".total-cards");
  const totalCards = cards.length;

  if (totalCardsSpan) {
    totalCardsSpan.textContent = totalCards;
  }

  function showCard(index) {
    // Hide all cards using Bootstrap d-none
    cards.forEach(card => {
      card.classList.add("d-none");
      card.classList.remove("active");
    });

    // Show target card
    cards[index].classList.remove("d-none");
    cards[index].classList.add("active");

    // Update counters
    if (currentCardSpan) currentCardSpan.textContent = index + 1;
    if (currentCountSpan) currentCountSpan.textContent = index + 1;

    // Update progress bar
    if (progressBar) {
      const progress = ((index + 1) / totalCards) * 100;
      progressBar.style.width = progress + "%";
      progressBar.setAttribute("aria-valuenow", Math.round(progress));
    }

    // Update button states
    if (prevBtn) prevBtn.disabled = index === 0;
    if (nextBtn) nextBtn.disabled = index === totalCards - 1;
  }

  if (prevBtn) {
    prevBtn.addEventListener("click", function () {
      if (currentIndex > 0) {
        currentIndex--;
        showCard(currentIndex);
      }
    });
  }

  if (nextBtn) {
    nextBtn.addEventListener("click", function () {
      if (currentIndex < totalCards - 1) {
        currentIndex++;
        showCard(currentIndex);
      }
    });
  }

  // Keyboard navigation
  document.addEventListener("keydown", function (e) {
    if (e.key === "ArrowLeft") {
      e.preventDefault();
      if (currentIndex > 0) {
        currentIndex--;
        showCard(currentIndex);
      }
    } else if (e.key === "ArrowRight") {
      e.preventDefault();
      if (currentIndex < totalCards - 1) {
        currentIndex++;
        showCard(currentIndex);
      }
    }
  });

  // Initialize — show first card
  showCard(0);
});