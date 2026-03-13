use rodio::{Decoder, OutputStream, Sink};
use std::io::{Read, Result as IoResult, Seek, SeekFrom};
use std::sync::mpsc::{channel, Sender};
use std::thread;
use std::time::Duration;
use tauri::{AppHandle, Emitter, State};

use crate::RusteerState;

// Synchronous wrapper around Tokio Duplex stream for Rodio's decoder.
pub struct SyncStreamReader {
    pub inner: tokio::io::ReadHalf<tokio::io::DuplexStream>,
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
    fn seek(&mut self, _pos: SeekFrom) -> IoResult<u64> {
        Ok(0)
    }
}

pub struct HeaderInjectReader<R: Read> {
    pub inner: R,
    pub injected: bool,
}

impl<R: Read> Read for HeaderInjectReader<R> {
    fn read(&mut self, buf: &mut [u8]) -> IoResult<usize> {
        if !self.injected {
            let dummy_frame: [u8; 10] =
                [0xFF, 0xFB, 0x92, 0x64, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00];
            let to_copy = std::cmp::min(buf.len(), dummy_frame.len());
            buf[..to_copy].copy_from_slice(&dummy_frame[..to_copy]);
            self.injected = true;
            return Ok(to_copy);
        }
        self.inner.read(buf)
    }
}

impl<R: Read + Seek> Seek for HeaderInjectReader<R> {
    fn seek(&mut self, pos: SeekFrom) -> IoResult<u64> {
        self.inner.seek(pos)
    }
}

pub trait ReadAndSeek: Read + Seek {}
impl<T: Read + Seek> ReadAndSeek for T {}

pub enum AudioCommand {
    Play(Box<dyn ReadAndSeek + Send + Sync>, f64),
    Pause,
    Resume,
    Stop,
    SetVolume(f32),
}

use std::sync::atomic::{AtomicU64, Ordering};

pub struct AudioPlayerState {
    pub tx: Sender<AudioCommand>,
    pub request_count: AtomicU64,
}

impl AudioPlayerState {
    pub fn new(app_handle: AppHandle) -> Self {
        let (tx, rx) = channel::<AudioCommand>();

        thread::spawn(move || {
            let (_stream, handle) = OutputStream::try_default().unwrap();
            let sink = Sink::try_new(&handle).unwrap();
            let mut current_offset_sec = 0.0;

            loop {
                match rx.recv_timeout(Duration::from_millis(50)) {
                    Ok(cmd) => {
                        match cmd {
                            AudioCommand::Play(reader, offset) => {
                                current_offset_sec = offset;
                                match Decoder::new_mp3(reader) {
                                    Ok(decoder) => {
                                        sink.stop();
                                        sink.append(decoder);
                                        sink.play();
                                        let _ = app_handle.emit("playback_progress_native", offset);
                                    }
                                    Err(_e) => {
                                         
                                    }
                                }
                            }
                            AudioCommand::Pause => sink.pause(),
                            AudioCommand::Resume => sink.play(),
                            AudioCommand::Stop => {
                                sink.stop();
                                current_offset_sec = -1.0;
                            }
                            AudioCommand::SetVolume(v) => sink.set_volume(v),
                        }
                    }
                    Err(std::sync::mpsc::RecvTimeoutError::Timeout) => {
                        if !sink.is_paused() {
                            if sink.empty() {
                                if current_offset_sec >= 0.0 {
                                    let _ = app_handle.emit("playback_ended_native", ());
                                    current_offset_sec = -1.0;
                                }
                            } else {
                                let pos = sink.get_pos();
                                let total_pos = pos.as_secs_f64() + current_offset_sec;
                                let _ = app_handle.emit("playback_progress_native", total_pos);
                            }
                        }
                    }
                    Err(std::sync::mpsc::RecvTimeoutError::Disconnected) => break,
                }
            }
        });

        Self { 
            tx, 
            request_count: AtomicU64::new(0) 
        }
    }
}

#[tauri::command]
pub async fn audio_play_native(
    track_id: String,
    start_percent: f64,
    start_sec: f64,
    player: State<'_, AudioPlayerState>,
    rusteer_state: State<'_, RusteerState>,
) -> Result<(), String> {
    let my_request_id = player.request_count.fetch_add(1, Ordering::SeqCst) + 1;
    let _ = player.tx.send(AudioCommand::Stop);

    let rc = rusteer_state.inner().0.lock().unwrap().clone();
    let rusteer = rc.ok_or("Rusteer not initialized".to_string())?;

    let start_byte = if start_percent <= 0.001 {
        0
    } else {
        (start_sec * 16_000.0) as u64
    };

    let stream_res = rusteer
        .stream_track(&track_id, start_byte, None)
        .await
        .map_err(|e| e.to_string())?;


    let reader = SyncStreamReader {
        inner: stream_res.stream,
        runtime: tokio::runtime::Handle::current(),
    };

    let final_reader = HeaderInjectReader {
        inner: reader,
        injected: start_byte == 0,
    };

    if player.request_count.load(Ordering::SeqCst) == my_request_id {
        let _ = player.tx.send(AudioCommand::Play(Box::new(final_reader), start_sec));
        Ok(())
    } else {
        Err("Request superseded by a newer one".to_string())
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
    let _ = player.tx.send(AudioCommand::Stop);
    Ok(())
}
