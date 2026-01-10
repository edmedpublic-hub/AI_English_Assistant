document.addEventListener("DOMContentLoaded", () => {
  let currentCard = 0;

  const cards = Array.from(document.querySelectorAll(".vocab-card"));
  if (!cards.length) return; // Safety: no vocab cards

  function showCard(index) {
    cards.forEach((card, i) => {
      card.classList.toggle("hidden", i !== index);
    });

    const prevBtn = cards[index].querySelector(".prev-btn");
    const nextBtn = cards[index].querySelector(".next-btn");

    if (prevBtn) prevBtn.disabled = index === 0;
    if (nextBtn) nextBtn.disabled = index === cards.length - 1;
  }

  document.body.addEventListener("click", (e) => {
    if (e.target.classList.contains("next-btn")) {
      if (currentCard < cards.length - 1) {
        currentCard++;
        showCard(currentCard);
      }
    }

    if (e.target.classList.contains("prev-btn")) {
      if (currentCard > 0) {
        currentCard--;
        showCard(currentCard);
      }
    }
  });

  // Initialize first card
  showCard(currentCard);
});
