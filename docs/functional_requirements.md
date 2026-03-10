# Functional Requirements for Modern Streaming Player

## 1. Authentication
*   **User Login**: The application must allow the user to authenticate using a Deezer ARL token.
*   **Session Management**: The system must securely store the authentication state and maintain the session via the backend `RusteerState`.

## 2. Discovery & Search
*   **Global Search**: The user must be able to search for specific songs, albums, and artists.
*   **Contextual Browsing**: The user must be able to navigate to an Artist's page or an Album's page directly from a playing track or search result.

## 3. User Interface (UI) & Experience
*   **Now Playing Bar**: A persistent bar anchored at the bottom of the screen displaying current playback controls, progress, and volume.
*   **Track Metadata**: The UI must display the Title, Artist Name, and Album Art of the currently playing track.

## 4. Audio Playback
*   **Streaming Engine**: The system must support real-time audio playback by receiving decrypted byte chunks from the Rust backend via IPC channels.
*   **Core Controls**: The user must be able to Play, Pause, and Resume the audio stream.
*   **Track Navigation**: The user must be able to Skip to the Next track and Return to the Previous track.
*   **Seeking**: The user must be able to jump (seek) to a specific timestamp within the current track.
*   **Volume Control**: The user must be able to adjust the playback volume and mute/unmute the audio.

## 5. Queue & Playlist Management
*   **Up Next Queue**: The user must be able to view the list of upcoming tracks in the current play queue.
*   **Queue Manipulation**: The user must be able to add tracks to the end of the queue or play them immediately ("Play Next").
*   **Playback Modes**: The system must support Shuffle (randomized order) and Repeat modes (Repeat Track, Repeat All, Repeat Off).
*   **Local Custom Playlists**: The user must be able to create, edit, and save their own custom playlists locally within the application data.
*   **Auto-Queue Related Tracks**: When a track starts playing or the queue ends, the system should optionally queue related music automatically by querying the Deezer radio endpoint (`https://api.deezer.com/track/{track_id}/radio`).

## 6. Progress & Responsive Design
*   **Progress Indicator**: A visual progress bar showing the elapsed time and total duration of the current track.
*   **Responsive Design**: The application layout must adapt cleanly to different window sizes.
