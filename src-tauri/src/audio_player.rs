use rodio::{OutputStream, Sink};
use std::io::{Read, Result as IoResult, Seek, SeekFrom};
use std::sync::mpsc::{channel, Sender};
use std::thread;
use std::time::Duration;
use tauri::{AppHandle, Emitter, State};
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::Mutex;
use std::sync::Arc;

use crate::RusteerState;
use crate::rusteer::ReadAndSeekAsync;

pub struct SyncStreamReader {
    pub inner: Box<dyn ReadAndSeekAsync + Send + Sync + Unpin>,
    pub runtime: tokio::runtime::Handle,
}

unsafe impl Send for SyncStreamReader {}
unsafe impl Sync for SyncStreamReader {}

impl Read for SyncStreamReader {
    fn read(&mut self, buf: &mut [u8]) -> IoResult<usize> {
        let handle = self.runtime.clone();
        let inner = &mut self.inner;
        handle.block_on(async {
            use tokio::io::AsyncReadExt;
            inner.read(buf).await
        })
    }
}

impl Seek for SyncStreamReader {
    fn seek(&mut self, pos: SeekFrom) -> IoResult<u64> {
        let handle = self.runtime.clone();
        let inner = &mut self.inner;
        handle.block_on(async {
            use tokio::io::AsyncSeekExt;
            inner.seek(pos).await
        })
    }
}

pub trait ReadAndSeek: Read + Seek {}
impl<T: Read + Seek> ReadAndSeek for T {}

pub enum AudioCommand {
    Play(Box<dyn ReadAndSeek + Send + Sync>, f64, String),
    Seek(f64),
    Pause,
    Resume,
    Stop,
    SetVolume(f32),
}

pub struct AudioPlayerState {
    pub tx: Sender<AudioCommand>,
    pub request_count: AtomicU64,
    pub current_track_id: Mutex<Option<String>>,
    pub current_offset_ms: Arc<AtomicU64>,
    pub is_playing: Arc<AtomicBool>,
}

impl AudioPlayerState {
    pub fn new(app_handle: AppHandle) -> Self {
        let (tx, rx) = channel::<AudioCommand>();
        
        let current_offset_ms = Arc::new(AtomicU64::new(0));
        let is_playing = Arc::new(AtomicBool::new(false));

        let offset_clone = current_offset_ms.clone();
        let playing_clone = is_playing.clone();

        thread::spawn(move || {
            let (_stream, handle) = OutputStream::try_default().unwrap();
            let sink = Sink::try_new(&handle).unwrap();
            let mut current_offset_sec = 0.0;
            let mut global_volume = 1.0f32;

            loop {
                match rx.recv_timeout(Duration::from_millis(200)) {
                    Ok(cmd) => {
                        match cmd {
                            AudioCommand::Play(reader, offset, _id) => {
                                current_offset_sec = 0.0;
                                let decoder_res = rodio::Decoder::new(reader);
                                match decoder_res {
                                    Ok(decoder) => {
                                        sink.stop();
                                        sink.set_volume(global_volume);
                                        sink.append(decoder);
                                        if offset > 0.01 {
                                            let _ = sink.try_seek(Duration::from_secs_f64(offset));
                                        }
                                        sink.play();
                                        playing_clone.store(true, Ordering::SeqCst);
                                        let _ = app_handle.emit("playback_progress_native", offset);
                                    }
                                    Err(_) => {}
                                }
                            }
                            AudioCommand::Seek(offset) => {
                                if sink.try_seek(Duration::from_secs_f64(offset)).is_ok() {
                                    let _ = app_handle.emit("playback_progress_native", offset);
                                }
                            }
                            AudioCommand::Pause => {
                                sink.pause();
                                playing_clone.store(false, Ordering::SeqCst);
                            }
                            AudioCommand::Resume => {
                                sink.play();
                                playing_clone.store(true, Ordering::SeqCst);
                            }
                            AudioCommand::Stop => {
                                sink.stop();
                                current_offset_sec = -1.0;
                                playing_clone.store(false, Ordering::SeqCst);
                                offset_clone.store(0, Ordering::SeqCst);
                            }
                            AudioCommand::SetVolume(v) => {
                                global_volume = v;
                                sink.set_volume(v);
                            }
                        }
                    }
                    Err(std::sync::mpsc::RecvTimeoutError::Timeout) => {
                        if !sink.is_paused() {
                            if sink.empty() {
                                if current_offset_sec >= 0.0 {
                                    let _ = app_handle.emit("playback_ended_native", ());
                                    current_offset_sec = -1.0;
                                    playing_clone.store(false, Ordering::SeqCst);
                                    offset_clone.store(0, Ordering::SeqCst);
                                }
                            } else {
                                let pos = sink.get_pos();
                                let total_pos = pos.as_secs_f64();
                                offset_clone.store((total_pos * 1000.0) as u64, Ordering::SeqCst);
                                playing_clone.store(true, Ordering::SeqCst);
                                let _ = app_handle.emit("playback_progress_native", total_pos);
                            }
                        } else {
                            playing_clone.store(false, Ordering::SeqCst);
                        }
                    }
                    Err(std::sync::mpsc::RecvTimeoutError::Disconnected) => break,
                }
            }
        });

        Self { 
            tx, 
            request_count: AtomicU64::new(0),
            current_track_id: Mutex::new(None),
            current_offset_ms,
            is_playing,
        }
    }
}

