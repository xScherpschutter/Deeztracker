// Rusteer Modules
pub mod api;
pub mod converters;
pub mod crypto;
pub mod database;
pub mod error;
pub mod models;
mod rusteer;
pub mod tagging;

pub use api::{DeezerApi, GatewayApi};
pub use database::{DbState};
pub use error::DeezerError;
pub use models::{Album, Artist, Playlist, Track};
pub use rusteer::{BatchDownloadResult, DownloadQuality, DownloadResult, Rusteer};

use souvlaki::{MediaControls, MediaMetadata, MediaPlayback, MediaPosition, PlatformConfig};
use std::collections::HashMap;
use std::io::{Read, Seek, SeekFrom};
use std::path::PathBuf;
use std::sync::Arc;
use tauri::menu::{Menu, MenuItem};
use tauri::tray::TrayIconBuilder;
use tauri::Manager;
use tokio::io::AsyncReadExt;

// Shared State to hold Rusteer instance
pub struct RusteerState(pub Arc<std::sync::Mutex<Option<Rusteer>>>);

// Streaming Server State
pub struct StreamServerState {
    pub base_url: String,
}

#[tauri::command]
fn get_streaming_base_url(state: tauri::State<'_, StreamServerState>) -> String {
    state.base_url.clone()
}

#[tauri::command]
async fn login(arl: String, state: tauri::State<'_, RusteerState>) -> Result<bool, String> {
    let instance = Rusteer::new(&arl)
        .await
        .map_err(|e| format!("Login failed: {}", e))?;
    let mut rusteer = state.0.lock().map_err(|e| e.to_string())?;
    *rusteer = Some(instance);
    Ok(true)
}

#[tauri::command]
async fn is_premium(state: tauri::State<'_, RusteerState>) -> Result<bool, String> {
    let rusteer = get_rusteer(&state)?;
    Ok(rusteer.has_premium())
}

#[tauri::command]
async fn get_user_info(state: tauri::State<'_, RusteerState>) -> Result<serde_json::Value, String> {
    let rusteer = get_rusteer(&state)?;
    Ok(serde_json::json!({
        "is_premium": rusteer.has_premium(),
    }))
}

#[tauri::command]
async fn set_audio_quality(quality: String, state: tauri::State<'_, RusteerState>) -> Result<(), String> {
    let mut guard = state.0.lock().map_err(|e| e.to_string())?;
    let rusteer = guard.as_mut().ok_or_else(|| "Not logged in".to_string())?;
    
    let q = match quality.as_str() {
        "FLAC" => DownloadQuality::Flac,
        "MP3_320" => DownloadQuality::Mp3_320,
        "MP3_128" => DownloadQuality::Mp3_128,
        _ => return Err("Invalid quality".to_string()),
    };
    
    rusteer.set_quality(q);
    Ok(())
}

#[tauri::command]
async fn get_audio_quality(state: tauri::State<'_, RusteerState>) -> Result<String, String> {
    let rusteer = get_rusteer(&state)?;
    Ok(rusteer.quality().format().to_string())
}

// Media Controls State
pub struct MediaState {
    pub controls: Arc<std::sync::Mutex<MediaControls>>,
}

#[tauri::command]
async fn update_media_metadata(
    title: String,
    artist: String,
    album: String,
    cover_url: Option<String>,
    duration_ms: Option<u64>,
    state: tauri::State<'_, MediaState>,
) -> Result<(), String> {
    let mut controls = state.controls.lock().map_err(|e| e.to_string())?;
    controls
        .set_metadata(MediaMetadata {
            title: Some(&title),
            artist: Some(&artist),
            album: Some(&album),
            cover_url: cover_url.as_deref(),
            duration: duration_ms.map(|ms| std::time::Duration::from_millis(ms)),
        })
        .map_err(|e| format!("Failed to set media metadata: {:?}", e))
}

