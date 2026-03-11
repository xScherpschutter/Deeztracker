use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use tauri::AppHandle;
use tauri::Manager;

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct LrcLibResponse {
    pub id: Option<u32>,
    pub name: Option<String>,
    pub track_name: Option<String>,
    pub artist_name: Option<String>,
    pub album_name: Option<String>,
    pub duration: Option<f64>,
    pub instrumental: Option<bool>,
    pub plain_lyrics: Option<String>,
    pub synced_lyrics: Option<String>,
}

async fn fetch_from_lrclib(
    artist: &str,
    title: &str,
    album: &str,
    duration: f64,
) -> Result<Option<String>, String> {
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(15))
        .build()
        .map_err(|e| e.to_string())?;
    
    let url = "https://lrclib.net/api/get";
    let query = [
        ("artist_name", artist),
        ("track_name", title),
        ("album_name", album),
        ("duration", &duration.to_string()),
    ];

    let mut exact_plain_fallback: Option<String> = None;

    if let Ok(res) = client.get(url).query(&query).send().await {
        if res.status().is_success() {
            if let Ok(lrc_res) = res.json::<LrcLibResponse>().await {
                if let Some(synced) = lrc_res.synced_lyrics {
                    if !synced.is_empty() {
                        return Ok(Some(synced));
                    }
                }
                exact_plain_fallback = lrc_res.plain_lyrics;
            }
        }
    }

    let search_url = "https://lrclib.net/api/search";
    let search_query = [("q", format!("{} {}", artist, title))];
    
    if let Ok(res) = client.get(search_url).query(&search_query).send().await {
        if res.status().is_success() {
            if let Ok(results) = res.json::<Vec<LrcLibResponse>>().await {
                for result in results.iter().take(5) {
                    if let Some(synced) = &result.synced_lyrics {
                        if !synced.is_empty() {
                            return Ok(Some(synced.clone()));
                        }
                    }
                }

                if let Some(ref plain) = exact_plain_fallback {
                    if !plain.is_empty() {
                        return Ok(Some(plain.clone()));
                    }
                }

                for result in results {
                    if let Some(plain) = result.plain_lyrics {
                        if !plain.is_empty() {
                            return Ok(Some(plain));
                        }
                    }
                }
            }
        }
    }

    if let Some(plain) = exact_plain_fallback {
        return Ok(Some(plain));
    }

    Ok(None)
}

fn get_cache_path(app: &AppHandle, artist: &str, title: &str) -> Option<PathBuf> {
    let mut path = app.path().app_data_dir().ok()?;
    path.push("lyrics");
    
    if !path.exists() {
        let _ = fs::create_dir_all(&path);
    }

    let safe_artist = artist.chars().filter(|c| c.is_alphanumeric() || *c == ' ').collect::<String>().replace(" ", "_");
    let safe_title = title.chars().filter(|c| c.is_alphanumeric() || *c == ' ').collect::<String>().replace(" ", "_");
    path.push(format!("{}_{}.lrc", safe_artist, safe_title));
    
    Some(path)
}

#[tauri::command]
pub async fn get_lyrics(
    app: AppHandle,
    artist: String,
    title: String,
    album: String,
    duration_ms: u64,
) -> Result<Option<String>, String> {
    let duration_sec = duration_ms as f64 / 1000.0;
    
    // 1. Check Cache
    if let Some(cache_path) = get_cache_path(&app, &artist, &title) {
        if cache_path.exists() {
            if let Ok(content) = fs::read_to_string(cache_path) {
                if !content.is_empty() && content != "NOT_FOUND" {
                    return Ok(Some(content));
                }
            }
        }
    }

    // 2. Fetch from API with Enhanced Fallback
    match fetch_from_lrclib(&artist, &title, &album, duration_sec).await {
        Ok(Some(lyrics)) => {
            if let Some(cache_path) = get_cache_path(&app, &artist, &title) {
                let _ = fs::write(cache_path, &lyrics);
            }
            Ok(Some(lyrics))
        }
        Ok(None) => Ok(None),
        Err(e) => Err(e),
    }
}
