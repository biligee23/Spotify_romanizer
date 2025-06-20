document.addEventListener("DOMContentLoaded", function () {
  // --- Element References ---
  const searchForm = document.getElementById("search-form");
  const queryInput = document.getElementById("query-input");
  const searchButton = document.getElementById("search-button");
  const searchButtonText = searchButton.querySelector(".search-text");
  const spinner = searchButton.querySelector(".spinner");
  const resultsContainer = document.getElementById("search-results-container");
  const addToPlaylistBtn = document.getElementById("btn-add-to-playlist");
  const globalSelectAllBtn = document.getElementById("btn-select-all-global");
  const playlistModal = document.getElementById("playlist-modal");
  const modalCloseBtn = document.querySelector(".modal-close");
  const modalPlaylistList = document.getElementById("modal-playlist-list");
  const newPlaylistNameInput = document.getElementById("new-playlist-name");
  const modalCreateBtn = document.getElementById("btn-modal-create");
  const segmentedControl = document.getElementById("library-segmented-control");
  const bulkActionPill = document.getElementById("bulk-action-pill");
  const bulkFavoriteBtn = document.getElementById("btn-bulk-favorite");
  const bulkUnfavoriteBtn = document.getElementById("btn-bulk-unfavorite");
  const searchHistoryDropdown = document.getElementById(
    "search-history-dropdown"
  );

  // --- Search History Logic ---
  const HISTORY_KEY = "spotifyRomanizerSearchHistory";
  const MAX_HISTORY_ITEMS = 3;

  function getSearchHistory() {
    return JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];
  }

  function addSearchToHistory(query) {
    let history = getSearchHistory();
    const lowerCaseQuery = query.toLowerCase();
    history = history.filter((item) => item.toLowerCase() !== lowerCaseQuery);
    history.unshift(query);
    history = history.slice(0, MAX_HISTORY_ITEMS);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
  }

  function displaySearchHistory() {
    const history = getSearchHistory();
    if (history.length === 0) {
      searchHistoryDropdown.style.display = "none";
      return;
    }

    searchHistoryDropdown.innerHTML = history
      .map(
        (query) => `
      <div class="search-history-item" data-query="${query}">
        <i class="fa-solid fa-clock-rotate-left"></i>
        <span>${query}</span>
      </div>
    `
      )
      .join("");

    searchHistoryDropdown.style.display = "block";

    document.querySelectorAll(".search-history-item").forEach((item) => {
      item.addEventListener("click", function () {
        queryInput.value = this.dataset.query;
        searchHistoryDropdown.style.display = "none";
        searchForm.requestSubmit();
      });
    });
  }

  // --- Search Logic ---
  searchForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    const query = queryInput.value.trim();
    if (!query) return;

    addSearchToHistory(query);
    searchHistoryDropdown.style.display = "none";

    searchButton.disabled = true;
    searchButtonText.style.display = "none";
    spinner.style.display = "inline-block";
    resultsContainer.innerHTML = "";

    try {
      const response = await fetch(
        `/api/search?query=${encodeURIComponent(query)}`
      );
      if (!response.ok)
        throw new Error(`HTTP error! status: ${response.status}`);
      const tracks = await response.json();
      renderSearchResults(tracks);
    } catch (error) {
      console.error("Search failed:", error);
      resultsContainer.innerHTML =
        '<p class="text-center text-danger">Search failed. Please try again.</p>';
    } finally {
      searchButton.disabled = false;
      searchButtonText.style.display = "inline";
      spinner.style.display = "none";
    }
  });

  queryInput.addEventListener("focus", displaySearchHistory);

  document.addEventListener("click", function (e) {
    if (!searchForm.contains(e.target)) {
      searchHistoryDropdown.style.display = "none";
    }
  });

  function renderSearchResults(tracks) {
    if (!tracks || tracks.length === 0) {
      resultsContainer.innerHTML =
        '<h3 class="section-heading">No Results Found</h3>';
      return;
    }
    const resultsHtml = `
            <h3 class="section-heading">Search Results</h3>
            <div class="list-group">
                ${tracks
                  .map((track) => {
                    const detailUrl = `/track/${track.track_id}`;
                    return `<a href="${detailUrl}" class="list-group-item list-group-item-action d-flex align-items-center">
                        <img src="${track.image_url_sm}" alt="Album art for ${track.title}" class="search-result-img me-3">
                        <div class="flex-grow-1">
                            <h5 class="mb-1">${track.title}</h5>
                            <p class="mb-0 text-muted">${track.artist}</p>
                        </div>
                        <span class="play-icon" aria-hidden="true">►</span>
                    </a>`;
                  })
                  .join("")}
            </div>`;
    resultsContainer.innerHTML = resultsHtml;
  }

  // --- Library Interaction Logic ---
  function attachRowListeners(row) {
    row.addEventListener("click", function () {
      window.location.href = this.dataset.trackUrl;
    });
    row
      .querySelector(".btn-remove-cache")
      .addEventListener("click", handleRemoveCache);
    row
      .querySelector(".btn-favorite")
      .addEventListener("click", handleFavoriteToggle);
  }

  document
    .querySelectorAll(".recently-viewed-item")
    .forEach(attachRowListeners);

  async function handleRemoveCache(event) {
    event.preventDefault();
    event.stopPropagation();
    const button = event.currentTarget;
    const row = button.closest(".recently-viewed-item");
    const cacheKey = button.dataset.cacheKey;
    try {
      const response = await fetch("/api/cache/delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cache_key: cacheKey }),
      });
      if (response.ok) {
        row.style.transition = "opacity 0.3s ease, transform 0.3s ease";
        row.style.opacity = "0";
        row.style.transform = "scale(0.95)";
        setTimeout(() => {
          const parentList = row.parentElement;
          row.remove();
          updateEmptyListMessages(parentList);
        }, 300);
      } else {
        showNotification("Could not remove item. Please try again.", "error");
      }
    } catch (error) {
      showNotification("An error occurred. Please try again.", "error");
    }
  }

  async function handleFavoriteToggle(event) {
    event.preventDefault();
    event.stopPropagation();

    const button = event.currentTarget;
    const songRow = button.closest(".recently-viewed-item");
    const isFavorited = button.classList.contains("is-favorite");
    const endpoint = isFavorited
      ? "/api/favorites/remove"
      : "/api/favorites/add";
    const cacheKey = button.dataset.cacheKey;

    const favoritesList = document.getElementById("favorites-list");
    const historyList = document.getElementById("history-list");

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cache_key: cacheKey }),
      });
      const data = await response.json();

      if (data.success) {
        if (isFavorited) {
          button.classList.remove("is-favorite");
          historyList.prepend(songRow);
          showNotification("Removed from favorites", "success");
          updateEmptyListMessages(favoritesList);
          updateEmptyListMessages(historyList);
        } else {
          button.classList.add("is-favorite");
          favoritesList.prepend(songRow);
          showNotification("Added to favorites", "success");
          updateEmptyListMessages(historyList);
          updateEmptyListMessages(favoritesList);
        }
      } else {
        showNotification("Action failed. Please try again.", "error");
      }
    } catch (error) {
      showNotification("An error occurred.", "error");
    }
  }

  /**
   * Checks a list and adds or removes the enhanced empty state message as needed.
   * @param {HTMLElement} listElement The list element to check (e.g., favoritesList).
   */
  function updateEmptyListMessages(listElement) {
    if (!listElement) return;

    const isEmpty = !listElement.querySelector(".recently-viewed-item");
    const emptyMessage = listElement.querySelector(".empty-state-container");

    if (isEmpty && !emptyMessage) {
      const isFavorites = listElement.id === "favorites-list";
      const iconClass = isFavorites
        ? "fa-regular fa-star"
        : "fa-solid fa-clock-rotate-left";
      const title = isFavorites
        ? "No Favorite Songs Yet"
        : "Your History is Empty";
      const text = isFavorites
        ? "Click the star icon on any song in your history to add it here."
        : "Search for a song and view its details to start building your history.";

      const emptyStateHTML = `
        <div class="empty-state-container">
            <i class="${iconClass} empty-state-icon"></i>
            <h4 class="empty-state-title">${title}</h4>
            <p class="empty-state-text">${text}</p>
        </div>
      `;
      listElement.innerHTML = emptyStateHTML;
    } else if (!isEmpty && emptyMessage) {
      emptyMessage.remove();
    }
  }

  // --- Playlist Creation and Selection Logic ---
  const allCheckboxes = document.querySelectorAll(".song-checkbox");

  function updateGlobalButtonStates() {
    const selectedCount = document.querySelectorAll(
      ".song-checkbox:checked"
    ).length;
    const hasSelection = selectedCount > 0;

    if (addToPlaylistBtn) addToPlaylistBtn.disabled = !hasSelection;

    if (bulkActionPill) {
      bulkActionPill.classList.toggle("disabled", !hasSelection);
      bulkFavoriteBtn.disabled = !hasSelection;
      bulkUnfavoriteBtn.disabled = !hasSelection;
    }

    if (globalSelectAllBtn) {
      const allChecked =
        allCheckboxes.length > 0 && selectedCount === allCheckboxes.length;
      globalSelectAllBtn.textContent = allChecked
        ? "Deselect All"
        : "Select All";
    }
  }

  allCheckboxes.forEach((checkbox) => {
    checkbox.addEventListener("change", () => {
      checkbox
        .closest(".recently-viewed-item")
        .classList.toggle("selected", checkbox.checked);
      updateGlobalButtonStates();
    });
  });

  if (globalSelectAllBtn) {
    globalSelectAllBtn.addEventListener("click", () => {
      const allChecked =
        document.querySelectorAll(".song-checkbox:checked").length ===
        allCheckboxes.length;
      const shouldBeChecked = !allChecked;
      allCheckboxes.forEach((checkbox) => {
        if (checkbox.checked !== shouldBeChecked) {
          checkbox.checked = shouldBeChecked;
          checkbox.dispatchEvent(new Event("change"));
        }
      });
    });
  }

  // --- Bulk Favorite/Unfavorite Logic ---
  async function handleBulkFavoriteAction(isFavoriting) {
    const selectedCheckboxes = document.querySelectorAll(
      ".song-checkbox:checked"
    );
    const count = selectedCheckboxes.length;
    if (count === 0) return;

    const action = isFavoriting ? "favorite" : "unfavorite";
    if (
      !confirm(`Are you sure you want to ${action} ${count} selected song(s)?`)
    ) {
      return;
    }

    const cacheKeys = Array.from(selectedCheckboxes).map(
      (cb) =>
        cb.closest(".recently-viewed-item").querySelector(".btn-favorite")
          .dataset.cacheKey
    );
    const endpoint = isFavoriting
      ? "/api/favorites/add_bulk"
      : "/api/favorites/remove_bulk";

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cache_keys: cacheKeys }),
      });
      const data = await response.json();
      if (!data.success) throw new Error("Bulk action failed on the server.");

      showNotification(`Successfully ${action}d ${count} song(s).`, "success");

      const favoritesList = document.getElementById("favorites-list");
      const historyList = document.getElementById("history-list");
      selectedCheckboxes.forEach((cb) => {
        const songRow = cb.closest(".recently-viewed-item");
        const favButton = songRow.querySelector(".btn-favorite");
        if (isFavoriting) {
          favButton.classList.add("is-favorite");
          favoritesList.prepend(songRow);
        } else {
          favButton.classList.remove("is-favorite");
          historyList.prepend(songRow);
        }
      });
      updateEmptyListMessages(favoritesList);
      updateEmptyListMessages(historyList);
    } catch (error) {
      showNotification(`Error: ${error.message}`, "error");
    }
  }

  if (bulkFavoriteBtn) {
    bulkFavoriteBtn.addEventListener("click", () =>
      handleBulkFavoriteAction(true)
    );
  }
  if (bulkUnfavoriteBtn) {
    bulkUnfavoriteBtn.addEventListener("click", () =>
      handleBulkFavoriteAction(false)
    );
  }

  // --- Segmented Control Logic ---
  if (segmentedControl) {
    const highlight = segmentedControl.querySelector(".sg-control-highlight");
    const buttons = segmentedControl.querySelectorAll(".sg-control-btn");

    function moveHighlight(button) {
      highlight.style.width = `${button.offsetWidth}px`;
      highlight.style.transform = `translateX(${button.offsetLeft}px)`;
    }

    buttons.forEach((button) => {
      button.addEventListener("click", () => {
        buttons.forEach((btn) => btn.classList.remove("active"));
        button.classList.add("active");
        moveHighlight(button);

        const targetId = button.dataset.target;
        document
          .querySelectorAll(".library-content .list-group")
          .forEach((pane) => {
            pane.style.display =
              pane.id === targetId.substring(1) ? "block" : "none";
          });
      });
    });

    const activeButton = segmentedControl.querySelector(
      ".sg-control-btn.active"
    );
    if (activeButton) {
      moveHighlight(activeButton);
    }
  }

  // --- Modal Logic ---
  async function openPlaylistModal() {
    playlistModal.style.display = "flex";
    modalPlaylistList.innerHTML = '<div class="modal-spinner"></div>';
    try {
      const playlistsUrl = document.body.dataset.playlistsUrl;
      const response = await fetch(playlistsUrl);
      if (!response.ok) throw new Error("Failed to fetch playlists.");
      const playlists = await response.json();
      renderModalPlaylistList(playlists);
    } catch (error) {
      modalPlaylistList.innerHTML = `<p class="text-center text-danger">${error.message}</p>`;
    }
  }

  function closePlaylistModal() {
    playlistModal.style.display = "none";
  }

  function renderModalPlaylistList(playlists) {
    if (!playlists || playlists.length === 0) {
      modalPlaylistList.innerHTML =
        '<p class="text-center">You have no playlists to add to.</p>';
      return;
    }
    const listHtml = playlists
      .map(
        (p) => `
            <div class="modal-playlist-item" data-playlist-id="${p.id}">
                <img src="${
                  p.image_url || "/static/img/placeholder.png"
                }" alt="">
                <span>${p.name}</span>
            </div>
        `
      )
      .join("");
    modalPlaylistList.innerHTML = listHtml;

    document.querySelectorAll(".modal-playlist-item").forEach((item) => {
      item.addEventListener("click", () =>
        handleAddTracks(item.dataset.playlistId)
      );
    });
  }

  async function handleAddTracks(playlistId, newPlaylistName = null) {
    activeTrackIds = Array.from(
      document.querySelectorAll(".song-checkbox:checked")
    ).map((cb) => cb.dataset.trackId);

    let endpoint = "/api/playlist/add_tracks";
    let payload = {
      track_ids: activeTrackIds,
      playlist_id: playlistId,
    };

    if (newPlaylistName) {
      endpoint = "/api/create_playlist";
      payload = {
        track_ids: activeTrackIds,
        playlist_name: newPlaylistName,
      };
    }

    const button = newPlaylistName
      ? modalCreateBtn
      : document.querySelector(
          `.modal-playlist-item[data-playlist-id="${playlistId}"]`
        );
    const originalContent = button.innerHTML;
    button.innerHTML = '<span class="spinner"></span>';
    button.disabled = true;

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (data.success) {
        if (newPlaylistName) {
          showNotification(
            "Playlist creation started! It will appear in 'My Playlists' soon.",
            "info"
          );
        } else {
          let message = `Added ${data.added} new song(s).`;
          if (data.skipped > 0) {
            message += ` Skipped ${data.skipped} duplicate(s).`;
          }
          showNotification(message, "success");
        }
      } else {
        throw new Error(data.error || "Failed to add songs.");
      }
    } catch (error) {
      showNotification(`Error: ${error.message}`, "error");
    } finally {
      button.innerHTML = originalContent;
      button.disabled = false;
      closePlaylistModal();
    }
  }

  if (addToPlaylistBtn) {
    addToPlaylistBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      openPlaylistModal();
    });
  }
  if (modalCloseBtn) {
    modalCloseBtn.addEventListener("click", closePlaylistModal);
  }
  if (newPlaylistNameInput) {
    newPlaylistNameInput.addEventListener("input", () => {
      modalCreateBtn.disabled = newPlaylistNameInput.value.trim() === "";
    });
  }
  if (modalCreateBtn) {
    modalCreateBtn.addEventListener("click", () => {
      const newName = newPlaylistNameInput.value.trim();
      if (newName) {
        handleAddTracks(null, newName);
      }
    });
  }
  playlistModal.addEventListener("click", (event) => {
    if (event.target === playlistModal) {
      closePlaylistModal();
    }
  });

  updateGlobalButtonStates();
});
