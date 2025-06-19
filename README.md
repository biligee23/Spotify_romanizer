# Spotify Romanizer

A web application that generates romanized lyrics for Japanese songs, built with Python, Flask, Redis, Docker, CSS, HTML, and JavaScript.

## Introduction

As a music enthusiast, I've often found myself struggling to find romanized lyrics for Japanese songs, especially for lesser-known tracks. This frustration sparked an idea - what if I could automate the process of generating romanized lyrics and create a clean, user-friendly interface to showcase them?

And so, Spotify Romanizer was born. I hope to demonstrate my skills and showcase the potential of this application to fellow music enthusiasts and developers alike.

## How it Works

Here's a step-by-step overview of how Spotify Romanizer generates romanized lyrics:

1. **Song Retrieval**: When a user searches for a song, the application queries the Spotify API to retrieve the song's metadata, including its title, artist, and album.
2. **Video Retrieval**: The application then uses the YouTube API to retrieve the song's music video, if available.
3. **Lyrics Retrieval**: The application uses a Genius API to retrieve the song's lyrics in Japanese.
4. **Romanization**: The application uses a romanization library (pykakasi) to convert the Japanese lyrics to their romanized equivalent.
5. **Storage**: The romanized lyrics are then stored in a Redis database using LRU caching, which stores the 20 most recently accessed songs.
6. **Cache Eviction**: When the cache reaches its limit, the least and oldest accessed song is evicted to make room for new songs. Additionalli, after 300 minutes, the entire system storage is cleared.

## Features

- **Clean UI**: A user-friendly interface that makes it easy to search and view songs.
- **Romanized Lyrics**: Semi-accurate romanization of Japanese lyrics for singing along. Some kanji's romanized forms are written as its wrong interpretation from the song.
- **Video Playback**: Embedded YouTube video playback for a seamless listening experience.

* **LRU Caching**: Stores the 20 most recently accessed songs for quick retrieval.

- **Search**: Users can search for songs by title, artist (Search is supported by Spotify API, so search how you would search a song using Spotify).

## Technologies Used

- **Python**: The application's backend is built using Python, with Flask as the web framework.
- **Redis**: Used for storing romanized lyrics and user favorites.
- **Docker**: Used for containerization and deployment.
- **CSS**: Used for styling the application's UI.
- **HTML**: Used for structuring the application's UI.
- **JavaScript**: Used for client-side scripting and interacting with the backend API.

## Installation

To run the application locally, follow these steps:

1. Clone the repository: `git clone https://github.com/biligee23/spotify-romanizer.git`
2. Navigate to the project directory: `cd spotify-romanizer`
3. Build the Docker image using Docker Compose: `docker-compose build`
4. Run the application using Docker Compose: `docker-compose up`

## Usage

1. Open a web browser and navigate to `http://localhost:5000`.
2. Search for a song by title, artist, or album.
3. View the song's romanized lyrics and video playback.

## License

This project is licensed under the MIT License.

## Acknowledgments

- **Spotify API**: For providing access to song metadata.
- **YouTube API**: For providing access to music videos.
- **Lyrics API**: For providing access to song lyrics.
- **Redis**: For providing a fast and efficient storage solution.
- **Docker**: For providing a containerization platform.

I hope you enjoy using Spotify Romanizer! If you have any feedback or suggestions, please don't hesitate to reach out.
