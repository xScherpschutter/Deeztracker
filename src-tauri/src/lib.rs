// Rusteer Modules
pub mod api;
pub mod converters;
pub mod crypto;
pub mod error;
pub mod models;
mod rusteer;
pub mod tagging;

pub use api::{DeezerApi, GatewayApi};
pub use error::DeezerError;
pub use models::{Album, Artist, Playlist, Track};
pub use rusteer::{BatchDownloadResult, DownloadQuality, DownloadResult, Rusteer};

use std::sync::Arc;
use tauri::ipc::Channel;
use tokio::io::AsyncReadExt;
use tokio::sync::Mutex;

// Shared State to hold Rusteer instance
pub struct RusteerState(pub Arc<Mutex<Option<Rusteer>>>);

#[tauri::command]
async fn login(arl: String, state: tauri::State<'_, RusteerState>) -> Result<bool, String> {
    match Rusteer::new(&arl).await {
        Ok(instance) => {
            let mut rusteer = state.0.lock().await;
            *rusteer = Some(instance);
            Ok(true)
        }
        Err(e) => Err(format!("Login failed: {}", e)),
    }
}

#[tauri::command]
async fn stream_track(
    id: String,
    on_chunk: Channel<Vec<u8>>,
    state: tauri::State<'_, RusteerState>,
) -> Result<(), String> {
    // Acquire the lock, and clone the data if we need it (or stay locked if it's cheap).
    // Here we need mutable access or access to Rusteer instance.
    // stream_track only takes &self, so an active lock is fine, but streaming is async and long.
    // It is better to get the lock, ensure instance exists, and call stream_track.
    // The Rusteer instance handles the spawn under the hood, but returns a stream that we consume.
    let rusteer_guard = state.0.lock().await;
    let rusteer = rusteer_guard
        .as_ref()
        .ok_or_else(|| "Not logged in. Please call login first.".to_string())?;

    let mut stream_result = rusteer
        .stream_track(&id)
        .await
        .map_err(|e| format!("Failed to start stream: {}", e))?;

    // Drop the guard before entering the long-running while loop to keep state accessible
    drop(rusteer_guard);

    // Consume the stream chunk by chunk and push it over the IPC channel.
    let mut buffer = vec![0u8; 8192]; // 8KB chunks
    loop {
        match stream_result.stream.read(&mut buffer).await {
            Ok(0) => break, // EOF
            Ok(n) => {
                if on_chunk.send(buffer[..n].to_vec()).is_err() {
                    // Receiver closed the channel (frontend stopped listening)
                    break;
                }
            }
            Err(e) => {
                return Err(format!("Error reading stream: {}", e));
            }
        }
    }

    Ok(())
}

#[tauri::command]
async fn search_tracks(
    query: String,
    limit: u32,
    index: u32,
    state: tauri::State<'_, RusteerState>,
) -> Result<Vec<Track>, String> {
    let rusteer_guard = state.0.lock().await;
    let rusteer = rusteer_guard
        .as_ref()
        .ok_or_else(|| "Not logged in".to_string())?;

    rusteer
        .search_tracks(&query, limit, index)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
async fn search_albums(
    query: String,
    limit: u32,
    index: u32,
    state: tauri::State<'_, RusteerState>,
) -> Result<Vec<Album>, String> {
    let rusteer_guard = state.0.lock().await;
    let rusteer = rusteer_guard
        .as_ref()
        .ok_or_else(|| "Not logged in".to_string())?;

    rusteer
        .search_albums(&query, limit, index)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
async fn search_artists(
    query: String,
    limit: u32,
    index: u32,
    state: tauri::State<'_, RusteerState>,
) -> Result<Vec<Artist>, String> {
    let rusteer_guard = state.0.lock().await;
    let rusteer = rusteer_guard
        .as_ref()
        .ok_or_else(|| "Not logged in".to_string())?;

    rusteer
        .search_artists(&query, limit, index)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
async fn search_playlists(
    query: String,
    limit: u32,
    index: u32,
    state: tauri::State<'_, RusteerState>,
) -> Result<Vec<Playlist>, String> {
    let rusteer_guard = state.0.lock().await;
    let rusteer = rusteer_guard
        .as_ref()
        .ok_or_else(|| "Not logged in".to_string())?;

    rusteer
        .search_playlists(&query, limit, index)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
async fn get_album(
    id: String,
    state: tauri::State<'_, RusteerState>,
) -> Result<Album, String> {
    let rusteer_guard = state.0.lock().await;
    let rusteer = rusteer_guard
        .as_ref()
        .ok_or_else(|| "Not logged in".to_string())?;

    rusteer.get_album(&id).await.map_err(|e| e.to_string())
}

#[tauri::command]
async fn get_artist(
    id: String,
    state: tauri::State<'_, RusteerState>,
) -> Result<Artist, String> {
    let rusteer_guard = state.0.lock().await;
    let rusteer = rusteer_guard
        .as_ref()
        .ok_or_else(|| "Not logged in".to_string())?;

    rusteer.get_artist(&id).await.map_err(|e| e.to_string())
}

#[tauri::command]
async fn get_playlist(
    id: String,
    state: tauri::State<'_, RusteerState>,
) -> Result<Playlist, String> {
    let rusteer_guard = state.0.lock().await;
    let rusteer = rusteer_guard
        .as_ref()
        .ok_or_else(|| "Not logged in".to_string())?;

    rusteer.get_playlist(&id).await.map_err(|e| e.to_string())
}

#[tauri::command]
async fn get_artist_top_tracks(
    id: String,
    limit: u32,
    state: tauri::State<'_, RusteerState>,
) -> Result<Vec<Track>, String> {
    let rusteer_guard = state.0.lock().await;
    let rusteer = rusteer_guard
        .as_ref()
        .ok_or_else(|| "Not logged in".to_string())?;

    rusteer.get_artist_top_tracks(&id, limit).await.map_err(|e| e.to_string())
}

#[tauri::command]
async fn get_artist_albums(
    id: String,
    limit: u32,
    state: tauri::State<'_, RusteerState>,
) -> Result<Vec<Album>, String> {
    let rusteer_guard = state.0.lock().await;
    let rusteer = rusteer_guard
        .as_ref()
        .ok_or_else(|| "Not logged in".to_string())?;

    rusteer.get_artist_albums(&id, limit).await.map_err(|e| e.to_string())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app_state = RusteerState(Arc::new(Mutex::new(None)));

    tauri::Builder::default()
        .manage(app_state)
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_os::init())
        .invoke_handler(tauri::generate_handler![
            login,
            stream_track,
            search_tracks,
            search_albums,
            search_artists,
            search_playlists,
            get_album,
            get_artist,
            get_playlist,
            get_artist_top_tracks,
            get_artist_albums
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
