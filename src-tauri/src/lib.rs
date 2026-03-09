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

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app_state = RusteerState(Arc::new(Mutex::new(None)));

    tauri::Builder::default()
        .manage(app_state)
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![login, stream_track])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
