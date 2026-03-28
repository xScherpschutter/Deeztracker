//! Unified Rusteer interface.
//!
//! This module provides a high-level, easy-to-use interface for
//! downloading music and fetching metadata from Deezer.

use std::fs;
use std::io::{Result as IoResult, SeekFrom};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use tokio::sync::{Notify, Semaphore};
use tokio_util::sync::CancellationToken;
use tauri::{AppHandle, Emitter};

use crate::api::{DeezerApi, GatewayApi};
use crate::crypto;
use crate::error::{DeezerError, Result};
use crate::models::{Album, Artist, Playlist, Track};
use crate::tagging::{self, AudioMetadata};

#[derive(Debug, Clone, serde::Serialize)]
pub struct DownloadProgress {
    pub track_id: String,
    pub status: String, // "pending", "downloading", "completed", "error"
    pub error: Option<String>,
}

/// Audio quality options for downloads.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum DownloadQuality {
    /// FLAC lossless (requires premium).
    Flac,
    /// MP3 320 kbps (requires premium).
    Mp3_320,
    /// MP3 128 kbps (free accounts).
    #[default]
    Mp3_128,
}

impl DownloadQuality {
    pub fn format(&self) -> &'static str {
        match self {
            DownloadQuality::Flac => "FLAC",
            DownloadQuality::Mp3_320 => "MP3_320",
            DownloadQuality::Mp3_128 => "MP3_128",
        }
    }

    pub fn extension(&self) -> &'static str {
        match self {
            DownloadQuality::Flac => ".flac",
            DownloadQuality::Mp3_320 | DownloadQuality::Mp3_128 => ".mp3",
        }
    }

    pub fn all() -> &'static [DownloadQuality] {
        &[
            DownloadQuality::Flac,
            DownloadQuality::Mp3_320,
            DownloadQuality::Mp3_128,
        ]
    }
}

/// Result of a single track download.
#[derive(Debug, Clone)]
pub struct DownloadResult {
    pub track_id: String,
    pub path: PathBuf,
    pub quality: DownloadQuality,
    pub size: u64,
    pub title: String,
    pub artist: String,
}

/// A shared memory buffer for streaming.
#[derive(Debug, Clone)]
pub struct SharedBuffer {
    pub data: Arc<Mutex<Vec<u8>>>,
    pub is_complete: Arc<AtomicBool>,
    pub notify: Arc<Notify>,
}

impl SharedBuffer {
    pub fn new() -> Self {
        Self {
            data: Arc::new(Mutex::new(Vec::with_capacity(5 * 1024 * 1024))), // Pre-alloc 5MB
            is_complete: Arc::new(AtomicBool::new(false)),
            notify: Arc::new(Notify::new()),
        }
    }
}

/// Result of a single streaming track download.
pub struct StreamingResult {
    pub quality: DownloadQuality,
    pub title: String,
    pub artist: String,
    pub content_length: u64,
    pub total_size: Option<u64>,
    pub stream: Box<dyn ReadAndSeekAsync + Send + Sync + Unpin>,
}

pub trait ReadAndSeekAsync: tokio::io::AsyncRead + tokio::io::AsyncSeek {}
impl<T: tokio::io::AsyncRead + tokio::io::AsyncSeek> ReadAndSeekAsync for T {}

impl std::fmt::Debug for StreamingResult {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("StreamingResult")
            .field("quality", &self.quality)
            .field("title", &self.title)
            .field("artist", &self.artist)
            .finish()
    }
}

/// Cache for the current track's metadata and buffer.
#[derive(Debug, Clone)]
struct StreamCache {
    track_id: String,
    title: String,
    artist: String,
    quality: DownloadQuality,
    buffer: SharedBuffer,
}

