// practice.js - COMPLETE WORKING VERSION

document.addEventListener("DOMContentLoaded", function () {
  console.log("✅ Practice.js loaded");

  const flashcards = Array.from(document.querySelectorAll(".flashcard"));
  if (!flashcards.length) {
    console.log("❌ No flashcards found");
    return;
  }

  let currentIndex = 0;
  const totalCards = flashcards.length;

  const container = document.querySelector(".flashcards-container");
  const prevBtn = document.querySelector(".prev-card");
  const nextBtn = document.querySelector(".next-card");
  const shuffleBtn = document.querySelector(".shuffle-btn");
  const resetFlipsBtn = document.querySelector(".reset-flips-btn");
  const cardPositionSpan = document.querySelector(".card-position");

  console.log(`📊 Found ${totalCards} flashcards`);

  function resetCardFaces(card) {
    const front = card.querySelector(".card-front");
    const back = card.querySelector(".card-back");
    if (front && back) {
      front.classList.remove("d-none");
      back.classList.add("d-none");
    }
  }

  function resetAllFlips() {
    flashcards.forEach(card => resetCardFaces(card));
  }

  function showCard(index) {
    flashcards.forEach((card, i) => {
      if (i === index) {
        card.classList.remove("d-none");
      } else {
        card.classList.add("d-none");
        resetCardFaces(card);
      }
    });
    if (cardPositionSpan) cardPositionSpan.textContent = `${index + 1} / ${totalCards}`;
    if (prevBtn) prevBtn.disabled = index === 0;
    if (nextBtn) nextBtn.disabled = index === totalCards - 1;
  }

  function flipCurrentCard() {
    const currentCard = flashcards[currentIndex];
    if (!currentCard) return;
    const front = currentCard.querySelector(".card-front");
    const back = currentCard.querySelector(".card-back");
    if (!front || !back) return;
    if (front.classList.contains("d-none")) {
      front.classList.remove("d-none");
      back.classList.add("d-none");
    } else {
      front.classList.add("d-none");
      back.classList.remove("d-none");
    }
  }

  function goToPrevious() {
    if (currentIndex > 0) { currentIndex--; showCard(currentIndex); }
  }

  function goToNext() {
    if (currentIndex < totalCards - 1) { currentIndex++; showCard(currentIndex); }
  }

  function shuffleCards() {
    const cards = Array.from(container.children).filter(c => c.classList.contains("flashcard"));
    for (let i = cards.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      container.insertBefore(cards[j], cards[i]);
    }
    flashcards.length = 0;
    flashcards.push(...Array.from(container.children).filter(c => c.classList.contains("flashcard")));
    flashcards.forEach((card, idx) => { card.dataset.index = idx; });
    currentIndex = 0;
    resetAllFlips();
    showCard(0);
  }

  function flipBackToFront(card) {
    if (!card) return;
    const front = card.querySelector(".card-front");
    const back = card.querySelector(".card-back");
    if (front && back) {
      front.classList.remove("d-none");
      back.classList.add("d-none");
    }
  }

  // Card click — flip
  flashcards.forEach(card => {
    card.addEventListener("click", function (e) {
      if (e.target.closest(".flip-back-btn")) { e.stopPropagation(); return; }
      if (parseInt(card.dataset.index) === currentIndex) flipCurrentCard();
    });
  });

  // Flip-back button
  document.querySelectorAll(".flip-back-btn").forEach(btn => {
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      const card = this.closest(".flashcard");
      if (card && parseInt(card.dataset.index) === currentIndex) flipBackToFront(card);
    });
  });

  if (prevBtn) prevBtn.addEventListener("click", e => { e.stopPropagation(); goToPrevious(); });
  if (nextBtn) nextBtn.addEventListener("click", e => { e.stopPropagation(); goToNext(); });
  if (shuffleBtn) shuffleBtn.addEventListener("click", e => { e.stopPropagation(); shuffleCards(); });
  if (resetFlipsBtn) resetFlipsBtn.addEventListener("click", e => { e.stopPropagation(); resetAllFlips(); });

  document.addEventListener("keydown", function (e) {
    if (e.target.matches("input, textarea, [contenteditable]")) return;
    switch (e.key) {
      case "ArrowLeft":  e.preventDefault(); goToPrevious(); break;
      case "ArrowRight": e.preventDefault(); goToNext(); break;
      case " ": case "f": case "F": e.preventDefault(); flipCurrentCard(); break;
      case "r": case "R": e.preventDefault(); resetAllFlips(); break;
    }
  });

  let touchStartX = 0;
  container.addEventListener("touchstart", e => { touchStartX = e.changedTouches[0].screenX; }, { passive: true });
  container.addEventListener("touchend", e => {
    const diff = e.changedTouches[0].screenX - touchStartX;
    if (Math.abs(diff) > 50) { diff > 0 ? goToPrevious() : goToNext(); }
  }, { passive: true });

  // Initialize
  resetAllFlips();
  showCard(0);

  console.log("✅ Practice initialized successfully!");
});