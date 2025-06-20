# Feature Deep Dive: Asynchronous Skeleton Loading & Self-Healing Cache

This document provides a technical explanation of the asynchronous data loading and "self-healing" cache architecture used in the Spotify Romanizer application.

### The Goal

To provide a modern, high-performance user experience where the user is never blocked by slow network operations. When a user navigates to a track page, the page should appear **instantly**, with the content populating seamlessly as it's fetched from external APIs in the background.

![Main Demo GIF](../assets/demo-main.gif)

### The Challenge

A single track page requires data from up to three different external APIs (Spotify, Genius, YouTube), plus a translation service. A traditional server-side rendering approach would force the user to wait for all four of these network calls to complete before seeing anything, resulting in a slow and frustrating experience. Furthermore, any one of these external services could fail, potentially crashing the request.

### The Implementation

The solution is a distributed, asynchronous architecture that decouples the user-facing web server from the slow data-fetching processes.

#### 1. The "Skeleton" Response (Flask Route)

- When a user requests `/track/<track_id>`, the Flask route first checks the Redis cache.
- **On a cache miss**, it does not perform any API calls. Instead, it immediately calls the `create_skeleton_cache_entry` service function.
- This function creates a dictionary containing all the necessary keys (`original_lyrics`, `youtube_url`, etc.) but fills them with placeholder values like `"Loading..."`.
- This "skeleton" data is saved to the cache, and the `track_info.html` template is rendered and returned to the user instantly. The template uses Jinja2 logic to display pulsing placeholder blocks (the skeleton UI) when it sees this placeholder data.

#### 2. Asynchronous Task Dispatch (Celery)

- Immediately after creating the skeleton entry, the Flask route dispatches the main background task to a Celery worker: `fetch_and_populate_task.delay(...)`.
- This returns control to the web server instantly, which finishes the user's request.

#### 3. Background Data Fetching (Celery Worker)

- A separate Celery worker process, which is always running, picks up the `fetch_and_populate_task` from the Redis message queue.
- This worker is responsible for performing all the slow, blocking API calls to Genius and YouTube.
- Once it has the data, it updates the existing cache entry for the track, replacing the "Loading..." placeholders with the real content.
- It also dispatches chained tasks for translation (`translate_and_update_cache_task`) and other operations, ensuring a clean, sequential workflow.

#### 4. Front-End Polling and UI Updates (JavaScript)

- The `track_info_page.js` script, upon loading, checks the HTML for `data-is-loading` attributes.
- If any content is marked as loading, it begins polling a status endpoint (`/api/track/status/<track_id>`) every few seconds.
- This API endpoint simply reads the current state of the track from the Redis cache.
- As the JavaScript receives updated data from the polling response, it dynamically updates the DOM: it replaces the skeleton placeholders with the real text, injects the YouTube `iframe`, and enables the appropriate lyric tabs.
- Once all expected content has been loaded, the polling stops.

#### 5. The "Self-Healing" Mechanism

- The system is designed to be resilient. If a user visits a track page that _is_ in the cache but has incomplete data (e.g., a previous translation task failed), the `track_details` route performs a "health check."
- It inspects the cached data. If it finds a field with a "failed" status or a missing value, it re-dispatches _only the specific Celery task_ needed to fix that piece of data (e.g., `translate_and_update_cache_task.delay(...)`).
- The front-end polling mechanism then takes over as usual, ensuring that the data will eventually become complete on subsequent visits.

### The Result

This architecture results in a lightning-fast perceived performance for the user and a highly resilient system that is not dependent on the uptime of its external APIs. It is a standard, professional pattern for building modern, scalable web applications.

---

[**« Back to Main README**](../README.md)
