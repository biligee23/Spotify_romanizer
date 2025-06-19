<div align="center">
  <h1>🎵 Spotify Romanizer 🎵</h1>
  <p>
    <strong>Your personal gateway to understanding and enjoying Japanese music.</strong>
  </p>
  <p>
    Instantly fetch and view Original Japanese, Romanized (Romaji), and English Translated lyrics for any song on Spotify.
  </p>
  <br>
  <p>
    <a href="https://www.gnu.org/licenses/gpl-3.0">
      <img src="https://img.shields.io/badge/License-GPLv3-blue.svg" alt="License: GPL v3" />
    </a>
  </p>
</div>

---

### 🎬 Live Demo & Showcase

A picture is worth a thousand words, and a video is worth a million. Watch the full demonstration of Spotify Romanizer's features on YouTube.

[![Spotify Romanizer Demo](https://img.youtube.com/vi/your-youtube-video-id/0.jpg)](https://www.youtube.com/watch?v=your-youtube-video-id)
*(Click the image above to watch the full video demo)*

---

## ✨ What is Spotify Romanizer?

Spotify Romanizer is a sophisticated web application designed for music lovers who want to bridge the language gap. It connects securely to your Spotify account and acts as a powerful companion, enhancing your listening experience with multi-format lyrics, advanced playlist management, and a dynamic, modern user interface.

The entire application is built with a focus on performance and user experience, leveraging a robust asynchronous backend to ensure that interactions are fast, smooth, and seamless.

---

## 🚀 Core Features

### 🎤 Lyrics & Translation
- **Triple-View Lyrics:** Instantly switch between **Original Japanese**, **Romanized (Romaji)**, and **English** translated lyrics in a clean, tabbed interface.
- **Intelligent Lyric Fetching:** A smart algorithm finds the correct original Japanese lyrics on Genius by prioritizing the shortest, most relevant song titles, automatically filtering out derivative versions.
- **Embedded Music Video:** An official music video from YouTube is embedded directly on the track page for a complete audio-visual experience.

### 🎨 Dynamic & Responsive User Experience
- **Asynchronous Skeleton Loading:** Pages load instantly with a polished "skeleton" UI. The lyrics, video, and translation then populate seamlessly as the data is fetched by background Celery workers.
- **Real-Time UI Updates:** All major actions—favoriting a song, adding to a playlist, reordering tracks—happen instantly on the page without requiring a full page reloads, creating a smooth, modern SPA-like feel.
- **Dynamic Theming:** The track and artist pages feature a beautiful, dynamic background gradient that is generated from the dominant colors of the album or artist artwork.
- **Polished Hover Effects:** Album art comes to life with a stylish, theme-aware "duotone" hover effect.

### 📚 Personalized Music Library & Management
- **Favorites & History:** Every song you view is automatically added to your personal library, which is intelligently separated into a permanent "Favorites" list and a temporary "History" list, managed by an LFU caching policy.
- **Self-Healing Cache:** If a background task fails (e.g., a translation), the app will automatically re-trigger the task the next time you visit the page, ensuring your data eventually becomes complete.
- **Bulk Actions:** Select multiple songs at once to favorite, unfavorite, or add them to a playlist in a single, efficient action.

### 🎶 Advanced Playlist Tools
- **Full Playlist Management:** View, rename, and delete your Spotify playlists directly from the app.
- **Duplicate-Free Adding:** When adding songs to an existing playlist, the app automatically checks for and skips any tracks that are already present.
- **Asynchronous Creation:** New playlists are created in the background, so your UI is never blocked.
- **Drag-and-Drop Reordering:**
    - **Tracks:** Reorder tracks within a playlist, and the changes are instantly saved to your Spotify account.
    - **Playlists:** Create a custom, persistent order for your main playlist view inside the app.
- **Bulk Cache Priming:** Pre-load all the lyrics for an entire playlist with a single click, with a live progress bar to track the status.

---

## 🖼️ Visual Showcase

<table>
  <tr>
    <td width="50%">
      <center><strong>Seamless Playlist Management</strong></center>
      <img src="assets/demo-playlist-management.gif" alt="Playlist Management Demo" width="100%">
    </td>
    <td width="50%">
      <center><strong>Efficient Bulk Actions</strong></center>
      <img src="assets/demo-bulk-actions.gif" alt="Bulk Actions Demo" width="100%">
    </td>
  </tr>
</table>

---

## 🛠️ Tech Stack & Architecture

-   **Backend:** Python, Flask
-   **Asynchronous Tasks:** Celery with a Redis message broker
-   **Cache & Data Store:** Redis (used for Flask-Caching, Celery backend, and custom data persistence)
-   **Frontend:** Vanilla JavaScript (ES6+), HTML5, CSS3
-   **APIs:** Spotify API, Genius API (via `lyricsgenius`), YouTube Data API
-   **Containerization:** Docker, Docker Compose

---

## ⚙️ Local Setup & Installation

This project is fully containerized, making local setup incredibly simple and consistent.

### Prerequisites
- [Docker](https://www.docker.com/products/docker-desktop/) & Docker Compose
- Git

### Step 1: Clone the Repository
First, clone the project to your local machine.
```bash
git clone https://github.com/your-github-username/spotify-romanizer.git
cd spotify-romanizer```

### Step 2: Configure Your API Keys (Crucial Step)
This application requires credentials from Spotify, Genius, and YouTube to function.
1.  **Create your `.env` file** by copying the provided template. This file is where you will store your secret keys.
    ```bash
    cp .env.template .env
    ```
2.  **Get Your Credentials:**
    -   **Spotify:** Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/) to create an app and get your Client ID and Secret.
    -   **Genius:** Go to the [Genius API page](https://genius.com/api-clients) to create a client and get your Access Token.
    -   **YouTube:** Go to the [Google Cloud Console](https://console.cloud.google.com/apis/credentials) to create a project, enable the "YouTube Data API v3", and get an API Key.
3.  **Fill in the `.env` file:** Open the `.env` file you just created and paste in your keys.
4.  **Set Spotify Redirect URI:** In your Spotify Developer Dashboard, you **must** add `http://localhost:5000/callback` to the list of "Redirect URIs" in your app's settings.

### Step 3: Build & Run the Application
With your configuration in place, this single command will build and run the entire application stack.
```bash
docker-compose up --build
```
- The `--build` flag is only needed the first time or after changing dependencies. For subsequent runs, you can just use `docker-compose up`.
- You will see logs from the `web`, `worker`, and `redis` services. Wait for them to stabilize.

### Step 4: Access Spotify Romanizer
Once the containers are running, open your web browser and navigate to:
### [http://localhost:5000](http://localhost:5000)
You should be greeted by the login page. Enjoy the application!

### Stopping the Application
- To stop the running containers, press `Ctrl+C` in the terminal.
- To remove the containers and all associated network resources, run:
  ```bash
  docker-compose down
  ```

---

## ⚠️ Known Limitations & Future Ideas

-   **YouTube API Quota:** The application uses the YouTube Data API v3 to find music videos. The default daily quota provided by Google for a new project is **10,000 units**. Each search query costs **100 units**. This means the application can perform approximately **100 searches for uncached songs per day**. Once this limit is reached, new YouTube videos will not be found until the quota resets at midnight PST. This limitation is a primary reason for the robust caching system and the "Bulk Cache Priming" feature.
-   **Future Enhancements:** A potential future improvement would be to integrate Spotify's Audio Analysis API to display features like Danceability, Energy, and Tempo, and allow users to sort their playlists by these metrics.

---

## ✍️ Original Work & Licensing Philosophy

This project was conceived and developed from the ground up as a portfolio piece to showcase modern web application architecture and a high-quality user experience. All of the core application code in the `src/` directory is my own original work.

The choice of the **GNU GPLv3 license** is a deliberate one, made to reflect the following principles:
1.  **Freedom to Learn:** I strongly believe in the open-source ethos of sharing knowledge. Anyone is free to clone, run, and study this codebase to learn from its patterns and implementation.
2.  **Protection from Commercialization:** The "copyleft" nature of the GPLv3 ensures that while this project is open for all to see and learn from, it cannot be absorbed into a closed-source, proprietary commercial product. If any company uses this code as part of a distributed product, they must release the full source code of their product under the same terms.
3.  **Sharing is Caring:** If you adapt this code to create and distribute your own cool project, you are required to share your source code under the same license, ensuring the community continues to benefit.

---

## 🙏 Acknowledgements

This project would not be possible without the incredible services and APIs provided by the following platforms:

-   **[Spotify](https://spotify.com)** for their comprehensive Web API that provides all the core music data.
-   **[Genius](https://genius.com)** for their vast, user-contributed library of song lyrics.
-   **[YouTube](https://youtube.com)** for providing music videos and audio streams.

---

## 📜 License

This project is licensed under the **GNU General Public License v3.0**.

See the [LICENSE](LICENSE) file for the full legal text.
