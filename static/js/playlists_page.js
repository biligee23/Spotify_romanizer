document.addEventListener("DOMContentLoaded", function () {
  // --- Delete Playlist Logic ---
  document.querySelectorAll(".btn-delete-playlist").forEach((button) => {
    button.addEventListener("click", async function (event) {
      event.preventDefault();
      event.stopPropagation();

      if (
        !confirm(
          "Are you sure you want to delete this playlist from your Spotify account? This action cannot be undone."
        )
      ) {
        return;
      }

      const playlistId = this.dataset.playlistId;
      const card = document.getElementById(`playlist-${playlistId}`);

      try {
        const response = await fetch("/api/playlist/delete", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ playlist_id: playlistId }),
        });

        const data = await response.json();
        if (data.success) {
          showNotification("Playlist deleted successfully.", "success");
          card.style.transition = "opacity 0.3s ease, transform 0.3s ease";
          card.style.opacity = "0";
          card.style.transform = "scale(0.95)";
          setTimeout(() => card.remove(), 300);
        } else {
          throw new Error(data.error || "Failed to delete playlist.");
        }
      } catch (error) {
        showNotification(`Error: ${error.message}`, "error");
      }
    });
  });

  // --- Rename Playlist Logic ---
  document.querySelectorAll(".btn-edit-playlist").forEach((button) => {
    button.addEventListener("click", function (event) {
      event.preventDefault();
      event.stopPropagation();

      const card = this.closest(".playlist-card");
      const titleElement = card.querySelector(".playlist-card-title");
      const inputElement = card.querySelector(".input-rename-playlist");

      titleElement.style.display = "none";
      inputElement.style.display = "block";
      inputElement.focus();
      inputElement.select();
    });
  });

  document.querySelectorAll(".input-rename-playlist").forEach((input) => {
    const card = input.closest(".playlist-card");
    const titleElement = card.querySelector(".playlist-card-title");

    const cancelEdit = () => {
      input.value = titleElement.textContent; // Revert to current title text
      input.style.display = "none";
      titleElement.style.display = "block";
    };

    const saveEdit = async () => {
      const newName = input.value.trim();
      // Save only if the name has actually changed
      if (newName && newName !== titleElement.textContent) {
        const playlistId = input.dataset.playlistId;
        try {
          const response = await fetch("/api/playlist/rename", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              playlist_id: playlistId,
              new_name: newName,
            }),
          });
          const data = await response.json();
          if (data.success) {
            titleElement.textContent = newName;
            showNotification("Playlist renamed!", "success");
          } else {
            throw new Error(data.error || "Failed to rename.");
          }
        } catch (error) {
          showNotification(`Error: ${error.message}`, "error");
        }
      }
      cancelEdit(); // Always revert UI after attempt
    };

    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        saveEdit();
      } else if (event.key === "Escape") {
        cancelEdit();
      }
    });

    input.addEventListener("blur", saveEdit);
  });
});