#[derive(Debug, Clone)]
pub struct Rusteer {
    public_api: DeezerApi,
    gateway_api: GatewayApi,
    preferred_quality: DownloadQuality,
    embed_tags: bool,
    output_dir: PathBuf,
    stream_cache: Arc<Mutex<Vec<StreamCache>>>,
    pub download_semaphore: Arc<Semaphore>,
    pub cancel_token: CancellationToken,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct BatchProgress {
    pub total: usize,
    pub current: usize,
    pub failed: usize,
}

impl Rusteer {
    pub async fn new(arl: &str) -> Result<Self> {
        let gateway_api = GatewayApi::new(arl).await?;
        let public_api = DeezerApi::new();

        Ok(Self {
            public_api,
            gateway_api,
            preferred_quality: DownloadQuality::default(),
            embed_tags: true,
            output_dir: PathBuf::from("downloads"),
            stream_cache: Arc::new(Mutex::new(Vec::with_capacity(5))),
            download_semaphore: Arc::new(Semaphore::new(4)),
            cancel_token: CancellationToken::new(),
        })
    }

    pub fn set_quality(&mut self, quality: DownloadQuality) {
        self.preferred_quality = quality;
    }
    pub fn quality(&self) -> DownloadQuality {
        self.preferred_quality
    }
    pub fn output_dir(&self) -> &Path {
        &self.output_dir
    }
    pub fn set_output_dir(&mut self, path: PathBuf) {
        self.output_dir = path;
    }
    pub fn has_premium(&self) -> bool {
        self.gateway_api.has_license_token()
    }

    pub async fn download_track_with_events(
        &self,
        track_id: &str,
        output_dir: &Path,
        app: &AppHandle,
    ) -> Result<DownloadResult> {
        let _permit = self.download_semaphore.acquire().await.map_err(|_| {
            DeezerError::ApiError("Semaphore closed".to_string())
        })?;

        if self.cancel_token.is_cancelled() {
            return Err(DeezerError::ApiError("Download cancelled".to_string()));
        }

        app.emit("download-progress", DownloadProgress {
            track_id: track_id.to_string(),
            status: "downloading".to_string(),
            error: None,
        }).unwrap_or_default();

        match self.download_track_to(track_id, output_dir).await {
            Ok(res) => Ok(res),
            Err(e) => {
                app.emit("download-progress", DownloadProgress {
                    track_id: track_id.to_string(),
                    status: "error".to_string(),
                    error: Some(e.to_string()),
                }).unwrap_or_default();
                Err(e)
            }
        }
    }

    pub async fn preload_track(&self, track_id: &str) -> Result<()> {
        let _ = self.get_or_create_buffer(track_id).await?;
        Ok(())
    }

