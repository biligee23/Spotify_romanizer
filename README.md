# Japanese Song Lyrics Romanizer

![Project Banner](assets/banner.png)

This project was created as a personal tool to help me sing Japanese songs by providing romanized lyrics. While it's relatively easy to find romanized lyrics manually, I wanted to combine APIs from **Spotify**, **Genius**, and **YouTube** to create an all-in-one application that:

1. Searches for songs using Spotify.
2. Fetches lyrics from Genius.
3. Romanizes Japanese lyrics using `pykakasi` and `jaconv`.
4. Embeds YouTube videos for song playback (since Spotify API does not allow full song playback within applications).

---

## Features

- **Search Songs**: Use Spotify's API to search for songs and retrieve metadata like song title, artist name, and album cover.
- **Fetch Lyrics**: Retrieve lyrics for the selected song from Genius API.
- **Romanize Lyrics**: Convert Japanese lyrics into Romanized form using `pykakasi` and `jaconv`.
- **YouTube Playback**: Embed a YouTube video of the song for playback.
- **User-Friendly Interface**: A clean and responsive UI built with Bootstrap.

---

## Technologies Used

- **Backend**:

  - Flask (Python web framework)
  - Spotipy (Spotify API wrapper)
  - LyricsGenius (Genius API wrapper)
  - Pykakasi and Jaconv (Japanese text romanization)
  - Requests (HTTP requests to YouTube API)

- **Frontend**:

  - HTML5
  - CSS3 (Custom styles + Bootstrap)
  - JavaScript (Loader functionality)

- **APIs**:

  - Spotify API (Song search and metadata)
  - Genius API (Lyrics retrieval)
  - YouTube Data API (Video embedding)

- **Other Tools**:
  - Python-dotenv (Environment variable management)
  - Flask-Caching (Optional, for caching API responses)

---

## API Keys and Environment Variables

To run this application, you need to obtain API keys from the following services:

1. **Genius API**:

   - Register an app on the [Genius Developer Portal](https://genius.com/api-clients).
   - Obtain the `Access Token`.

2. **Spotify API**:

   - Register an app on the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications).
   - Obtain the `Client ID` and `Client Secret`.

3. **YouTube Data API**:
   - Enable the YouTube Data API in the [Google Cloud Console](https://console.cloud.google.com/).
   - Obtain the `API Key`.

---

## Dependencies

- Flask[async]==3.0.2
- spotipy==2.23.0
- pygame==2.6.1
- requests==2.32.3
- beautifulsoup4==4.13.3
- python-dotenv==1.0.1
- lyricsgenius==3.2.0
- jaconv==0.4.0
- pykakasi==2.3.0
- flask-session==0.8.0
- aiohttp==3.11.12

## Screenshots

![Spotify authentication](assets/authentication.png)
_Spotify user authentication_

![Search Page](assets/search.png)
_The search page allows users to find songs by title or artist._

![Track Details](assets/result.png)
_The track details page displays the album cover, romanized lyrics, and an embedded YouTube video._

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Disclaimer

This README includes screenshots of the application for demonstration purposes only. The album covers, YouTube thumbnails, and other media displayed are the property of their respective owners and are used here solely to illustrate the functionality of the application.
