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
use tokio::io::AsyncReadExt;
use tauri::Manager;
use tauri::menu::{Menu, MenuItem};
use tauri::tray::{TrayIconBuilder, TrayIconEvent, MouseButton, MouseButtonState};
use souvlaki::{MediaControls, MediaMetadata, PlatformConfig, MediaPlayback, MediaPosition};

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
    let instance = Rusteer::new(&arl).await.map_err(|e| format!("Login failed: {}", e))?;
    let mut rusteer = state.0.lock().map_err(|e| e.to_string())?;
    *rusteer = Some(instance);
    Ok(true)
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
    controls.set_metadata(MediaMetadata {
        title: Some(&title),
        artist: Some(&artist),
        album: Some(&album),
        cover_url: cover_url.as_deref(),
        duration: duration_ms.map(|ms| std::time::Duration::from_millis(ms)),
    }).map_err(|e| format!("Failed to set media metadata: {:?}", e))
}

#[tauri::command]
async fn update_playback_state(
    playing: bool,
    position_ms: Option<u64>,
    state: tauri::State<'_, MediaState>,
) -> Result<(), String> {
    let mut controls = state.controls.lock().map_err(|e| e.to_string())?;
    let status = if playing { MediaPlayback::Playing { progress: position_ms.map(|ms| MediaPosition(std::time::Duration::from_millis(ms))) } } else { MediaPlayback::Paused { progress: position_ms.map(|ms| MediaPosition(std::time::Duration::from_millis(ms))) } };
    controls.set_playback(status).map_err(|e| format!("Failed to set playback state: {:?}", e))
}

fn get_rusteer(state: &RusteerState) -> Result<Rusteer, String> {
    let guard = state.0.lock().map_err(|e| e.to_string())?;
    guard.as_ref().cloned().ok_or_else(|| "Not logged in".to_string())
}

#[tauri::command]
async fn search_tracks(query: String, limit: u32, index: u32, state: tauri::State<'_, RusteerState>) -> Result<Vec<Track>, String> {
    let rusteer = get_rusteer(&state)?;
    rusteer.search_tracks(&query, limit, index).await.map_err(|e| e.to_string())
}

#[tauri::command]
async fn search_albums(query: String, limit: u32, index: u32, state: tauri::State<'_, RusteerState>) -> Result<Vec<Album>, String> {
    let rusteer = get_rusteer(&state)?;
    rusteer.search_albums(&query, limit, index).await.map_err(|e| e.to_string())
}

#[tauri::command]
async fn search_artists(query: String, limit: u32, index: u32, state: tauri::State<'_, RusteerState>) -> Result<Vec<Artist>, String> {
    let rusteer = get_rusteer(&state)?;
    rusteer.search_artists(&query, limit, index).await.map_err(|e| e.to_string())
}

