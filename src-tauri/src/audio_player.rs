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
        // Mp3 streams via Symphonia don't strictly require seeking to play, just to probe length
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
            // A valid 128kbps, 44100Hz, Stereo MP3 Frame Header (MPEG Version 1, Layer III)
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
            // ... resto del loop igual ...

            loop {
                match rx.recv_timeout(Duration::from_millis(50)) {
                    Ok(cmd) => {
                        match cmd {
                            AudioCommand::Play(reader, offset) => {
                                current_offset_sec = offset;
                                match Decoder::new_mp3(reader) {
                                    Ok(decoder) => {
                                        sink.stop();
                                        println!("Rodio: Decoder started from offset: {}", offset);
                                        sink.append(decoder);
                                        sink.play();
                                        // Immediate progress update to sync UI
                                        let _ = app_handle.emit("playback_progress_native", offset);
                                    }
                                    Err(e) => {
                                        println!("Rodio Error: Failed to start Decoder at offset {}: {:?}", offset, e);
                                    }
                                }
                            }
                            AudioCommand::Pause => sink.pause(),
                            AudioCommand::Resume => sink.play(),
                            AudioCommand::Stop => {
                                sink.stop();
                                // Mark as -1.0 to prevent the timeout loop from emitting playback_ended_native
                                current_offset_sec = -1.0;
                            }
                            AudioCommand::SetVolume(v) => sink.set_volume(v),
                        }
                    }
                    Err(std::sync::mpsc::RecvTimeoutError::Timeout) => {
                        if !sink.is_paused() {
                            if sink.empty() {
                                // Ensure we only emit once per track end by resetting offset and pausing/stopping
                                if current_offset_sec >= 0.0 {
                                    let _ = app_handle.emit("playback_ended_native", ());
                                    current_offset_sec = -1.0; // Mark as having emitted ended to avoid loop spam
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

// ------ TAURI COMMANDS ------

#[tauri::command]
pub async fn audio_play_native(
    track_id: String,
    start_percent: f64,
    start_sec: f64,
    player: State<'_, AudioPlayerState>,
    rusteer_state: State<'_, RusteerState>,
) -> Result<(), String> {
    // Increment request ID and stop immediately to avoid overlap
    let my_request_id = player.request_count.fetch_add(1, Ordering::SeqCst) + 1;
    let _ = player.tx.send(AudioCommand::Stop);

    let rc = rusteer_state.inner().0.lock().unwrap().clone();
    let rusteer = rc.ok_or("Rusteer not initialized".to_string())?;

    println!(
        "NATIVE AUDIO CMD -> play_native: track: {}, request_id: {}, percent: {}, sec: {}",
        track_id, my_request_id, start_percent, start_sec
    );

    // Deezer MP3 format standard quality is ~128kbps = 16,000 bytes per second
    let start_byte = if start_percent <= 0.001 {
        0
    } else {
        (start_sec * 16_000.0) as u64
    };
    println!(
        "Native Audio Seek - Calculated Start Byte without Probe: {}",
        start_byte
    );

    // We must pass the correct exact byte offset because Deezer Blowfish works on 2048 blocks!
    let stream_res = rusteer
        .stream_track(&track_id, start_byte, None)
        .await
        .map_err(|e| e.to_string())?;

    // The actual start byte requested might differ because of 2048 padding in rusteer.rs,
    // but the `stream_track` strips the padding transparently from `stream_res.stream`!

    let reader = SyncStreamReader {
        inner: stream_res.stream,
        runtime: tokio::runtime::Handle::current(),
    };

    let final_reader = HeaderInjectReader {
        inner: reader,
        injected: start_byte == 0, // If streaming from start, we don't need to inject header
    };

    // ONLY send the play command if we are still the LATEST request
    if player.request_count.load(Ordering::SeqCst) == my_request_id {
        let _ = player.tx.send(AudioCommand::Play(Box::new(final_reader), start_sec));
        Ok(())
    } else {
        println!("Anxiety Click: Discarding outdated play request for track {}", track_id);
        Err("Request superseded by a newer one".to_string())
    }
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
