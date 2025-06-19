document.addEventListener("DOMContentLoaded", function () {
  const trackId = document.body.dataset.trackId;

  // --- Element References ---
  const elements = {
    youtubeContainer: document.getElementById("youtube-container"),
    lyricsContainer: document.getElementById("lyrics-display-container"),

    originalTab: document.getElementById("original-tab"),
    englishTab: document.getElementById("english-tab"),

    romanizedText: document.getElementById("romanized-lyrics-text"),
    originalText: document.getElementById("original-lyrics-text"),
    englishText: document.getElementById("english-lyrics-text"),
  };

  // --- State Tracking based on initial HTML ---
  const contentState = {
    lyrics: elements.lyricsContainer.dataset.isLoading === "true",
    youtube: elements.youtubeContainer.dataset.isLoading === "true",
    translation: elements.englishTab ? elements.englishTab.disabled : false,
    pageFinalized: false,
  };

  // --- ColorThief Logic ---
  const img = document.querySelector(".track-image");
  function runColorThief() {
    if (!img) return;
    try {
      const colorThief = new ColorThief();
      const palette = colorThief.getPalette(img, 2);
      const dominantColor = `rgb(${palette[0].join(",")})`;
      const secondaryColor = palette[1]
        ? `rgb(${palette[1].join(",")})`
        : dominantColor;

      const root = document.documentElement;
      // Set the variables for the background gradient
      root.style.setProperty("--primary-color", dominantColor);
      root.style.setProperty("--secondary-color", secondaryColor);
      // NEW: Set the variable for the duotone hover effect
      root.style.setProperty("--album-dominant-color", dominantColor);

      const getTextColor = (rgb) =>
        (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255 > 0.5
          ? "#111"
          : "#fff";
      const headerTextColor = getTextColor(palette[0]);

      const heroHeader = document.querySelector(".hero-header");
      heroHeader.style.color = headerTextColor;
      heroHeader
        .querySelectorAll("h2, h3, a.artist-link")
        .forEach((el) => (el.style.color = headerTextColor));

      if (headerTextColor === "#111") {
        root.style.setProperty("--title-text-shadow", "none");
      } else {
        root.style.setProperty(
          "--title-text-shadow",
          `0 0 10px rgba(0,0,0,0.2), 0 0 20px var(--primary-color)`
        );
      }
    } catch (error) {
      console.error("ColorThief error:", error);
    }
  }

  if (img) {
    if (img.complete) runColorThief();
    else img.addEventListener("load", runColorThief);
  }

  // --- Lyrics Tab Switching Logic ---
  const tabs = document.querySelectorAll(".lyrics-tab");
  const contentPanes = document.querySelectorAll(".lyrics-content");
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      if (tab.disabled) return;
      tabs.forEach((t) => t.classList.remove("active"));
      contentPanes.forEach((p) => p.classList.remove("active"));
      tab.classList.add("active");
      const targetPane = document.getElementById(tab.dataset.target);
      if (targetPane) targetPane.classList.add("active");
    });
  });

  // --- Smart Content Polling Logic ---
  function pollForContent() {
    let attempts = 0;
    const maxAttempts = 30;

    const intervalId = setInterval(async () => {
      const allDone =
        !contentState.lyrics &&
        !contentState.youtube &&
        !contentState.translation;

      if (allDone) {
        clearInterval(intervalId);
        if (!contentState.pageFinalized) {
          showNotification("Page content finalized.", "info");
          contentState.pageFinalized = true;
        }
        return;
      }

      if (attempts >= maxAttempts) {
        clearInterval(intervalId);
        if (contentState.lyrics)
          updateElementText(
            elements.originalText,
            "Content failed to load. Please try refreshing."
          );
        if (contentState.translation)
          updateElementText(elements.englishText, "Translation timed out.");
        return;
      }

      try {
        const response = await fetch(`/api/track/status/${trackId}`);
        if (!response.ok) {
          clearInterval(intervalId);
          return;
        }

        const result = await response.json();
        if (result.status === "error") {
          clearInterval(intervalId);
          return;
        }

        const data = result.data;

        if (contentState.youtube && data.youtube_url) {
          const iframe = document.createElement("iframe");
          iframe.src = data.youtube_url;
          iframe.title = `YouTube video player for ${data.song_title}`;
          iframe.frameborder = 0;
          iframe.allow =
            "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture";
          iframe.allowfullscreen = true;

          elements.youtubeContainer.innerHTML = "";
          elements.youtubeContainer.appendChild(iframe);
          elements.youtubeContainer.classList.remove(
            "skeleton",
            "skeleton-block"
          );
          contentState.youtube = false;
        }

        const lyricsAreLoaded = !data.original_lyrics
          .toLowerCase()
          .includes("loading");
        if (contentState.lyrics && lyricsAreLoaded) {
          updateElementText(elements.originalText, data.original_lyrics);
          updateElementText(elements.romanizedText, data.romanized_lyrics);
          contentState.lyrics = false;
        }

        const translationIsLoaded =
          !data.translated_lyrics.toLowerCase().includes("loading") &&
          !data.translated_lyrics.toLowerCase().includes("in progress");
        if (contentState.translation && translationIsLoaded) {
          if (
            !data.translated_lyrics.toLowerCase().includes("not available") &&
            !data.translated_lyrics.toLowerCase().includes("failed")
          ) {
            updateElementText(elements.englishText, data.translated_lyrics);
            elements.englishTab.disabled = false;
          } else {
            elements.englishTab.classList.add("d-none");
          }
          contentState.translation = false;
        }
      } catch (error) {
        console.error("Polling error:", error);
        clearInterval(intervalId);
      }

      attempts++;
    }, 3000);
  }

  function updateElementText(element, text) {
    if (element.dataset.loading === "true") {
      element.innerHTML = "";
      element.dataset.loading = "false";
    }
    element.style.opacity = 0;
    element.textContent = text;
    element.style.transition = "opacity 0.5s ease-in-out";
    element.style.opacity = 1;
  }

  if (contentState.lyrics || contentState.youtube || contentState.translation) {
    pollForContent();
  }
});
