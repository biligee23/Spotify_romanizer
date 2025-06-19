document.addEventListener("DOMContentLoaded", function () {
  /**
   * Handles the deletion of a playlist after it has been confirmed to be empty.
   * @param {string} playlistId The ID of the playlist to delete.
   */
  async function deleteEmptyPlaylist(playlistId) {
    try {
      const response = await fetch("/api/playlist/delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ playlist_id: playlistId }),
      });
      const data = await response.json();
      if (data.success) {
        showNotification("Empty playlist deleted successfully.", "success");
        setTimeout(() => {
          window.location.href = "/playlists";
        }, 2000);
      } else {
        throw new Error(data.error || "Failed to delete the playlist.");
      }
    } catch (error) {
      showNotification(`Error: ${error.message}`, "error");
    }
  }

  document.querySelectorAll(".btn-remove-from-playlist").forEach((button) => {
    button.addEventListener("click", async function (event) {
      event.preventDefault();
      event.stopPropagation();

      if (
        !confirm("Are you sure you want to remove this song from the playlist?")
      ) {
        return;
      }

      const playlistId = this.dataset.playlistId;
      const trackId = this.dataset.trackId;
      const row = document.getElementById(`track-${trackId}`);

      try {
        const response = await fetch("/api/playlist/track/delete", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ playlist_id: playlistId, track_id: trackId }),
        });

        const data = await response.json();

        if (data.success) {
          showNotification("Track removed from playlist.", "success");

          row.style.transition = "opacity 0.3s ease, transform 0.3s ease";
          row.style.opacity = "0";
          row.style.transform = "scale(0.95)";
          setTimeout(() => {
            row.remove();
            const trackList = document.getElementById("playlist-track-list");
            if (trackList) {
              const trackItems = trackList.querySelectorAll(
                ".list-group-item-action"
              );
              trackItems.forEach((item, index) => {
                const trackNumberElement = item.querySelector(".track-number");
                if (trackNumberElement) {
                  trackNumberElement.textContent = index + 1;
                }
              });
            }
          }, 300);

          // --- UPDATED: More robust UI update logic ---
          if (data.new_image_url) {
            const mainImage = document.querySelector(".entity-image-main");
            const headerBg = document.querySelector(".entity-header");
            const colorThiefImg = document.getElementById("color-thief-img");

            if (mainImage) mainImage.src = data.new_image_url;
            if (headerBg)
              headerBg.style.backgroundImage = `url('${data.new_image_url}')`;

            // Check if the new URL is a single artwork or a mosaic
            if (data.new_image_url.includes("mosaic.scdn.co")) {
              // It's a mosaic, remove dynamic background
              document.body.classList.remove("dynamic-bg");
              if (colorThiefImg) colorThiefImg.src = ""; // Clear the source
            } else {
              // It's a single artwork, apply dynamic background
              document.body.classList.add("dynamic-bg");
              if (colorThiefImg) {
                colorThiefImg.src = data.new_image_url;
                if (typeof window.runColorThief === "function") {
                  // The 'load' event on the image will trigger runColorThief
                  // but we can call it directly as a fallback.
                  setTimeout(() => window.runColorThief(), 50);
                }
              }
            }
          }

          if (data.remaining_tracks === 0) {
            setTimeout(() => {
              if (
                confirm(
                  "This playlist is now empty. Would you like to delete it?"
                )
              ) {
                deleteEmptyPlaylist(playlistId);
              }
            }, 1000);
          }
        } else {
          throw new Error(data.error || "Failed to remove track.");
        }
      } catch (error) {
        showNotification(`Error: ${error.message}`, "error");
      }
    });
  });

  // --- Bulk Cache Priming Logic ---
  const primeCacheBtn = document.getElementById("btn-prime-cache");
  if (primeCacheBtn) {
    primeCacheBtn.addEventListener("click", async function () {
      const button = this;
      const btnText = button.querySelector(".btn-text");
      const spinner = button.querySelector(".spinner");
      const url = button.dataset.url;

      button.disabled = true;
      btnText.style.display = "none";
      spinner.style.display = "inline-block";

      showNotification("Checking playlist for uncached tracks...", "info");

      try {
        const response = await fetch(url, { method: "POST" });
        const data = await response.json();

        if (!data.success) {
          throw new Error(data.error || "Failed to start priming process.");
        }

        if (data.tasks_dispatched === 0) {
          showNotification(
            "All tracks in this playlist are already cached!",
            "success"
          );
          btnText.textContent = "All Lyrics Loaded";
          spinner.style.display = "none";
          btnText.style.display = "inline-block";
          return;
        }

        showNotification(
          `Pre-loading ${data.tasks_dispatched} track(s). This may take a moment.`,
          "info"
        );
        pollPrimingProgress(data.job_id, data.tasks_dispatched);
      } catch (error) {
        showNotification(`Error: ${error.message}`, "error");
        button.disabled = false;
        btnText.style.display = "inline-block";
        spinner.style.display = "none";
      }
    });
  }

  function pollPrimingProgress(jobId, totalTasks) {
    const progressContainer = document.getElementById("progress-container");
    const progressBar = document.getElementById("progress-bar");
    const progressText = document.getElementById("progress-text");
    const primeCacheBtn = document.getElementById("btn-prime-cache");
    const btnText = primeCacheBtn.querySelector(".btn-text");
    const spinner = primeCacheBtn.querySelector(".spinner");

    progressContainer.style.display = "block";

    const intervalId = setInterval(async () => {
      try {
        const response = await fetch(`/api/priming/status/${jobId}`);
        if (!response.ok) {
          if (response.status === 404) {
            updateProgressUI(totalTasks, totalTasks);
            clearInterval(intervalId);
            finalizePrimingUI();
          }
          return;
        }

        const data = await response.json();
        const completedCount = data.completed || 0;

        updateProgressUI(completedCount, totalTasks);

        if (completedCount >= totalTasks) {
          clearInterval(intervalId);
          finalizePrimingUI();
        }
      } catch (error) {
        clearInterval(intervalId);
        showNotification(
          "Error checking progress. Please refresh to see status.",
          "error"
        );
        progressText.textContent = "Error checking status.";
      }
    }, 2000);
  }

  function updateProgressUI(completed, total) {
    const progressBar = document.getElementById("progress-bar");
    const progressText = document.getElementById("progress-text");
    const percent = total > 0 ? (completed / total) * 100 : 100;

    progressBar.style.width = `${percent}%`;
    progressBar.setAttribute("aria-valuenow", percent);
    progressText.textContent = `Loading... (${completed} / ${total})`;
  }

  function finalizePrimingUI() {
    const primeCacheBtn = document.getElementById("btn-prime-cache");
    const btnText = primeCacheBtn.querySelector(".btn-text");
    const spinner = primeCacheBtn.querySelector(".spinner");
    const progressText = document.getElementById("progress-text");

    progressText.textContent =
      "All tasks complete! Translations may take a moment longer.";
    showNotification("Playlist pre-loading complete!", "success");
    btnText.textContent = "Lyrics Loaded";
    btnText.style.display = "inline-block";
    spinner.style.display = "none";
  }
});
