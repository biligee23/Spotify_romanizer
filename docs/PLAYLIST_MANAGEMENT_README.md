# Feature Deep Dive: Advanced Playlist Management

This document provides a technical explanation of the advanced playlist management features in Spotify Romanizer, including drag-and-drop reordering for both tracks and the main playlist list.

### The Goal

To provide users with a powerful and intuitive interface for organizing their music that surpasses the standard functionality of the official Spotify client. All actions should feel seamless and update the UI in real-time without page reloads.

### The Challenge

Implementing drag-and-drop requires careful coordination between the front-end UI and the back-end API. Furthermore, the Spotify API has specific and different rules for reordering tracks *within* a playlist versus reordering the playlists themselves.

1.  **Track Reordering:** The API requires the `oldIndex` and `newIndex` of the moved track to calculate the final position. This calculation must account for the list shifting after the item is conceptually removed.
2.  **Playlist List Reordering:** The Spotify API **does not support** reordering a user's main list of playlists. This feature must be implemented as a custom, app-specific layer of personalization.

### The Implementation

<table>
  <tr>
    <td width="50%">
      <p><strong>Seamless Drag & Drop</strong></p>
      <p></p>
      <img src="../assets/drag_drop.gif" alt="Playlist Management Demo" width="100%">
    </td>
    <td width="50%">
      <p>The entire reordering experience is handled by the <strong>SortableJS</strong> library on the front-end and dedicated API endpoints on the back-end.</p>
      <p><strong>Track Reordering:</strong> When a track is dropped, the front-end sends the `oldIndex` and `newIndex` to the <code>/api/playlist/reorder_items</code> endpoint. The Flask back-end contains the critical logic to calculate the correct `insert_before` parameter for the Spotify API, ensuring the change is persisted correctly. It also fetches the new cover art and returns it for a live UI update.</p>
      <p><strong>Custom Playlist Order:</strong> When a playlist card is dropped, the front-end sends the *entire new array* of playlist IDs to the <code>/api/playlists/save_order</code> endpoint. The back-end saves this ordered list to Redis, keyed by the user's Spotify ID. On subsequent page loads, this custom order is used to sort the playlists retrieved from Spotify.</p>
    </td>
  </tr>
</table>

### The Result

This implementation provides two distinct but powerful organizational tools. Track reordering is perfectly synchronized with Spotify, while playlist reordering offers a unique, persistent, and valuable customization layer within the application itself.

---
[**« Back to Main README**](../README.md)