    async fn get_or_create_buffer(&self, track_id: &str) -> Result<StreamCache> {
        {
            let mut cache = self.stream_cache.lock().unwrap();
            if let Some(pos) = cache
                .iter()
                .position(|c| c.track_id == track_id && c.quality == self.preferred_quality)
            {
                let item = cache.remove(pos);
                cache.push(item.clone());
                return Ok(item);
            }
        }

        let track = self.public_api.get_track(track_id).await?;
        let artist = track.artists_string(", ");
        let title = track.title.clone();
        let song_data = self.gateway_api.get_song_data(track_id).await?;

        if !song_data.readable {
            return Err(DeezerError::TrackNotFound(format!(
                "Track {} not readable",
                track_id
            )));
        }

        let track_token = song_data
            .track_token
            .ok_or_else(|| DeezerError::NoDataApi("No track token".to_string()))?;
        let (media_url, quality) = self.find_media_url(&track_token).await?;

        let shared_buffer = SharedBuffer::new();
        let cache_item = StreamCache {
            track_id: track_id.to_string(),
            title,
            artist,
            quality,
            buffer: shared_buffer.clone(),
        };

        {
            let mut cache = self.stream_cache.lock().unwrap();
            if cache.len() >= 5 {
                cache.remove(0);
            }
            cache.push(cache_item.clone());
        }

        let buffer_clone = shared_buffer.clone();
        let media_url_str = media_url.url.clone();
        let track_id_cloned = track_id.to_string();

        tokio::spawn(async move {
            let client = reqwest::Client::new();
            if let Ok(res) = client.get(&media_url_str).send().await {
                use futures_util::StreamExt;
                let mut byte_stream = res.bytes_stream();
                let key = crypto::calc_blowfish_key(&track_id_cloned);
                let mut chunk_buffer = Vec::new();
                let mut block_index = 0;
                let mut batch_buffer = Vec::with_capacity(16384);

                while let Some(chunk_res) = byte_stream.next().await {
                    if let Ok(bytes) = chunk_res {
                        chunk_buffer.extend_from_slice(&bytes);
                        while chunk_buffer.len() >= 2048 {
                            let block: Vec<u8> = chunk_buffer.drain(..2048).collect();
                            let processed = if block_index % 3 == 0 {
                                crypto::decrypt_blowfish_chunk(&block, &key)
                            } else {
                                block
                            };

                            batch_buffer.extend_from_slice(&processed);
                            block_index += 1;

                            if batch_buffer.len() >= 16384 {
                                {
                                    let mut data = buffer_clone.data.lock().unwrap();
                                    data.extend_from_slice(&batch_buffer);
                                }
                                buffer_clone.notify.notify_waiters();
                                batch_buffer.clear();
                            }
                        }
                    } else {
                        break;
                    }
                }
                if !batch_buffer.is_empty() {
                    let mut data = buffer_clone.data.lock().unwrap();
                    data.extend_from_slice(&batch_buffer);
                }
                if !chunk_buffer.is_empty() {
                    let mut data = buffer_clone.data.lock().unwrap();
                    data.extend_from_slice(&chunk_buffer);
                }
                buffer_clone.is_complete.store(true, Ordering::SeqCst);
                buffer_clone.notify.notify_waiters();
            }
        });

        Ok(cache_item)
    }

    pub async fn stream_track(
        &self,
        track_id: &str,
        start_byte: u64,
        _end_byte: Option<u64>,
    ) -> Result<StreamingResult> {
        let cache = self.get_or_create_buffer(track_id).await?;
        let stream = BufferStream {
            buffer: cache.buffer.clone(),
            pos: start_byte as usize,
        };

        Ok(StreamingResult {
            quality: cache.quality,
            title: cache.title,
            artist: cache.artist,
            content_length: 0,
            total_size: None,
            stream: Box::new(stream),
        })
    }

    async fn find_media_url(
        &self,
        track_token: &str,
    ) -> Result<(crate::api::gateway::MediaUrl, DownloadQuality)> {
        let qualities = match self.preferred_quality {
            DownloadQuality::Flac => vec![
                DownloadQuality::Flac,
                DownloadQuality::Mp3_320,
                DownloadQuality::Mp3_128,
            ],
            DownloadQuality::Mp3_320 => vec![DownloadQuality::Mp3_320, DownloadQuality::Mp3_128],
            DownloadQuality::Mp3_128 => vec![DownloadQuality::Mp3_128],
        };
        for quality in qualities {
            if let Ok(urls) = self
                .gateway_api
                .get_media_url(&[track_token.to_string()], quality.format())
                .await
            {
                if let Some(url) = urls.into_iter().next() {
                    return Ok((url, quality));
                }
            }
        }
        Err(DeezerError::NoRightOnMedia("No media URL".to_string()))
    }