// ------ TAURI COMMANDS ------

#[tauri::command]
pub async fn audio_get_state(
    player: State<'_, AudioPlayerState>,
) -> Result<serde_json::Value, String> {
    let current_id = player.current_track_id.lock().unwrap();
    Ok(serde_json::json!({
        "track_id": *current_id,
        "position_ms": player.current_offset_ms.load(Ordering::SeqCst),
        "is_playing": player.is_playing.load(Ordering::SeqCst),
    }))
}

#[tauri::command]
pub async fn audio_play_native(
    track_id: String,
    _start_percent: f64,
    start_sec: f64,
    player: State<'_, AudioPlayerState>,
    rusteer_state: State<'_, RusteerState>,
) -> Result<(), String> {
    // 1. FAST PATH: If same track, just Seek
    {
        let mut current_id = player.current_track_id.lock().unwrap();
        if Some(track_id.clone()) == *current_id {
            let _ = player.tx.send(AudioCommand::Seek(start_sec));
            return Ok(());
        }
        // If different track, update the ID
        *current_id = Some(track_id.clone());
    }

    let my_request_id = player.request_count.fetch_add(1, Ordering::SeqCst) + 1;
    let _ = player.tx.send(AudioCommand::Stop);

    let rc = rusteer_state.inner().0.lock().unwrap().clone();
    let rusteer = rc.ok_or("Rusteer not initialized".to_string())?;

    // We always stream from 0 because we now have a seekable RAM buffer
    let stream_res = rusteer
        .stream_track(&track_id, 0, None)
        .await
        .map_err(|e| e.to_string())?;

    let reader = SyncStreamReader {
        inner: stream_res.stream,
        runtime: tokio::runtime::Handle::current(),
    };

    if player.request_count.load(Ordering::SeqCst) == my_request_id {
        let _ = player.tx.send(AudioCommand::Play(Box::new(reader), start_sec, track_id));
        Ok(())
    } else {
        Err("Request superseded".to_string())
    }
}

#[tauri::command]
pub async fn audio_preload_native(
    track_id: String,
    rusteer_state: State<'_, RusteerState>,
) -> Result<(), String> {
    let rc = rusteer_state.inner().0.lock().unwrap().clone();
    let rusteer = rc.ok_or("Rusteer not initialized".to_string())?;
    let _ = rusteer.preload_track(&track_id).await.map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
pub async fn audio_pause_native(player: State<'_, AudioPlayerState>) -> Result<(), String> {
    let _ = player.tx.send(AudioCommand::Pause);
    Ok(())
}

#[tauri::command]
pub async fn audio_resume_native(player: State<'_, AudioPlayerState>) -> Result<(), String> {
    let _ = player.tx.send(AudioCommand::Resume);
    Ok(())
}

#[tauri::command]
pub async fn audio_set_volume_native(
    volume: f32,
    player: State<'_, AudioPlayerState>,
) -> Result<(), String> {
    let _ = player.tx.send(AudioCommand::SetVolume(volume));
    Ok(())
}

#[tauri::command]
pub async fn audio_stop_native(player: State<'_, AudioPlayerState>) -> Result<(), String> {
    let mut current_id = player.current_track_id.lock().unwrap();
    *current_id = None;
    let _ = player.tx.send(AudioCommand::Stop);
    Ok(())
}
