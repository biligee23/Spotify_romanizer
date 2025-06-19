document.addEventListener("DOMContentLoaded", function () {
  const viewAlbumsBtn = document.getElementById("btn-view-albums");
  const albumsModal = document.getElementById("albums-modal");
  const closeModalBtn = document.getElementById("albums-modal-close");
  const albumGrid = document.getElementById("modal-album-grid");

  /**
   * Fetches and displays the artist's albums in the modal.
   */
  async function openAlbumsModal() {
    albumsModal.style.display = "flex";
    albumGrid.innerHTML = '<div class="modal-spinner"></div>'; // Show spinner

    try {
      const url = viewAlbumsBtn.dataset.url;
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error("Failed to fetch albums.");
      }
      const albums = await response.json();
      renderAlbums(albums);
    } catch (error) {
      albumGrid.innerHTML = `<p class="text-center text-danger">${error.message}</p>`;
    }
  }

  /**
   * Renders the fetched albums into the modal grid.
   * @param {Array} albums - An array of album objects.
   */
  function renderAlbums(albums) {
    if (!albums || albums.length === 0) {
      albumGrid.innerHTML =
        '<p class="text-center">No albums found for this artist.</p>';
      return;
    }

    const albumHtml = albums
      .map(
        (album) => `
            <a href="/album/${album.id}" class="playlist-card">
                <img src="${
                  album.image_url || "/static/img/placeholder.png"
                }" alt="Cover for ${album.name}" class="playlist-card-img">
                <div class="playlist-card-overlay">
                    <h5 class="playlist-card-title">${album.name}</h5>
                    <p class="playlist-card-info">${album.release_date} • ${
          album.album_type
        }</p>
                </div>
            </a>
        `
      )
      .join("");

    albumGrid.innerHTML = albumHtml;
  }

  /**
   * Hides the albums modal.
   */
  function closeAlbumsModal() {
    albumsModal.style.display = "none";
  }

  // --- Event Listeners ---
  if (viewAlbumsBtn) {
    viewAlbumsBtn.addEventListener("click", openAlbumsModal);
  }
  if (closeModalBtn) {
    closeModalBtn.addEventListener("click", closeAlbumsModal);
  }
  if (albumsModal) {
    // Close modal if user clicks on the backdrop
    albumsModal.addEventListener("click", function (event) {
      if (event.target === albumsModal) {
        closeAlbumsModal();
      }
    });
  }
});