    pub async fn get_track(&self, track_id: &str) -> Result<Track> {
        self.public_api.get_track(track_id).await
    }
    pub async fn get_album(&self, album_id: &str) -> Result<Album> {
        self.public_api.get_album(album_id).await
    }
    pub async fn get_playlist(&self, playlist_id: &str) -> Result<Playlist> {
        self.public_api.get_playlist(playlist_id).await
    }
    pub async fn get_artist(&self, artist_id: &str) -> Result<Artist> {
        self.public_api.get_artist(artist_id).await
    }
    pub async fn get_artist_top_tracks(&self, artist_id: &str, limit: u32) -> Result<Vec<Track>> {
        self.public_api
            .get_artist_top_tracks(artist_id, limit)
            .await
    }
    pub async fn get_artist_albums(&self, artist_id: &str, limit: u32) -> Result<Vec<Album>> {
        self.public_api.get_artist_albums(artist_id, limit).await
    }
    pub async fn search_tracks(&self, query: &str, limit: u32, index: u32) -> Result<Vec<Track>> {
        self.public_api.search_tracks(query, limit, index).await
    }
    pub async fn search_albums(&self, query: &str, limit: u32, index: u32) -> Result<Vec<Album>> {
        self.public_api.search_albums(query, limit, index).await
    }
    pub async fn search_artists(&self, query: &str, limit: u32, index: u32) -> Result<Vec<Artist>> {
        self.public_api.search_artists(query, limit, index).await
    }
    pub async fn search_playlists(
        &self,
        query: &str,
        limit: u32,
        index: u32,
    ) -> Result<Vec<Playlist>> {
        self.public_api.search_playlists(query, limit, index).await
    }

    pub async fn get_track_radio(&self, track_id: &str) -> Result<Vec<Track>> {
        let track = self.get_track(track_id).await?;
        let primary_artist_id = track
            .artists
            .first()
            .and_then(|a| a.ids.deezer.as_ref())
            .ok_or_else(|| DeezerError::NoDataApi("No artist ID".to_string()))?;

        match self
            .public_api
            .get_artist_radio(primary_artist_id, 40)
            .await
        {
            Ok(tracks) if !tracks.is_empty() => {
                return Ok(tracks);
            }
            Ok(_) => {}
            Err(_e) => {}
        }

        let related_artists = self
            .public_api
            .get_related_artists(primary_artist_id)
            .await
            .unwrap_or_default();

        if related_artists.is_empty() {
            return self.get_artist_top_tracks(primary_artist_id, 25).await;
        }

        let mut mix_tracks = Vec::new();
        for related in related_artists.iter().take(5) {
            if let Some(rid) = &related.ids.deezer {
                if let Ok(tops) = self.get_artist_top_tracks(rid, 10).await {
                    mix_tracks.extend(tops.into_iter().take(10));
                }
            }
        }

        use rand::seq::SliceRandom;
        mix_tracks.shuffle(&mut rand::thread_rng());
        Ok(mix_tracks)
    }

