// Vocabulary Hub JavaScript - Slideshow Effect
document.addEventListener("DOMContentLoaded", function() {
  // Get all slideshow cards
  const cards = Array.from(document.querySelectorAll(".slideshow-card"));
  if (!cards.length) return;

  // State
  let currentIndex = 0;

  // DOM elements
  const prevBtn = document.querySelector(".prev-btn");
  const nextBtn = document.querySelector(".next-btn");
  const currentCardSpan = document.querySelector(".current-card");
  const currentCountSpan = document.querySelector(".current-count");
  const progressBar = document.querySelector(".progress-bar");
  const totalCards = cards.length;

  // Update total cards display
  const totalCardsSpan = document.querySelector(".total-cards");
  if (totalCardsSpan) {
    totalCardsSpan.textContent = totalCards;
  }

  // Initialize
  function showCard(index) {
    // Hide all cards
    cards.forEach(card => {
      card.classList.remove("active");
    });
    
    // Show current card
    cards[index].classList.add("active");
    
    // Update counters
    if (currentCardSpan) {
      currentCardSpan.textContent = index + 1;
    }
    if (currentCountSpan) {
      currentCountSpan.textContent = index + 1;
    }
    
    // Update progress bar
    if (progressBar) {
      const progress = ((index + 1) / totalCards) * 100;
      progressBar.style.width = progress + "%";
    }
    
    // Update button states
    if (prevBtn) {
      prevBtn.disabled = index === 0;
    }
    if (nextBtn) {
      nextBtn.disabled = index === totalCards - 1;
    }
  }

  // Event Listeners
  if (prevBtn) {
    prevBtn.addEventListener("click", function() {
      if (currentIndex > 0) {
        currentIndex--;
        showCard(currentIndex);
      }
    });
  }

  if (nextBtn) {
    nextBtn.addEventListener("click", function() {
      if (currentIndex < totalCards - 1) {
        currentIndex++;
        showCard(currentIndex);
      }
    });
  }

  // Keyboard navigation
  document.addEventListener("keydown", function(e) {
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

  // Show first card
  showCard(0);
});