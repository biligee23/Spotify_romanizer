# Spotify Romanizer 🎵

**Spotify Romanizer** is a sophisticated, full-featured web application built with a robust Python, Flask, and Celery backend. It provides users with instant access to original Japanese, Romanized (Romaji), and English translated lyrics for any song on Spotify.

The application features a dynamic, SPA-like interface that feels fast and responsive, leveraging background task processing for slow operations and a self-healing cache to ensure data is always fresh and complete. It's more than just a lyrics viewer; it's a powerful tool for managing and exploring your music library in new ways.

### 🎬 Live Demo

[![Spotify Romanizer Demo](https://img.youtube.com/vi/your-youtube-video-id/0.jpg)](https://www.youtube.com/watch?v=your-youtube-video-id)
*(Click the image above to watch a full video demonstration of the application)*

---

## ✨ Features Showcase

### Core Experience: Instant Lyrics & Dynamic UI

The core of the application is designed to be fast, intuitive, and visually engaging. Pages load instantly with a polished skeleton UI, and content populates seamlessly as it's fetched by background workers.

![Main Demo GIF](assets/demo-main.gif)

| Feature                 | Description                                                                                                                                                           |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Triple-View Lyrics**  | Instantly switch between **Original Japanese**, **Romanized (Romaji)**, and **English** translated lyrics.                                                              |
| **Intelligent Fetching**| A smart algorithm finds the correct original Japanese lyrics on Genius, automatically filtering out romanized or translated versions.                                 |
| **Embedded Video**      | An official music video from YouTube is embedded directly on the track page for a complete audio-visual experience.                                                     |
| **Dynamic Theming**     | The page background and header dynamically adapt to the dominant colors of the album or artist artwork, creating a unique and immersive theme for every page.           |

---

### Advanced Playlist & Library Management

Spotify Romanizer is also a powerful tool for organizing your music. All actions happen in real-time without page reloads, providing a smooth and modern user experience.

<table>
  <tr>
    <td width="50%">
      <center><strong>Drag & Drop Reordering</strong></center>
      <img src="assets/demo-playlist-management.gif" alt="Playlist Management Demo" width="100%">
    </td>
    <td width="50%">
      <center><strong>Seamless Bulk Actions</strong></center>
      <img src="assets/demo-bulk-actions.gif" alt="Bulk Actions Demo" width="100%">
    </td>
  </tr>
</table>

| Feature                     | Description                                                                                                                                                                                          |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Drag & Drop Reordering**  | **Tracks:** Reorder tracks within a playlist, and the changes are instantly saved to your Spotify account. <br> **Playlists:** Create a custom, persistent order for your main playlist view inside the app. |
| **Bulk Actions**            | Select multiple songs from your library and favorite, unfavorite, or add them to a playlist all at once.                                                                                             |
| **Personalized Library**    | Every song you view is added to your library, which is intelligently separated into a permanent **Favorites** list and a temporary **History** list, managed by an LFU caching policy.                 |
| **Duplicate-Free Adding**   | When adding songs to an existing playlist, the app automatically detects and skips any tracks that are already present, keeping your playlists clean.                                                |
| **Asynchronous Creation**   | New playlists are created in the background by a Celery worker, so your UI is never blocked, even when adding a large number of songs.                                                              |

---

### Power-User Features: Bulk Cache Priming

For users who want the fastest possible experience, the entire lyrical content of a playlist can be pre-loaded and cached in the background.

![Cache Priming Screenshot](assets/demo-cache-priming.png)

A live progress bar provides clear feedback on the status of the bulk operation. This ensures that when you navigate to the songs later, the data loads instantly from the cache. The system is smart enough to skip any tracks that are already cached.

---

## 🛠️ Tech Stack & Architecture

-   **Backend:** Python, Flask
-   **Asynchronous Tasks:** Celery with a Redis message broker
-   **Cache & Data Store:** Redis (used for Flask-Caching, Celery backend, and custom data persistence)
-   **Frontend:** Vanilla JavaScript (ES6+), HTML5, CSS3
-   **APIs:** Spotify API, Genius API (via `lyricsgenius`), YouTube Data API
-   **Containerization:** Docker, Docker Compose

The application is architected with a clean separation of concerns, using a service-oriented pattern on the back-end and a modular, event-driven approach on the front-end. The use of Celery workers to offload all slow network requests ensures the main Flask application remains lightweight and highly responsive.

---

## 🚀 Getting Started

This project is fully containerized, making local setup incredibly simple and consistent.

### Prerequisites

-   [Docker](https://www.docker.com/products/docker-desktop/) & Docker Compose (usually included with Docker Desktop)
-   Git

### Setup Instructions

**1. Clone the Repository**

```bash
git clone https://github.com/your-username/spotify-romanizer.git
cd spotify-romanizer
```

**2. Create Your Environment File**

The application requires API keys from Spotify, Genius, and YouTube. A template is provided to make this easy.

-   **Copy the template file:**
    ```bash
    cp .env.template .env
    ```
-   **Edit the `.env` file:** Open the new `.env` file in your favorite text editor.
-   **Fill in your keys:** Follow the instructions inside the file to get your API credentials from the respective developer portals and paste them into the file.
-   **Crucially**, ensure the `SPOTIFY_REDIRECT_URI` in your `.env` file (`http://localhost:5000/callback` by default) is added to the list of "Redirect URIs" in your application's settings on the Spotify Developer Dashboard.

**3. Build and Run with Docker Compose**

This single command will build the Docker images for the web server and the Celery worker, start the Redis container, and run the entire application stack.

```bash
docker-compose up --build
```

-   The `--build` flag is only needed the first time or after changing dependencies. For subsequent runs, you can just use `docker-compose up`.
-   You will see logs from three services (`web`, `worker`, `redis`) in your terminal. Wait until they are all running and stable.

**4. Access the Application**

Once the containers are running, open your web browser and navigate to:

### [http://localhost:5000](http://localhost:5000)

You should be greeted by the Spotify Romanizer login page. Enjoy!

### Stopping the Application

To stop all the running containers, press `Ctrl+C` in the terminal where `docker-compose` is running. To remove the containers and network entirely, run:

```bash
docker-compose down```