    pub async fn download_track_to<P: AsRef<Path>>(
        &self,
        track_id: &str,
        output_dir: P,
    ) -> Result<DownloadResult> {
        let output_dir = output_dir.as_ref();
        fs::create_dir_all(output_dir)?;
        let track = self.public_api.get_track(track_id).await?;
        let artist = track.artists_string(", ");
        let title = track.title.clone();
        let song_data = self.gateway_api.get_song_data(track_id).await?;
        if !song_data.readable {
            return Err(DeezerError::TrackNotFound("Not readable".to_string()));
        }
        let track_token = song_data
            .track_token
            .ok_or_else(|| DeezerError::NoDataApi("No track token".to_string()))?;
        let (media_url, quality) = self.find_media_url(&track_token).await?;
        let encrypted_bytes = reqwest::Client::new()
            .get(&media_url.url)
            .send()
            .await?
            .bytes()
            .await?;
        let safe_artist = sanitize_filename(&artist);
        let safe_title = sanitize_filename(&title);
        let output_path = output_dir.join(format!(
            "{} - {}{}",
            safe_artist,
            safe_title,
            quality.extension()
        ));
        crypto::decrypt_track(&encrypted_bytes, track_id, &output_path)?;
        if self.embed_tags {
            let cover_art = if !track.album.images.is_empty() {
                tagging::fetch_cover_art(&track.album.images[0].url).await
            } else {
                None
            };
            let metadata = AudioMetadata::new()
                .with_title(&track.title)
                .with_artist(&artist)
                .with_album(&track.album.title)
                .with_album_artist(&track.album.artists_string(", "))
                .with_track(track.track_number, Some(track.album.total_tracks))
                .with_disc(track.disc_number, Some(track.album.total_discs))
                .with_year(track.album.release_date.year);
            let metadata = if let Some(isrc) = &track.ids.isrc {
                metadata.with_isrc(isrc)
            } else {
                metadata
            };
            let metadata = if !track.album.genres.is_empty() {
                metadata.with_genre(track.album.genres.join(", "))
            } else {
                metadata
            };
            let metadata = if let Some(cover) = cover_art {
                metadata.with_cover_art(cover)
            } else {
                metadata
            };
            tagging::write_metadata(&output_path, &metadata)?;
        }
        Ok(DownloadResult {
            track_id: track_id.to_string(),
            path: output_path,
            quality,
            size: fs::metadata(output_dir.join(format!(
                "{} - {}{}",
                safe_artist,
                safe_title,
                quality.extension()
            )))?
            .len(),
            title,
            artist,
        })
    }
}

/// A custom stream that reads from the SharedBuffer and supports Seeking.
struct BufferStream {
    buffer: SharedBuffer,
    pos: usize,
}

impl tokio::io::AsyncRead for BufferStream {
    fn poll_read(
        mut self: std::pin::Pin<&mut Self>,
        cx: &mut std::task::Context<'_>,
        buf: &mut tokio::io::ReadBuf<'_>,
    ) -> std::task::Poll<IoResult<()>> {
        let data = self.buffer.data.lock().unwrap();
        if self.pos < data.len() {
            let to_read = std::cmp::min(buf.remaining(), data.len() - self.pos);
            buf.put_slice(&data[self.pos..self.pos + to_read]);
            let new_pos = self.pos + to_read;
            drop(data);
            self.pos = new_pos;
            return std::task::Poll::Ready(Ok(()));
        }
        if self.buffer.is_complete.load(Ordering::SeqCst) {
            return std::task::Poll::Ready(Ok(()));
        }
        let notify = self.buffer.notify.clone();
        let waker = cx.waker().clone();
        tokio::spawn(async move {
            notify.notified().await;
            waker.wake();
        });
        std::task::Poll::Pending
    }
}

impl tokio::io::AsyncSeek for BufferStream {
    fn start_seek(mut self: std::pin::Pin<&mut Self>, position: SeekFrom) -> IoResult<()> {
        let data_len = self.buffer.data.lock().unwrap().len();
        match position {
            SeekFrom::Start(p) => self.pos = p as usize,
            SeekFrom::Current(p) => self.pos = (self.pos as i64 + p) as usize,
            SeekFrom::End(p) => self.pos = (data_len as i64 + p) as usize,
        }
        Ok(())
    }
    fn poll_complete(
        self: std::pin::Pin<&mut Self>,
        _cx: &mut std::task::Context<'_>,
    ) -> std::task::Poll<IoResult<u64>> {
        std::task::Poll::Ready(Ok(self.pos as u64))
    }
}

fn sanitize_filename(name: &str) -> String {
    name.replace(['/', '\\', ':', '*', '?', '"', '<', '>', '|'], "_")
        .trim()
        .to_string()
}

#[derive(Debug, Clone)]
pub struct BatchDownloadResult {
    pub directory: PathBuf,
    pub successful: Vec<DownloadResult>,
    pub failed: Vec<(String, String)>,
}
impl BatchDownloadResult {
    pub fn total(&self) -> usize {
        self.successful.len() + self.failed.len()
    }
    pub fn all_successful(&self) -> bool {
        self.failed.is_empty()
    }
}