#[tauri::command]
async fn search_playlists(query: String, limit: u32, index: u32, state: tauri::State<'_, RusteerState>) -> Result<Vec<Playlist>, String> {
    let rusteer = get_rusteer(&state)?;
    rusteer.search_playlists(&query, limit, index).await.map_err(|e| e.to_string())
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
async fn get_playlist(id: String, state: tauri::State<'_, RusteerState>) -> Result<Playlist, String> {
    let rusteer = get_rusteer(&state)?;
    rusteer.get_playlist(&id).await.map_err(|e| e.to_string())
}

#[tauri::command]
async fn get_artist_top_tracks(id: String, limit: u32, state: tauri::State<'_, RusteerState>) -> Result<Vec<Track>, String> {
    let rusteer = get_rusteer(&state)?;
    rusteer.get_artist_top_tracks(&id, limit).await.map_err(|e| e.to_string())
}

#[tauri::command]
async fn get_artist_albums(id: String, limit: u32, state: tauri::State<'_, RusteerState>) -> Result<Vec<Album>, String> {
    let rusteer = get_rusteer(&state)?;
    rusteer.get_artist_albums(&id, limit).await.map_err(|e| e.to_string())
}

#[tauri::command]
async fn get_track_radio(id: String, state: tauri::State<'_, RusteerState>) -> Result<Vec<Track>, String> {
    let rusteer = get_rusteer(&state)?;
    rusteer.get_track_radio(&id).await.map_err(|e| e.to_string())
}

struct SyncStreamReader {
    inner: tokio::io::ReadHalf<tokio::io::DuplexStream>,
    runtime: tokio::runtime::Handle,
}

impl std::io::Read for SyncStreamReader {
    fn read(&mut self, buf: &mut [u8]) -> std::io::Result<usize> {
        self.runtime.block_on(async { self.inner.read(buf).await })
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app_state = RusteerState(Arc::new(std::sync::Mutex::new(None)));
    #[cfg(not(target_os = "android"))]
    let config = PlatformConfig { dbus_name: "deeztracker_streaming", display_name: "Deeztracker Streaming", hwnd: None };
    #[cfg(not(target_os = "android"))]
    let mut controls = MediaControls::new(config).expect("Failed to create media controls");
    #[cfg(not(target_os = "android"))]
    let _ = controls.attach(|_| {});
    let media_state = MediaState { controls: Arc::new(std::sync::Mutex::new(controls)) };

    tauri::Builder::default()
        .manage(app_state).manage(media_state)
        .plugin(tauri_plugin_opener::init()).plugin(tauri_plugin_notification::init()).plugin(tauri_plugin_os::init())
        .setup(|app| {
            let quit_i = MenuItem::with_id(app, "quit", "Quit", true, None::<&str>)?;
            let show_i = MenuItem::with_id(app, "show", "Show", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&show_i, &quit_i])?;
            let _tray = TrayIconBuilder::new().icon(app.default_window_icon().unwrap().clone()).menu(&menu)
                .on_menu_event(|app, event| if event.id.as_ref() == "quit" { app.exit(0); } else if event.id.as_ref() == "show" {
                    if let Some(w) = app.get_webview_window("main") { let _ = w.show(); let _ = w.set_focus(); }
                })
                .on_tray_icon_event(|tray, event| {
                    if let TrayIconEvent::Click { button: MouseButton::Left, button_state: MouseButtonState::Up, .. } = event {
                        if let Some(w) = tray.app_handle().get_webview_window("main") { let _ = w.show(); let _ = w.set_focus(); }
                    }
                })
                .build(app)?;

            let rusteer_state = app.state::<RusteerState>().0.clone();
            let server = tiny_http::Server::http("127.0.0.1:0").map_err(|e| e.to_string())?;
            let port = match server.server_addr() { tiny_http::ListenAddr::IP(addr) => addr.port(), _ => 0 };
            let base_url = format!("http://localhost:{}", port);
            app.manage(StreamServerState { base_url });

            let runtime_handle = tokio::runtime::Handle::current();
            std::thread::spawn(move || {
                for request in server.incoming_requests() {
                    let url = request.url().to_string();
                    if url.starts_with("/stream/") {
                        let track_id = url.trim_start_matches("/stream/").to_string();
                        let state = rusteer_state.clone();
                        let handle = runtime_handle.clone();
                        let stream_res = handle.block_on(async move {
                            let guard = state.lock().ok()?;
                            if let Some(ref rusteer) = *guard { rusteer.stream_track(&track_id).await.ok() } else { None }
                        });
                        if let Some(res) = stream_res {
                            let reader = SyncStreamReader { inner: res.stream, runtime: handle };
                            let response = tiny_http::Response::new(
                                tiny_http::StatusCode(200),
                                vec![
                                    tiny_http::Header::from_bytes(&b"Content-Type"[..], &b"audio/mpeg"[..]).unwrap(),
                                    tiny_http::Header::from_bytes(&b"Access-Control-Allow-Origin"[..], &b"*"[..]).unwrap(),
                                ],
                                reader, None, None,
                            );
                            let _ = request.respond(response);
                        } else { let _ = request.respond(tiny_http::Response::from_string("Not Found").with_status_code(404)); }
                    } else { let _ = request.respond(tiny_http::Response::from_string("Not Found").with_status_code(404)); }
                }
            });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            login, search_tracks, search_albums, search_artists, search_playlists,
            get_album, get_artist, get_playlist, get_artist_top_tracks, get_artist_albums,
            get_track_radio, update_media_metadata, update_playback_state, get_streaming_base_url
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
