document.addEventListener("DOMContentLoaded", function () {
  // --- Logic for reordering tracks WITHIN a playlist ---
  const trackListElement = document.getElementById("playlist-track-list");
  if (trackListElement) {
    const playlistId = trackListElement.dataset.playlistId;
    initializeTrackReordering(trackListElement, playlistId);
  }

  // --- Logic for reordering the main playlist grid ---
  const playlistGridElement = document.getElementById("playlist-grid");
  if (playlistGridElement) {
    initializePlaylistGridReordering(playlistGridElement);
  }
});

/**
 * Initializes SortableJS for the track list on the playlist details page.
 * @param {HTMLElement} trackListEl The list element containing the tracks.
 * @param {string} playlistId The ID of the current playlist.
 */
function initializeTrackReordering(trackListEl, playlistId) {
  new Sortable(trackListEl, {
    animation: 150,
    ghostClass: "sortable-ghost",
    onEnd: async function (evt) {
      const { oldIndex, newIndex } = evt;
      if (oldIndex === newIndex) return;

      try {
        const response = await fetch("/api/playlist/reorder_items", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            playlist_id: playlistId,
            old_index: oldIndex,
            new_index: newIndex,
          }),
        });
        const data = await response.json();
        if (!data.success)
          throw new Error(data.error || "Failed to save new order.");

        showNotification("Playlist order saved to Spotify.", "success");
        updateTrackNumbers(trackListEl);

        // NEW: Update playlist cover art and background if it changed
        if (data.new_image_url) {
          updatePlaylistImages(data.new_image_url);
        }
      } catch (error) {
        showNotification(`Error: ${error.message}`, "error");
      }
    },
  });
}

/**
 * Initializes SortableJS for the main playlist grid on the playlists page.
 * @param {HTMLElement} gridEl The grid element containing the playlist cards.
 */
function initializePlaylistGridReordering(gridEl) {
  const saveUrl = gridEl.dataset.saveUrl;
  if (!saveUrl) return;

  new Sortable(gridEl, {
    animation: 150,
    ghostClass: "sortable-ghost",
    onEnd: async function () {
      const playlistCards = gridEl.querySelectorAll(".playlist-card");
      const newPlaylistOrder = Array.from(playlistCards).map(
        (card) => card.dataset.playlistId
      );

      try {
        const response = await fetch(saveUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ playlist_ids: newPlaylistOrder }),
        });
        const data = await response.json();
        if (!data.success)
          throw new Error(data.error || "Failed to save new order.");

        showNotification("Custom playlist order saved!", "info");
      } catch (error) {
        showNotification(`Error: ${error.message}`, "error");
      }
    },
  });
}

/**
 * Updates the visual track numbers in a list after a reorder.
 * @param {HTMLElement} listEl The list element whose track numbers need updating.
 */
function updateTrackNumbers(listEl) {
  const trackItems = listEl.querySelectorAll(".list-group-item-action");
  trackItems.forEach((item, index) => {
    const trackNumberElement = item.querySelector(".track-number");
    if (trackNumberElement) {
      trackNumberElement.textContent = index + 1;
    }
  });
}

/**
 * Updates the main playlist images and re-triggers the dynamic background.
 * @param {string} newImageUrl The new URL for the playlist cover art.
 */
function updatePlaylistImages(newImageUrl) {
  const mainImage = document.querySelector(".entity-image-main");
  const headerBg = document.querySelector(".entity-header");
  const colorThiefImg = document.getElementById("color-thief-img");

  if (mainImage) mainImage.src = newImageUrl;
  if (headerBg) headerBg.style.backgroundImage = `url('${newImageUrl}')`;

  if (newImageUrl.includes("mosaic.scdn.co")) {
    document.body.classList.remove("dynamic-bg");
    if (colorThiefImg) colorThiefImg.src = "";
  } else {
    document.body.classList.add("dynamic-bg");
    if (colorThiefImg) {
      colorThiefImg.src = newImageUrl;
      if (typeof window.runColorThief === "function") {
        setTimeout(() => window.runColorThief(), 50);
      }
    }
  }
}
