use rusqlite::{params, Connection};
use std::path::PathBuf;
use std::fs;
use crate::models::Track;
use serde_json;

pub struct DbState(pub std::sync::Mutex<Connection>);

pub fn init(app_data_dir: PathBuf) -> Result<Connection, String> {
    // Ensure the data directory exists
    fs::create_dir_all(&app_data_dir).map_err(|e| e.to_string())?;
    
    let db_path = app_data_dir.join("library.db");
    let conn = Connection::open(db_path).map_err(|e| e.to_string())?;

    // Create tables
    conn.execute(
        "CREATE TABLE IF NOT EXISTS favorites (
            track_id TEXT PRIMARY KEY,
            metadata TEXT NOT NULL,
            added_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )",
        [],
    ).map_err(|e| e.to_string())?;

    conn.execute(
        "CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )",
        [],
    ).map_err(|e| e.to_string())?;

    conn.execute(
        "CREATE TABLE IF NOT EXISTS playlist_tracks (
            playlist_id INTEGER NOT NULL,
            track_id TEXT NOT NULL,
            metadata TEXT NOT NULL,
            added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (playlist_id, track_id),
            FOREIGN KEY (playlist_id) REFERENCES playlists (id) ON DELETE CASCADE
        )",
        [],
    ).map_err(|e| e.to_string())?;

    Ok(conn)
}

// Favorites Commands
#[tauri::command]
pub async fn toggle_favorite(track: Track, state: tauri::State<'_, DbState>) -> Result<bool, String> {
    let conn = state.0.lock().map_err(|e| e.to_string())?;
    let track_id = track.ids.deezer.clone().ok_or("No track ID")?;
    
    // Check if exists
    let exists: bool = conn.query_row(
        "SELECT EXISTS(SELECT 1 FROM favorites WHERE track_id = ?)",
        params![track_id],
        |row| row.get(0),
    ).map_err(|e| e.to_string())?;

    if exists {
        conn.execute("DELETE FROM favorites WHERE track_id = ?", params![track_id])
            .map_err(|e| e.to_string())?;
        Ok(false)
    } else {
        let metadata = serde_json::to_string(&track).map_err(|e| e.to_string())?;
        conn.execute(
            "INSERT INTO favorites (track_id, metadata) VALUES (?, ?)",
            params![track_id, metadata],
        ).map_err(|e| e.to_string())?;
        Ok(true)
    }
}

#[tauri::command]
pub async fn get_favorites(state: tauri::State<'_, DbState>) -> Result<Vec<Track>, String> {
    let conn = state.0.lock().map_err(|e| e.to_string())?;
    let mut stmt = conn.prepare("SELECT metadata FROM favorites ORDER BY added_at DESC")
        .map_err(|e| e.to_string())?;
    
    let tracks_iter = stmt.query_map([], |row| {
        let metadata: String = row.get(0)?;
        Ok(serde_json::from_str::<Track>(&metadata).unwrap())
    }).map_err(|e| e.to_string())?;

    let mut tracks = Vec::new();
    for track in tracks_iter {
        tracks.push(track.map_err(|e| e.to_string())?);
    }
    Ok(tracks)
}

#[tauri::command]
pub async fn is_favorite(track_id: String, state: tauri::State<'_, DbState>) -> Result<bool, String> {
    let conn = state.0.lock().map_err(|e| e.to_string())?;
    let exists: bool = conn.query_row(
        "SELECT EXISTS(SELECT 1 FROM favorites WHERE track_id = ?)",
        params![track_id],
        |row| row.get(0),
    ).map_err(|e| e.to_string())?;
    Ok(exists)
}

// Playlist Commands
#[tauri::command]
pub async fn create_playlist(name: String, description: Option<String>, state: tauri::State<'_, DbState>) -> Result<i64, String> {
    let conn = state.0.lock().map_err(|e| e.to_string())?;
    conn.execute(
        "INSERT INTO playlists (name, description) VALUES (?, ?)",
        params![name, description],
    ).map_err(|e| e.to_string())?;
    Ok(conn.last_insert_rowid())
}

#[tauri::command]
pub async fn delete_playlist(id: i64, state: tauri::State<'_, DbState>) -> Result<(), String> {
    let conn = state.0.lock().map_err(|e| e.to_string())?;
    conn.execute("DELETE FROM playlists WHERE id = ?", params![id])
        .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
pub async fn get_playlists(state: tauri::State<'_, DbState>) -> Result<Vec<serde_json::Value>, String> {
    let conn = state.0.lock().map_err(|e| e.to_string())?;
    let mut stmt = conn.prepare("SELECT id, name, description, created_at FROM playlists ORDER BY created_at DESC")
        .map_err(|e| e.to_string())?;
    
    let rows = stmt.query_map([], |row| {
        Ok(serde_json::json!({
            "id": row.get::<_, i64>(0)?,
            "name": row.get::<_, String>(1)?,
            "description": row.get::<_, Option<String>>(2)?,
            "created_at": row.get::<_, String>(3)?
        }))
    }).map_err(|e| e.to_string())?;

    let mut playlists = Vec::new();
    for row in rows {
        playlists.push(row.map_err(|e| e.to_string())?);
    }
    Ok(playlists)
}

#[tauri::command]
pub async fn add_track_to_playlist(playlist_id: i64, track: Track, state: tauri::State<'_, DbState>) -> Result<(), String> {
    let conn = state.0.lock().map_err(|e| e.to_string())?;
    let track_id = track.ids.deezer.clone().ok_or("No track ID")?;
    let metadata = serde_json::to_string(&track).map_err(|e| e.to_string())?;
    
    conn.execute(
        "INSERT OR REPLACE INTO playlist_tracks (playlist_id, track_id, metadata) VALUES (?, ?, ?)",
        params![playlist_id, track_id, metadata],
    ).map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
pub async fn remove_track_from_playlist(playlist_id: i64, track_id: String, state: tauri::State<'_, DbState>) -> Result<(), String> {
    let conn = state.0.lock().map_err(|e| e.to_string())?;
    conn.execute(
        "DELETE FROM playlist_tracks WHERE playlist_id = ? AND track_id = ?",
        params![playlist_id, track_id],
    ).map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
pub async fn get_playlist_tracks(playlist_id: i64, state: tauri::State<'_, DbState>) -> Result<Vec<Track>, String> {
    let conn = state.0.lock().map_err(|e| e.to_string())?;
    let mut stmt = conn.prepare("SELECT metadata FROM playlist_tracks WHERE playlist_id = ? ORDER BY added_at ASC")
        .map_err(|e| e.to_string())?;
    
    let tracks_iter = stmt.query_map(params![playlist_id], |row| {
        let metadata: String = row.get(0)?;
        Ok(serde_json::from_str::<Track>(&metadata).unwrap())
    }).map_err(|e| e.to_string())?;

    let mut tracks = Vec::new();
    for track in tracks_iter {
        tracks.push(track.map_err(|e| e.to_string())?);
    }
    Ok(tracks)
}
