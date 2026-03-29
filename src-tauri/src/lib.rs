// Rusteer Modules
pub mod api;
pub mod audio_player;
pub mod converters;
pub mod crypto;
pub mod database;
pub mod error;
pub mod models;
mod rusteer;
pub mod tagging;

pub use api::{DeezerApi, GatewayApi};
pub use database::DbState;
pub use error::DeezerError;
pub use models::{Album, Artist, Playlist, Track};
pub use rusteer::{BatchDownloadResult, DownloadQuality, DownloadResult, Rusteer, BatchProgress, DownloadProgress};

use souvlaki::{MediaControls, MediaMetadata, MediaPlayback, MediaPosition, PlatformConfig};
use std::sync::Arc;
use tauri::menu::{Menu, MenuItem};
use tauri::tray::TrayIconBuilder;
use tauri::{Manager, Emitter};
use tauri_plugin_autostart::ManagerExt;

// Shared State to hold Rusteer instance
pub struct RusteerState(pub Arc<std::sync::Mutex<Option<Rusteer>>>);

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
async fn set_audio_quality(
    quality: String,
    state: tauri::State<'_, RusteerState>,
) -> Result<(), String> {
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

pub struct MediaState {
    pub controls: Arc<std::sync::Mutex<Option<MediaControls>>>,
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
    let mut guard = state.controls.lock().map_err(|e| e.to_string())?;
    if let Some(controls) = guard.as_mut() {
        controls
            .set_metadata(MediaMetadata {
                title: Some(&title),
                artist: Some(&artist),
                album: Some(&album),
                cover_url: cover_url.as_deref(),
                duration: duration_ms.map(|ms| std::time::Duration::from_millis(ms)),
            })
            .map_err(|e| format!("Failed to set media metadata: {:?}", e))?;
    }
    Ok(())
}

#[tauri::command]
async fn update_playback_state(
    playing: bool,
    position_ms: Option<u64>,
    state: tauri::State<'_, MediaState>,
) -> Result<(), String> {
    let mut guard = state.controls.lock().map_err(|e| e.to_string())?;
    if let Some(controls) = guard.as_mut() {
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
            .map_err(|e| format!("Failed to set playback state: {:?}", e))?;
    }
    Ok(())
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
async fn get_track(id: String, state: tauri::State<'_, RusteerState>) -> Result<Track, String> {
    let rusteer = get_rusteer(&state)?;
    rusteer.get_track(&id).await.map_err(|e| e.to_string())
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

#[tauri::command]
async fn get_autostart(app: tauri::AppHandle) -> Result<bool, String> {
    app.autolaunch().is_enabled().map_err(|e| e.to_string())
}

#[tauri::command]
async fn set_autostart(app: tauri::AppHandle, enabled: bool) -> Result<(), String> {
    let manager = app.autolaunch();
    if enabled {
        manager.enable().map_err(|e| e.to_string())
    } else {
        manager.disable().map_err(|e| e.to_string())
    }
}

#[tauri::command]
async fn update_tray_menu(
    app: tauri::AppHandle,
    toggle: String,
    next: String,
    prev: String,
    show: String,
    quit: String,
) -> Result<(), String> {
    let toggle_i = MenuItem::with_id(&app, "toggle", toggle, true, None::<&str>).map_err(|e| e.to_string())?;
    let next_i = MenuItem::with_id(&app, "next", next, true, None::<&str>).map_err(|e| e.to_string())?;
    let prev_i = MenuItem::with_id(&app, "prev", prev, true, None::<&str>).map_err(|e| e.to_string())?;
    let show_i = MenuItem::with_id(&app, "show", show, true, None::<&str>).map_err(|e| e.to_string())?;
    let quit_i = MenuItem::with_id(&app, "quit", quit, true, None::<&str>).map_err(|e| e.to_string())?;
    
    let menu = Menu::with_items(&app, &[
        &toggle_i, 
        &next_i, 
        &prev_i, 
        &tauri::menu::PredefinedMenuItem::separator(&app).map_err(|e| e.to_string())?,
        &show_i, 
        &quit_i
    ]).map_err(|e| e.to_string())?;

    if let Some(tray) = app.tray_by_id("main_tray") {
        let _ = tray.set_menu(Some(menu));
    }
    Ok(())
    }

    #[tauri::command]
    async fn get_downloads_dir(app: tauri::AppHandle) -> Result<String, String> {

    let mut path = app.path().audio_dir().map_err(|e| e.to_string())?;
    path.push("Deeztracker");
    if !path.exists() {
        let _ = std::fs::create_dir_all(&path);
    }
    Ok(path.to_string_lossy().to_string())
}

async fn internal_download_track(
    rusteer: Rusteer,
    track_id: String,
    output_dir: std::path::PathBuf,
    app: tauri::AppHandle,
) -> Result<(), String> {
    let res = rusteer.download_track_with_events(&track_id, &output_dir, &app).await.map_err(|e| e.to_string())?;
    
    let track = rusteer.get_track(&track_id).await.map_err(|e| e.to_string())?;
    let metadata = serde_json::to_string(&track).unwrap();
    
    let db = app.state::<DbState>();
    database::add_download_record(
        track_id.clone(),
        res.path.to_string_lossy().to_string(),
        res.quality.format().to_string(),
        metadata,
        db
    ).await?;

    // Emit completed event AFTER DB is updated
    app.emit("download-progress", DownloadProgress {
        track_id,
        status: "completed".to_string(),
        error: None,
    }).unwrap_or_default();

    Ok(())
}

#[tauri::command]
async fn download_track_node(
    track_id: String,
    app: tauri::AppHandle,
    state: tauri::State<'_, RusteerState>,
) -> Result<(), String> {
    let rusteer = get_rusteer(&state)?;
    let output_dir_str = get_downloads_dir(app.clone()).await?;
    let output_dir = std::path::PathBuf::from(output_dir_str);

    internal_download_track(rusteer, track_id, output_dir, app).await
}

#[tauri::command]
async fn download_album_node(
    album_id: String,
    app: tauri::AppHandle,
    state: tauri::State<'_, RusteerState>,
) -> Result<(), String> {
    let rusteer = get_rusteer(&state)?;
    let album = rusteer.get_album(&album_id).await.map_err(|e| e.to_string())?;
    let output_dir_str = get_downloads_dir(app.clone()).await?;
    let mut album_dir = std::path::PathBuf::from(output_dir_str);
    
    // Create album subdirectory
    let safe_artist = album.artists.first().map(|a| a.name.clone()).unwrap_or_else(|| "Unknown".to_string());
    let folder_name = format!("{} - {}", safe_artist, album.title).replace(['/', '\\', ':', '*', '?', '"', '<', '>', '|'], "_");
    album_dir.push(folder_name);
    let _ = std::fs::create_dir_all(&album_dir);

    let mut track_ids = Vec::new();
    for track in album.tracks {
        if let Some(tid) = track.ids.deezer {
            track_ids.push(tid);
        }
    }

    let total = track_ids.len();
    let current = std::sync::Arc::new(std::sync::Mutex::new(0));
    let failed = std::sync::Arc::new(std::sync::Mutex::new(0));

    for tid in track_ids {
        let r_clone = rusteer.clone();
        let a_clone = app.clone();
        let dir_clone = album_dir.clone();
        let c_clone = current.clone();
        let f_clone = failed.clone();
        
        tokio::spawn(async move {
            match internal_download_track(r_clone, tid, dir_clone, a_clone.clone()).await {
                Ok(_) => {
                    let mut c = c_clone.lock().unwrap();
                    *c += 1;
                }
                Err(_) => {
                    let mut f = f_clone.lock().unwrap();
                    *f += 1;
                    let mut c = c_clone.lock().unwrap();
                    *c += 1;
                }
            }
            
            a_clone.emit("batch-progress", BatchProgress {
                total,
                current: *c_clone.lock().unwrap(),
                failed: *f_clone.lock().unwrap(),
            }).unwrap_or_default();
        });
    }

    Ok(())
}

#[tauri::command]
async fn download_playlist_node(
    playlist_id: String,
    app: tauri::AppHandle,
    state: tauri::State<'_, RusteerState>,
) -> Result<(), String> {
    let rusteer = get_rusteer(&state)?;
    let playlist = rusteer.get_playlist(&playlist_id).await.map_err(|e| e.to_string())?;
    let output_dir_str = get_downloads_dir(app.clone()).await?;
    let mut playlist_dir = std::path::PathBuf::from(output_dir_str);
    
    let folder_name = format!("Playlist - {}", playlist.title).replace(['/', '\\', ':', '*', '?', '"', '<', '>', '|'], "_");
    playlist_dir.push(folder_name);
    let _ = std::fs::create_dir_all(&playlist_dir);

    let mut track_ids = Vec::new();
    for track in playlist.tracks {
        if let Some(tid) = track.ids.deezer {
            track_ids.push(tid);
        }
    }

    let total = track_ids.len();
    let current = std::sync::Arc::new(std::sync::Mutex::new(0));
    let failed = std::sync::Arc::new(std::sync::Mutex::new(0));

    for tid in track_ids {
        let r_clone = rusteer.clone();
        let a_clone = app.clone();
        let dir_clone = playlist_dir.clone();
        let c_clone = current.clone();
        let f_clone = failed.clone();
        
        tokio::spawn(async move {
            match internal_download_track(r_clone, tid, dir_clone, a_clone.clone()).await {
                Ok(_) => {
                    let mut c = c_clone.lock().unwrap();
                    *c += 1;
                }
                Err(_) => {
                    let mut f = f_clone.lock().unwrap();
                    *f += 1;
                    let mut c = c_clone.lock().unwrap();
                    *c += 1;
                }
            }
            
            a_clone.emit("batch-progress", BatchProgress {
                total,
                current: *c_clone.lock().unwrap(),
                failed: *f_clone.lock().unwrap(),
            }).unwrap_or_default();
        });
    }

    Ok(())
}

#[tauri::command]
async fn cancel_all_downloads(state: tauri::State<'_, RusteerState>) -> Result<(), String> {
    let guard = state.0.lock().map_err(|e| e.to_string())?;
    if let Some(rusteer) = guard.as_ref() {
        rusteer.cancel_token.cancel();
    }
    Ok(())
}

#[tauri::command]
async fn get_charts(state: tauri::State<'_, RusteerState>) -> Result<serde_json::Value, String> {
    let _ = get_rusteer(&state)?;
    let api = DeezerApi::new();
    let charts = api.get_charts().await.map_err(|e| e.to_string())?;

    let mut processed_charts = serde_json::json!({
        "tracks": [],
        "albums": [],
        "artists": [],
        "playlists": []
    });

    if let Some(tracks) = charts
        .get("tracks")
        .and_then(|t| t.get("data"))
        .and_then(|d| d.as_array())
    {
        processed_charts["tracks"] = serde_json::Value::Array(
            tracks
                .iter()
                .filter_map(|t| converters::parse_track(t).ok())
                .map(|t| serde_json::to_value(t).unwrap())
                .collect(),
        );
    }

    if let Some(albums) = charts
        .get("albums")
        .and_then(|a| a.get("data"))
        .and_then(|d| d.as_array())
    {
        processed_charts["albums"] = serde_json::Value::Array(
            albums
                .iter()
                .filter_map(|a| converters::parse_album(a).ok())
                .map(|a| serde_json::to_value(a).unwrap())
                .collect(),
        );
    }

    if let Some(artists) = charts
        .get("artists")
        .and_then(|a| a.get("data"))
        .and_then(|d| d.as_array())
    {
        processed_charts["artists"] = serde_json::Value::Array(
            artists
                .iter()
                .filter_map(|a| converters::parse_artist(a).ok())
                .map(|a| serde_json::to_value(a).unwrap())
                .collect(),
        );
    }

    if let Some(playlists) = charts
        .get("playlists")
        .and_then(|p| p.get("data"))
        .and_then(|d| d.as_array())
    {
        processed_charts["playlists"] = serde_json::Value::Array(
            playlists
                .iter()
                .filter_map(|p| converters::parse_playlist(p).ok())
                .map(|p| serde_json::to_value(p).unwrap())
                .collect(),
        );
    }

    Ok(processed_charts)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app_state = RusteerState(Arc::new(std::sync::Mutex::new(None)));

    tauri::Builder::default()
        .manage(app_state)
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_os::init())
        .plugin(tauri_plugin_autostart::init(
            tauri_plugin_autostart::MacosLauncher::LaunchAgent,
            None,
        ))
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                let _ = window.hide();
                api.prevent_close();
            }
        })
        .setup(|app| {
            // Initialize Media State (always manage it to avoid crashes in commands)
            let media_state = MediaState {
                controls: Arc::new(std::sync::Mutex::new(None)),
            };
            let media_controls_ref = media_state.controls.clone();
            app.manage(media_state);

            // Initialize Media Controls (Souvlaki)
            #[cfg(not(target_os = "android"))]
            {
                use tauri::Manager;
                
                let window = app.get_webview_window("main");
                let hwnd = if let Some(_w) = window {
                    #[cfg(target_os = "windows")]
                    {
                        _w.hwnd().ok().map(|h| h.0 as *mut std::ffi::c_void)
                    }
                    #[cfg(not(target_os = "windows"))]
                    {
                        None
                    }
                } else {
                    None
                };

                let config = PlatformConfig {
                    dbus_name: "Deeztracker",
                    display_name: "Deeztracker",
                    hwnd,
                };

                match MediaControls::new(config) {
                    Ok(mut controls) => {
                        let app_handle = app.handle().clone();
                        let _ = controls.attach(move |event| {
                            use souvlaki::MediaControlEvent;
                            use tauri::Emitter;
                            match event {
                                MediaControlEvent::Play => {
                                    let _ = app_handle.emit("media-play", ());
                                }
                                MediaControlEvent::Pause => {
                                    let _ = app_handle.emit("media-pause", ());
                                }
                                MediaControlEvent::Toggle => {
                                    let _ = app_handle.emit("media-toggle", ());
                                }
                                MediaControlEvent::Next => {
                                    let _ = app_handle.emit("media-next", ());
                                }
                                MediaControlEvent::Previous => {
                                    let _ = app_handle.emit("media-prev", ());
                                }
                                _ => (),
                            }
                        });

                        // Store the successfully initialized controls
                        if let Ok(mut guard) = media_controls_ref.lock() {
                            *guard = Some(controls);
                        }
                    }
                    Err(e) => {
                        eprintln!("Failed to initialize media controls: {:?}", e);
                    }
                }
            }

            // Initialize Database
            let app_data_dir = app
                .path()
                .app_data_dir()
                .expect("Failed to get app data dir");
            let conn = database::init(app_data_dir).expect("Failed to initialize database");
            app.manage(database::DbState(std::sync::Mutex::new(conn)));

            // Tray Menu Items
            let toggle_i = MenuItem::with_id(app, "toggle", "Play / Pausa", true, None::<&str>)?;
            let next_i = MenuItem::with_id(app, "next", "Siguiente", true, None::<&str>)?;
            let prev_i = MenuItem::with_id(app, "prev", "Anterior", true, None::<&str>)?;
            let show_i = MenuItem::with_id(app, "show", "Mostrar ventana", true, None::<&str>)?;
            let quit_i = MenuItem::with_id(app, "quit", "Salir", true, None::<&str>)?;
            
            let menu = Menu::with_items(app, &[
                &toggle_i, 
                &next_i, 
                &prev_i, 
                &tauri::menu::PredefinedMenuItem::separator(app)?,
                &show_i, 
                &quit_i
            ])?;

            let _tray = TrayIconBuilder::with_id("main_tray")
                .icon(app.default_window_icon().unwrap().clone())
                .tooltip("Deeztracker")
                .menu(&menu)
                .on_menu_event(|app, event| {
                    use tauri::Emitter;
                    match event.id.as_ref() {
                        "quit" => { app.exit(0); }
                        "show" => {
                            if let Some(w) = app.get_webview_window("main") {
                                let _ = w.show();
                                let _ = w.unminimize();
                                let _ = w.set_focus();
                            }
                        }
                        "toggle" => { let _ = app.emit("media-toggle", ()); }
                        "next" => { let _ = app.emit("media-next", ()); }
                        "prev" => { let _ = app.emit("media-prev", ()); }
                        _ => {}
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
                            let _ = w.unminimize();
                            let _ = w.set_focus();
                        }
                    }
                })
                .build(app)?;

            let audio_player = audio_player::AudioPlayerState::new(app.handle().clone());
            app.manage(audio_player);

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
            get_track,
            get_album,
            get_artist,
            get_playlist,
            get_artist_top_tracks,
            get_artist_albums,
            get_track_radio,
            update_media_metadata,
            update_playback_state,
            update_tray_menu,
            get_charts,
            get_autostart,
            set_autostart,
            api::lyrics::get_lyrics,
            database::toggle_favorite,
            database::get_favorites,
            database::is_favorite,
            database::create_playlist,
            database::delete_playlist,
            database::get_playlists,
            database::add_track_to_playlist,
            database::remove_track_from_playlist,
            database::get_playlist_tracks,
            database::get_downloads,
            database::is_downloaded,
            database::remove_download_record,
            database::add_download_record,
            database::get_download_path,
            database::check_downloads_integrity,
            get_downloads_dir,
            download_track_node,
            download_album_node,
            download_playlist_node,
            cancel_all_downloads,
            audio_player::audio_get_state,
            audio_player::audio_play_native,
            audio_player::audio_preload_native,
            audio_player::audio_pause_native,
            audio_player::audio_resume_native,
            audio_player::audio_stop_native,
            audio_player::audio_set_volume_native
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
