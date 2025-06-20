# Feature Deep Dive: Advanced Playlist Management

This document provides a technical explanation of the advanced playlist management features in Spotify Romanizer, including drag-and-drop reordering for both tracks and the main playlist list.

### The Goal

To provide users with a powerful and intuitive interface for organizing their music that surpasses the standard functionality of the official Spotify client. All actions should feel seamless and update the UI in real-time without page reloads.

![Playlist Management Demo](../assets/demo-playlist-management.gif)

### The Challenge

Implementing drag-and-drop requires careful coordination between the front-end UI and the back-end API. Furthermore, the Spotify API has specific and different rules for reordering tracks _within_ a playlist versus reordering the playlists themselves.

1.  **Track Reordering:** The API requires the `oldIndex` and `newIndex` of the moved track to calculate the final position. This calculation must account for the list shifting after the item is conceptually removed.
2.  **Playlist List Reordering:** The Spotify API **does not support** reordering a user's main list of playlists. This feature must be implemented as a custom, app-specific layer of personalization.

### The Implementation

#### 1. Track Reordering (Inside a Playlist)

- **Front-End (UI):** The `SortableJS` library is initialized on the track list container (`#playlist-track-list`) in `playlist_details.html`.
- **Front-End (Logic):** The `onEnd` event callback in `playlist_reorder.js` captures the `oldIndex` and `newIndex` of the dropped track. It sends these two indices to a dedicated API endpoint.
- **Back-End (API Endpoint):** The `POST /api/playlist/reorder_items` route in `routes.py` receives the indices. It contains the critical logic to correctly calculate the `insert_before` parameter required by Spotify, accounting for whether the track was moved up or down the list (`if old_index < new_index: insert_before = new_index + 1`).
- **Back-End (Service):** The route calls the `reorder_playlist_items` service function, which executes the `playlist_reorder_items` command via `spotipy`. After a successful reorder, it makes a second, quick call to fetch the playlist's updated cover art (as it may have changed) and returns this new URL in the response.
- **Result:** The UI updates optimistically, and the back-end call ensures the change is persisted to Spotify. The front-end then uses the returned `new_image_url` to update the page's theme in real-time.

#### 2. Custom Playlist Order

- **Front-End (UI):** `SortableJS` is initialized on the main playlist grid container (`#playlist-grid`) in `playlists.html`.
- **Front-End (Logic):** When a user drops a playlist card, the `onEnd` callback in `playlist_reorder.js` iterates through _all_ the playlist cards in the grid in their new order. It builds an array of `playlist_id`s from the `data-playlist-id` attributes.
- **Back-End (API Endpoint):** The front-end sends this complete, ordered array of IDs to the `POST /api/playlists/save_order` endpoint.
- **Back-End (Service & Data Store):** The `save_user_playlist_order` service function receives this list. It gets the current user's unique Spotify ID and uses it to create a key (e.g., `user:USER_ID:playlist_order`). It then saves the entire ordered list of IDs to this key in the **Redis database**.
- **Data Loading Logic:** When the `/playlists` page is loaded, the `get_user_playlists` service function first fetches the playlists from Spotify, then fetches the user's custom order list from Redis. It then re-sorts the Spotify data in memory to match the custom order before returning it to be rendered.
- **Result:** A persistent, personalized playlist view that is unique to the user's experience within Spotify Romanizer, providing a valuable feature that Spotify itself lacks.

---

[**« Back to Main README**](../README.md)
