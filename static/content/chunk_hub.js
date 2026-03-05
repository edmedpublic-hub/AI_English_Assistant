(function () {
  const englishText = window.CHUNK_DATA.englishText;
  const urduText = window.CHUNK_DATA.urduText;

  const englishSentences =
    englishText.match(/[^.!?]+(?:\.[A-Za-z]{1,3}\.)*[^.!?]*[.!?]?/g) || [englishText];
  const urduSentences = urduText.split(/۔\s+/);

  const tableBody = document.getElementById("sentence-table");

  englishSentences.forEach((en, i) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td class="sentence en" data-index="${i}" lang="en">${en}</td>
      <td class="sentence ur" data-index="${i}" lang="ur">${urduSentences[i] || ""}</td>
    `;
    tableBody.appendChild(row);
  });

  let currentIndex = 0;
  let paused = false;

  function clearHighlight() {
    document.querySelectorAll(".sentence").forEach(el =>
      el.classList.remove("highlight")
    );
  }

  function highlight(index) {
    clearHighlight();
    document.querySelectorAll(`.sentence[data-index="${index}"]`)
      .forEach(el => el.classList.add("highlight"));
    currentIndex = index;
  }

  function speak(text, lang) {
    return new Promise(resolve => {
      const u = new SpeechSynthesisUtterance(text);
      u.lang = lang;
      u.onend = resolve;
      speechSynthesis.speak(u);
    });
  }

  async function playSentence(index) {
    highlight(index);

    if (document.getElementById("english-audio")) {
      await document.getElementById("english-audio").play();
    } else {
      await speak(englishSentences[index], "en-US");
    }

    if (urduSentences[index]) {
      if (document.getElementById("urdu-audio")) {
        await document.getElementById("urdu-audio").play();
      } else {
        await speak(urduSentences[index], "ur-PK");
      }
    }
  }

  async function playAll() {
    paused = false;
    for (let i = 0; i < englishSentences.length; i++) {
      if (paused) break;
      await playSentence(i);
    }
    clearHighlight();
  }

  document.querySelectorAll(".sentence").forEach(el => {
    el.addEventListener("click", () => {
      paused = true;
      playSentence(parseInt(el.dataset.index));
    });
  });

  document.addEventListener("keydown", e => {
    if (e.key === "ArrowRight") highlight(Math.min(++currentIndex, englishSentences.length - 1));
    if (e.key === "ArrowLeft") highlight(Math.max(--currentIndex, 0));
    if (e.key === "Enter") playSentence(currentIndex);
  });

  document.getElementById("play-btn").onclick = playAll;
  document.getElementById("pause-btn").onclick = () => {
    paused = true;
    speechSynthesis.cancel();
};
document.getElementById("stop-btn").onclick = () => {
    paused = true;
    speechSynthesis.cancel();
    clearHighlight();
    currentIndex = 0;
};
  document.getElementById("resume-btn").onclick = playAll;
})();
