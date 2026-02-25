// content/static/content/vocabulary/js/practice.js

document.addEventListener("DOMContentLoaded", function() {
    // Get all flashcards
    const flashcards = Array.from(document.querySelectorAll(".flashcard"));
    if (!flashcards.length) return;

    // State
    let currentIndex = 0;
    let flippedCards = new Set();

    // DOM elements
    const container = document.querySelector(".flashcards-container");
    const prevBtn = document.querySelector(".prev-card");
    const nextBtn = document.querySelector(".next-card");
    const shuffleBtn = document.querySelector(".shuffle-btn");
    const resetFlipsBtn = document.querySelector(".reset-flips-btn");
    const cardPositionSpan = document.querySelector(".card-position");
    const cardCountSpan = document.querySelector(".card-count");
    const totalCards = flashcards.length;

    // Update card count display
    if (cardCountSpan) {
        cardCountSpan.textContent = `${totalCards} words to practice`;
    }

    // Initialize
    function init() {
        updateCardVisibility();
        updateNavigation();
        attachCardListeners();
    }

    // Show/hide cards based on current index
    function updateCardVisibility() {
        flashcards.forEach((card, index) => {
            if (index === currentIndex) {
                card.classList.add("active");
            } else {
                card.classList.remove("active");
                // Reset flip state when navigating away
                card.classList.remove("flipped");
            }
        });
        
        // Update flippedCards set to only include current card if flipped
        const currentCard = flashcards[currentIndex];
        if (currentCard && currentCard.classList.contains("flipped")) {
            flippedCards.add(currentIndex);
        } else {
            flippedCards.delete(currentIndex);
        }
    }

    // Update navigation buttons and position display
    function updateNavigation() {
        if (prevBtn) prevBtn.disabled = currentIndex === 0;
        if (nextBtn) nextBtn.disabled = currentIndex === totalCards - 1;
        
        if (cardPositionSpan) {
            cardPositionSpan.textContent = `${currentIndex + 1} / ${totalCards}`;
        }
    }

    // Attach click listeners to cards for flip functionality
    function attachCardListeners() {
        flashcards.forEach((card, index) => {
            const front = card.querySelector(".card-front");
            const backBtn = card.querySelector(".flip-back-btn");

            // Flip to back when clicking front
            if (front) {
                front.addEventListener("click", function(e) {
                    // Don't flip if clicking the flip hint or if card is already flipped
                    if (e.target.classList.contains("flip-hint") || 
                        card.classList.contains("flipped")) {
                        return;
                    }
                    flipCard(card, index);
                });
            }

            // Flip back to front when clicking back button
            if (backBtn) {
                backBtn.addEventListener("click", function(e) {
                    e.stopPropagation();
                    flipCard(card, index);
                });
            }
        });
    }

    // Flip a card
    function flipCard(card, index) {
        card.classList.toggle("flipped");
        
        if (card.classList.contains("flipped")) {
            flippedCards.add(index);
        } else {
            flippedCards.delete(index);
        }
    }

    // Navigate to previous card
    function goToPrevious() {
        if (currentIndex > 0) {
            currentIndex--;
            updateCardVisibility();
            updateNavigation();
        }
    }

    // Navigate to next card
    function goToNext() {
        if (currentIndex < totalCards - 1) {
            currentIndex++;
            updateCardVisibility();
            updateNavigation();
        }
    }

    // Shuffle cards
    function shuffleCards() {
        // Get current active card's flipped state
        const wasFlipped = flashcards[currentIndex].classList.contains("flipped");
        
        // Remove all cards from DOM
        flashcards.forEach(card => card.remove());
        
        // Shuffle array
        const shuffled = [...flashcards].sort(() => Math.random() - 0.5);
        
        // Reattach in new order
        shuffled.forEach((card, newIndex) => {
            container.appendChild(card);
            // Update data-index attributes
            card.dataset.index = newIndex;
        });
        
        // Update the flashcards array reference
        flashcards.length = 0;
        flashcards.push(...shuffled);
        
        // Reset to first card
        currentIndex = 0;
        flippedCards.clear();
        
        // If the previously active card was flipped and is now at index 0, restore flip
        if (wasFlipped && shuffled[0] && shuffled[0].classList.contains("flipped")) {
            flippedCards.add(0);
        }
        
        updateCardVisibility();
        updateNavigation();
        attachCardListeners(); // Re-attach listeners to maintain references
    }

    // Reset all flips
    function resetAllFlips() {
        flashcards.forEach(card => {
            card.classList.remove("flipped");
        });
        flippedCards.clear();
    }

    // Event Listeners
    if (prevBtn) {
        prevBtn.addEventListener("click", goToPrevious);
    }

    if (nextBtn) {
        nextBtn.addEventListener("click", goToNext);
    }

    if (shuffleBtn) {
        shuffleBtn.addEventListener("click", shuffleCards);
    }

    if (resetFlipsBtn) {
        resetFlipsBtn.addEventListener("click", resetAllFlips);
    }

    // Keyboard navigation
    document.addEventListener("keydown", function(e) {
        // Only handle if we have cards
        if (!flashcards.length) return;

        // Don't handle if user is typing in an input
        if (e.target.matches('input, textarea, [contenteditable]')) return;

        switch(e.key) {
            case "ArrowLeft":
                e.preventDefault();
                goToPrevious();
                break;
            case "ArrowRight":
                e.preventDefault();
                goToNext();
                break;
            case " ":
                e.preventDefault();
                const currentCard = flashcards[currentIndex];
                if (currentCard) {
                    flipCard(currentCard, currentIndex);
                }
                break;
            case "f":
            case "F":
                // Press 'F' to flip current card
                e.preventDefault();
                const card = flashcards[currentIndex];
                if (card) {
                    flipCard(card, currentIndex);
                }
                break;
            case "r":
            case "R":
                // Press 'R' to reset all flips
                e.preventDefault();
                resetAllFlips();
                break;
        }
    });

    // Touch swipe support for mobile
    let touchStartX = 0;
    let touchEndX = 0;
    
    container.addEventListener("touchstart", function(e) {
        touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });
    
    container.addEventListener("touchend", function(e) {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    }, { passive: true });
    
    function handleSwipe() {
        const swipeThreshold = 50;
        const diff = touchEndX - touchStartX;
        
        if (Math.abs(diff) > swipeThreshold) {
            if (diff > 0) {
                // Swipe right - go to previous
                goToPrevious();
            } else {
                // Swipe left - go to next
                goToNext();
            }
        }
    }

    // Auto-flip reset when navigating (optional - comment out if you want to keep flip state)
    // This is commented out because we want to preserve flip state when navigating
    /*
    function resetCurrentFlipOnNavigate() {
        const currentCard = flashcards[currentIndex];
        if (currentCard && currentCard.classList.contains("flipped")) {
            currentCard.classList.remove("flipped");
            flippedCards.delete(currentIndex);
        }
    }
    */

    // Save and restore scroll position for card content
    let scrollPositions = new Map();
    
    function saveScrollPosition(index) {
        const card = flashcards[index];
        if (card && card.classList.contains("flipped")) {
            const content = card.querySelector(".card-content");
            if (content) {
                scrollPositions.set(index, content.scrollTop);
            }
        }
    }
    
    function restoreScrollPosition(index) {
        const card = flashcards[index];
        if (card && card.classList.contains("flipped")) {
            const content = card.querySelector(".card-content");
            if (content && scrollPositions.has(index)) {
                content.scrollTop = scrollPositions.get(index);
            }
        }
    }
    
    // Override updateCardVisibility to restore scroll positions
    const originalUpdateCardVisibility = updateCardVisibility;
    updateCardVisibility = function() {
        // Save scroll position of current card before hiding
        saveScrollPosition(currentIndex);
        
        originalUpdateCardVisibility();
        
        // Restore scroll position of new current card
        restoreScrollPosition(currentIndex);
    };

    // Initialize
    init();

    // Log for debugging
    console.log(`Practice page initialized with ${totalCards} flashcards`);
});

// Optional: Add touch feedback
function addTouchFeedback() {
    const cards = document.querySelectorAll(".flashcard");
    cards.forEach(card => {
        card.addEventListener("touchstart", function() {
            this.style.transform = "scale(0.98)";
        }, { passive: true });
        
        card.addEventListener("touchend", function() {
            this.style.transform = "";
        }, { passive: true });
        
        card.addEventListener("touchcancel", function() {
            this.style.transform = "";
        }, { passive: true });
    });
}

// Call after DOM is loaded
document.addEventListener("DOMContentLoaded", addTouchFeedback);