#[tauri::command]
async fn update_playback_state(
    playing: bool,
    position_ms: Option<u64>,
    state: tauri::State<'_, MediaState>,
) -> Result<(), String> {
    let mut controls = state.controls.lock().map_err(|e| e.to_string())?;
    let status = if playing {
        MediaPlayback::Playing {
            progress: position_ms.map(|ms| MediaPosition(std::time::Duration::from_millis(ms))),
        }
    } else {
        MediaPlayback::Paused {
            progress: position_ms.map(|ms| MediaPosition(std::time::Duration::from_millis(ms))),
        }
    };
    controls
        .set_playback(status)
        .map_err(|e| format!("Failed to set playback state: {:?}", e))
}

fn get_rusteer(state: &RusteerState) -> Result<Rusteer, String> {
    let guard = state.0.lock().map_err(|e| e.to_string())?;
    guard
        .as_ref()
        .cloned()
        .ok_or_else(|| "Not logged in".to_string())
}

#[tauri::command]
async fn search_tracks(
    query: String,
    limit: u32,
    index: u32,
    state: tauri::State<'_, RusteerState>,
) -> Result<Vec<Track>, String> {
    let rusteer = get_rusteer(&state)?;
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
    let rusteer = get_rusteer(&state)?;
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
    let rusteer = get_rusteer(&state)?;
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
    let rusteer = get_rusteer(&state)?;
    rusteer
        .search_playlists(&query, limit, index)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
async fn get_album(id: String, state: tauri::State<'_, RusteerState>) -> Result<Album, String> {
    let rusteer = get_rusteer(&state)?;
    rusteer.get_album(&id).await.map_err(|e| e.to_string())
}

#[tauri::command]
async fn get_artist(id: String, state: tauri::State<'_, RusteerState>) -> Result<Artist, String> {
    let rusteer = get_rusteer(&state)?;
    rusteer.get_artist(&id).await.map_err(|e| e.to_string())
}

#[tauri::command]
async fn get_playlist(
    id: String,
    state: tauri::State<'_, RusteerState>,
) -> Result<Playlist, String> {
    let rusteer = get_rusteer(&state)?;
    rusteer.get_playlist(&id).await.map_err(|e| e.to_string())
}

#[tauri::command]
async fn get_artist_top_tracks(
    id: String,
    limit: u32,
    state: tauri::State<'_, RusteerState>,
) -> Result<Vec<Track>, String> {
    let rusteer = get_rusteer(&state)?;
    rusteer
        .get_artist_top_tracks(&id, limit)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
async fn get_artist_albums(
    id: String,
    limit: u32,
    state: tauri::State<'_, RusteerState>,
) -> Result<Vec<Album>, String> {
    let rusteer = get_rusteer(&state)?;
    rusteer
        .get_artist_albums(&id, limit)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
async fn get_track_radio(
    id: String,
    state: tauri::State<'_, RusteerState>,
) -> Result<Vec<Track>, String> {
    let rusteer = get_rusteer(&state)?;
    rusteer
        .get_track_radio(&id)
        .await
        .map_err(|e| e.to_string())
}

/// Synchronous wrapper that reads from an async DuplexStream.
/// Used only during the initial download-to-tempfile phase.
struct SyncStreamReader {
    inner: tokio::io::ReadHalf<tokio::io::DuplexStream>,
    runtime: tokio::runtime::Handle,
}

impl std::io::Read for SyncStreamReader {
    fn read(&mut self, buf: &mut [u8]) -> std::io::Result<usize> {
        self.runtime.block_on(async { self.inner.read(buf).await })
    }
}

/// Parse a Range header value like "bytes=1234-" or "bytes=1234-5678"
/// Returns (start, optional_end).
fn parse_range_header(header_value: &str) -> Option<(u64, Option<u64>)> {
    let s = header_value.strip_prefix("bytes=")?;
    let mut parts = s.splitn(2, '-');
    let start_str = parts.next()?;
    let end_str = parts.next().unwrap_or("");

    let start: u64 = start_str.parse().ok()?;
    let end: Option<u64> = if end_str.is_empty() {
        None
    } else {
        end_str.parse().ok()
    };
    Some((start, end))
}

/// Download and decrypt a track into a temporary file, returning its path.
fn download_track_to_tempfile(
    track_id: &str,
    rusteer_state: &Arc<std::sync::Mutex<Option<Rusteer>>>,
    runtime: &tokio::runtime::Handle,
) -> Option<PathBuf> {
    let state = rusteer_state.clone();
    let tid = track_id.to_string();
    let stream_res = runtime.block_on(async move {
        let guard = state.lock().ok()?;
        if let Some(ref rusteer) = *guard {
            rusteer.stream_track(&tid).await.ok()
        } else {
            None
        }
    })?;

    let tmp_path = std::env::temp_dir().join(format!("deeztracker_{}.mp3", track_id));
    let mut file = std::fs::File::create(&tmp_path).ok()?;
    let mut reader = SyncStreamReader {
        inner: stream_res.stream,
        runtime: runtime.clone(),
    };
    std::io::copy(&mut reader, &mut file).ok()?;
    Some(tmp_path)
}

/// Serve a cached file responding to an HTTP request, supporting Range headers.
fn serve_file_request(request: tiny_http::Request, file_path: &PathBuf) {
    let file_len = match std::fs::metadata(file_path) {
        Ok(m) => m.len(),
        Err(_) => {
            let _ = request
                .respond(tiny_http::Response::from_string("File Error").with_status_code(500));
            return;
        }
    };

    // Check for Range header
    let range_header = request
        .headers()
        .iter()
        .find(|h| h.field.as_str().to_string().to_lowercase() == "range")
        .map(|h| h.value.as_str().to_string());

    if let Some(ref range_val) = range_header {
        if let Some((start, end_opt)) = parse_range_header(range_val) {
            let end = end_opt.unwrap_or(file_len - 1).min(file_len - 1);
            let chunk_len = end - start + 1;

            let mut file = match std::fs::File::open(file_path) {
                Ok(f) => f,
                Err(_) => {
                    let _ = request.respond(
                        tiny_http::Response::from_string("File Error").with_status_code(500),
                    );
                    return;
                }
            };
            if file.seek(SeekFrom::Start(start)).is_err() {
                let _ = request
                    .respond(tiny_http::Response::from_string("Seek Error").with_status_code(500));
                return;
            }
            let limited_reader = file.take(chunk_len);

            let content_range = format!("bytes {}-{}/{}", start, end, file_len);
            let response = tiny_http::Response::new(
                tiny_http::StatusCode(206),
                vec![
                    tiny_http::Header::from_bytes(&b"Content-Type"[..], &b"audio/mpeg"[..])
                        .unwrap(),
                    tiny_http::Header::from_bytes(&b"Access-Control-Allow-Origin"[..], &b"*"[..])
                        .unwrap(),
                    tiny_http::Header::from_bytes(&b"Accept-Ranges"[..], &b"bytes"[..]).unwrap(),
                    tiny_http::Header::from_bytes(&b"Content-Range"[..], content_range.as_bytes())
                        .unwrap(),
                    tiny_http::Header::from_bytes(
                        &b"Content-Length"[..],
                        chunk_len.to_string().as_bytes(),
                    )
                    .unwrap(),
                ],
                limited_reader,
                Some(chunk_len as usize),
                None,
            );
            let _ = request.respond(response);
            return;
        }
    }

    // No Range header — serve the full file
    let file = match std::fs::File::open(file_path) {
        Ok(f) => f,
        Err(_) => {
            let _ = request
                .respond(tiny_http::Response::from_string("File Error").with_status_code(500));
            return;
        }
    };
    let response = tiny_http::Response::new(
        tiny_http::StatusCode(200),
        vec![
            tiny_http::Header::from_bytes(&b"Content-Type"[..], &b"audio/mpeg"[..]).unwrap(),
            tiny_http::Header::from_bytes(&b"Access-Control-Allow-Origin"[..], &b"*"[..]).unwrap(),
            tiny_http::Header::from_bytes(&b"Accept-Ranges"[..], &b"bytes"[..]).unwrap(),
            tiny_http::Header::from_bytes(&b"Content-Length"[..], file_len.to_string().as_bytes())
                .unwrap(),
        ],
        file,
        Some(file_len as usize),
        None,
    );
    let _ = request.respond(response);
}

#[tauri::command]
async fn get_charts(state: tauri::State<'_, RusteerState>) -> Result<serde_json::Value, String> {
    let _ = get_rusteer(&state)?;
    // We reuse the public API client inside Rusteer
    let api = DeezerApi::new();
    let charts = api.get_charts().await.map_err(|e| e.to_string())?;
    
    // Process the charts to convert them to our structured models
    let mut processed_charts = serde_json::json!({
        "tracks": [],
        "albums": [],
        "artists": [],
        "playlists": []
    });

    if let Some(tracks) = charts.get("tracks").and_then(|t| t.get("data")).and_then(|d| d.as_array()) {
        processed_charts["tracks"] = serde_json::Value::Array(
            tracks.iter().filter_map(|t| converters::parse_track(t).ok()).map(|t| serde_json::to_value(t).unwrap()).collect()
        );
    }

    if let Some(albums) = charts.get("albums").and_then(|a| a.get("data")).and_then(|d| d.as_array()) {
        processed_charts["albums"] = serde_json::Value::Array(
            albums.iter().filter_map(|a| converters::parse_album(a).ok()).map(|a| serde_json::to_value(a).unwrap()).collect()
        );
    }

    if let Some(artists) = charts.get("artists").and_then(|a| a.get("data")).and_then(|d| d.as_array()) {
        processed_charts["artists"] = serde_json::Value::Array(
            artists.iter().filter_map(|a| converters::parse_artist(a).ok()).map(|a| serde_json::to_value(a).unwrap()).collect()
        );
    }

    if let Some(playlists) = charts.get("playlists").and_then(|p| p.get("data")).and_then(|d| d.as_array()) {
        processed_charts["playlists"] = serde_json::Value::Array(
            playlists.iter().filter_map(|p| converters::parse_playlist(p).ok()).map(|p| serde_json::to_value(p).unwrap()).collect()
        );
    }

    Ok(processed_charts)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app_state = RusteerState(Arc::new(std::sync::Mutex::new(None)));
    #[cfg(not(target_os = "android"))]
    let config = PlatformConfig {
        dbus_name: "deeztracker_streaming",
        display_name: "Deeztracker Streaming",
        hwnd: None,
    };
    #[cfg(not(target_os = "android"))]
    let mut controls = MediaControls::new(config).expect("Failed to create media controls");
    #[cfg(not(target_os = "android"))]
    let _ = controls.attach(|_| {});
    let media_state = MediaState {
        controls: Arc::new(std::sync::Mutex::new(controls)),
    };

    tauri::Builder::default()
        .manage(app_state)
        .manage(media_state)
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_os::init())
        .setup(|app| {
            // Initialize Database
            let app_data_dir = app.path().app_data_dir().expect("Failed to get app data dir");
            let conn = database::init(app_data_dir).expect("Failed to initialize database");
            app.manage(database::DbState(std::sync::Mutex::new(conn)));

            let quit_i = MenuItem::with_id(app, "quit", "Quit", true, None::<&str>)?;
            let show_i = MenuItem::with_id(app, "show", "Show", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&show_i, &quit_i])?;
            let _tray = TrayIconBuilder::new()
                .icon(app.default_window_icon().unwrap().clone())
                .menu(&menu)
                .on_menu_event(|app, event| {
                    if event.id.as_ref() == "quit" {
                        app.exit(0);
                    } else if event.id.as_ref() == "show" {
                        if let Some(w) = app.get_webview_window("main") {
                            let _ = w.show();
                            let _ = w.set_focus();
                        }
                    }
                })
                .on_tray_icon_event(|tray, event| {
                    use tauri::tray::{MouseButton, MouseButtonState, TrayIconEvent};
                    if let TrayIconEvent::Click {
                        button: MouseButton::Left,
                        button_state: MouseButtonState::Up,
                        ..
                    } = event
                    {
                        if let Some(w) = tray.app_handle().get_webview_window("main") {
                            let _ = w.show();
                            let _ = w.set_focus();
                        }
                    }
                })
                .build(app)?;

            let rusteer_state = app.state::<RusteerState>().0.clone();
            let server = tiny_http::Server::http("127.0.0.1:0").map_err(|e| e.to_string())?;
            let port = match server.server_addr() {
                tiny_http::ListenAddr::IP(addr) => addr.port(),
                _ => 0,
            };
            let base_url = format!("http://localhost:{}", port);
            app.manage(StreamServerState { base_url });

            let runtime_handle = tokio::runtime::Handle::current();
            std::thread::spawn(move || {
                // Cache: track_id -> path to temp file with decrypted audio
                let file_cache: Arc<std::sync::Mutex<HashMap<String, PathBuf>>> =
                    Arc::new(std::sync::Mutex::new(HashMap::new()));

                for request in server.incoming_requests() {
                    let url = request.url().to_string();
                    if url.starts_with("/stream/") {
                        let track_id = url.trim_start_matches("/stream/").to_string();
                        let state = rusteer_state.clone();
                        let handle = runtime_handle.clone();
                        let cache = file_cache.clone();

                        std::thread::spawn(move || {
                            // Check cache first
                            let cached_path = {
                                let guard = cache.lock().unwrap();
                                guard.get(&track_id).cloned()
                            };

                            if let Some(path) = cached_path {
                                // File already cached — serve directly (supports Range)
                                if path.exists() {
                                    serve_file_request(request, &path);
                                    return;
                                }
                                // File was deleted, remove from cache
                                let mut guard = cache.lock().unwrap();
                                guard.remove(&track_id);
                            }

                            // Download + decrypt to temp file
                            if let Some(tmp_path) =
                                download_track_to_tempfile(&track_id, &state, &handle)
                            {
                                // Clean up old cached files (keep only the current track)
                                {
                                    let mut guard = cache.lock().unwrap();
                                    let old_keys: Vec<String> = guard.keys().cloned().collect();
                                    for old_key in old_keys {
                                        if let Some(old_path) = guard.remove(&old_key) {
                                            let _ = std::fs::remove_file(&old_path);
                                        }
                                    }
                                    guard.insert(track_id.clone(), tmp_path.clone());
                                }
                                serve_file_request(request, &tmp_path);
                            } else {
                                let _ = request.respond(
                                    tiny_http::Response::from_string("Not Found")
                                        .with_status_code(404),
                                );
                            }
                        });
                    } else {
                        let _ = request.respond(
                            tiny_http::Response::from_string("Not Found").with_status_code(404),
                        );
                    }
                }
            });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            login,
            is_premium,
            get_user_info,
            set_audio_quality,
            get_audio_quality,
            search_tracks,
            search_albums,
            search_artists,
            search_playlists,
            get_album,
            get_artist,
            get_playlist,
            get_artist_top_tracks,
            get_artist_albums,
            get_track_radio,
            update_media_metadata,
            update_playback_state,
            get_streaming_base_url,
            get_charts,
            api::lyrics::get_lyrics,
            database::toggle_favorite,
            database::get_favorites,
            database::is_favorite,
            database::create_playlist,
            database::delete_playlist,
            database::get_playlists,
            database::add_track_to_playlist,
            database::remove_track_from_playlist,
            database::get_playlist_tracks
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
