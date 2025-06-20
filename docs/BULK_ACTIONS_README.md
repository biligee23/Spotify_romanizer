# Feature Deep Dive: Bulk Actions & Cache Priming

This document provides a technical explanation of the advanced bulk operations available in Spotify Romanizer, showcasing how the application handles multiple actions efficiently without compromising the user experience.

### The Goal

To empower users to manage large libraries efficiently. Users should be able to select multiple songs and perform a single action (like "Favorite" or "Add to Playlist") on all of them at once. Additionally, users should be able to pre-load all data for an entire playlist to ensure a fast offline or on-the-go experience.

### The Implementation

<table>
  <tr>
    <td width="50%">
      <center><strong>Efficient Bulk Actions</strong></center>
      <img src="../assets/demo-bulk-actions.gif" alt="Bulk Actions Demo" width="100%">
    </td>
    <td width="50%">
      <p><strong>Bulk Favoriting:</strong> When a user favorites multiple selected songs, the front-end gathers the `cache_key` for each song and sends them as an array to the <code>/api/favorites/add_bulk</code> endpoint. The back-end uses Redis's highly efficient `SADD` command to add all keys to the favorites set in a single operation. The front-end then updates the UI in real-time, moving the items from the "History" to the "Favorites" list without a page reload.</p>
      <p><strong>Duplicate-Free Adding:</strong> When adding to an existing playlist, the back-end service first fetches the IDs of all tracks currently in the playlist. It then filters the user's selection to ensure only new, unique tracks are sent to the Spotify API, preventing duplicates.</p>
    </td>
  </tr>
</table>

#### Bulk Cache Priming

This feature uses a robust, manually-tracked progress system to provide reliable feedback for a long-running, multi-task operation.

![Cache Priming Screenshot](../assets/demo-cache-priming.png)

1.  **Initiation:** The user clicks "Pre-load." The back-end API (`/api/playlist/prime_cache`) identifies all uncached tracks, generates a unique `job_id`, and initializes a progress counter in Redis (e.g., `SET priming:job:{job_id} 0`).
2.  **Dispatch:** It dispatches a `fetch_and_populate_task` for each uncached song, passing the `job_id` to every task.
3.  **Worker Progress:** As each Celery worker completes its task, it sends an `INCR` command to the job's progress key in Redis.
4.  **Front-End Polling:** The front-end polls a status endpoint (`/api/priming/status/<job_id>`) which simply reads the current value of the Redis counter. This value is used to update the progress bar, providing a reliable and direct measure of the job's progress.

### The Result

These features provide significant quality-of-life improvements for users managing large libraries, built on a foundation of efficient database operations and reliable asynchronous task management.

---
[**« Back to Main README**](../README.md)
