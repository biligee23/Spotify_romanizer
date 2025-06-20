# Feature Deep Dive: Bulk Actions & Cache Priming

This document provides a technical explanation of the advanced bulk operations available in Spotify Romanizer, showcasing how the application handles multiple actions efficiently without compromising the user experience.

### The Goal

To empower users to manage large libraries efficiently. Users should be able to select multiple songs and perform a single action (like "Favorite" or "Add to Playlist") on all of them at once. Additionally, users should be able to pre-load all data for an entire playlist to ensure a fast offline or on-the-go experience.

|                Efficient Bulk Actions                 |                    Live Progress Feedback                     |
| :---------------------------------------------------: | :-----------------------------------------------------------: |
| ![Bulk Actions Demo](../assets/demo-bulk-actions.gif) | ![Cache Priming Screenshot](../assets/demo-cache-priming.png) |

### The Challenge

Performing actions on dozens or hundreds of items at once can be very slow. A naive implementation would either lock up the user's browser or time out the web server request. The solution requires a combination of efficient back-end database operations and asynchronous background processing.

### The Implementation

#### 1. Bulk Favoriting / Unfavoriting

- **Front-End (UI & State):** The UI provides checkboxes for each song. A JavaScript function, `updateGlobalButtonStates`, tracks the number of selected items and enables/disables the bulk action buttons accordingly.
- **Front-End (Logic):** When a user clicks a bulk action button (e.g., "Favorite Selected"), a confirmation dialog is shown. If confirmed, the JavaScript collects the `cache_key` from the `data-cache-key` attribute of every selected song and sends this array of keys to a dedicated bulk API endpoint (e.g., `/api/favorites/add_bulk`).
- **Back-End (API & Service):** The API endpoint receives the list of keys and passes it to a service function like `add_to_favorites_bulk`.
- **Back-End (Database):** This is the key optimization. Instead of looping and calling Redis for each key, the service function uses Redis's ability to handle multiple members in a single command. It uses `SADD favorite_tracks key1 key2 key3...` to add all keys to the favorites set in one highly efficient operation. It then updates the cache timeouts for each item to make them permanent.
- **Result:** A highly performant bulk action that feels instant to the user, with a real-time UI update that moves the items between the "History" and "Favorites" lists without a page reload.

#### 2. Bulk Cache Priming

- **Front-End (Initiation):** The user clicks the "Pre-load All Lyrics" button on a playlist page. The JavaScript makes a `POST` request to the `/api/playlist/prime_cache/<playlist_id>` endpoint.
- **Back-End (Task Dispatch):** This API endpoint is the "mission control" for the bulk job.
  1.  It fetches the full track list for the playlist.
  2.  It filters out any tracks that are already in the cache to avoid redundant work.
  3.  It generates a unique **`job_id`** (using Python's `uuid` library).
  4.  It initializes a progress counter in Redis (e.g., `SET priming:job:{job_id} 0`).
  5.  It loops through the list of uncached tracks and dispatches a `fetch_and_populate_task` for each one, passing the `job_id` to every task.
  6.  It immediately returns the `job_id` and the `total_tasks` count to the front-end.
- **Back-End (Worker Task):** Each `fetch_and_populate_task` performs its work (fetching lyrics, etc.). In its `finally` block (which runs on both success and failure), it performs one final action: `redis.incr(priming:job:{job_id})`, incrementing the progress counter.
- **Front-End (Progress Tracking):** The JavaScript, having received the `job_id`, starts polling a status endpoint (`/api/priming/status/<job_id>`). This endpoint simply reads the current value from the progress counter in Redis. The front-end uses this value to update the width of the progress bar, providing clear, accurate, and real-time feedback to the user.
- **Result:** A robust, scalable system for handling long-running bulk operations. The user gets immediate feedback, can track the progress live, and the entire workload is handled efficiently by the background workers without impacting the main web application.

---

[**« Back to Main README**](../README.md)
