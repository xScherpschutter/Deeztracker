use clap::{Parser, Subcommand, ValueEnum};
use std::path::PathBuf;
use tauri_app_lib::{DownloadQuality, Rusteer};

// Update to add Stream enum command
#[derive(Parser)]
#[command(name = "rusteer-cli")]
#[command(about = "CLI for Rusteer - Deezer Downloader", long_about = None)]
struct Cli {
    /// Deezer ARL token (can also be set via DEEZER_ARL env var)
    #[arg(long, env = "DEEZER_ARL")]
    arl: String,

    /// Output directory for downloads
    #[arg(short, long, default_value = "downloads")]
    output: PathBuf,

    /// Audio quality
    #[arg(short, long, value_enum, default_value_t = Quality::Mp3_320)]
    quality: Quality,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Copy, Clone, PartialEq, Eq, PartialOrd, Ord, ValueEnum)]
enum Quality {
    Flac,
    Mp3_320,
    Mp3_128,
}

impl From<Quality> for DownloadQuality {
    fn from(q: Quality) -> Self {
        match q {
            Quality::Flac => DownloadQuality::Flac,
            Quality::Mp3_320 => DownloadQuality::Mp3_320,
            Quality::Mp3_128 => DownloadQuality::Mp3_128,
        }
    }
}

#[derive(Subcommand)]
enum Commands {
    /// Download a track, album, or playlist
    Download {
        /// URL or ID of the content to download
        id_or_url: String,

        /// Type of content (track, album, playlist) - optional, will try to auto-detect if URL provided
        #[arg(short, long)]
        r#type: Option<ContentType>,
    },
    /// Stream a track and save it chunk by chunk (testing)
    Stream {
        /// ID of the track to stream
        id: String,
    },
    /// Search for content
    Search {
        /// Search query
        query: String,

        /// Type of content to search (track, album)
        #[arg(short, long, value_enum, default_value_t = SearchType::Track)]
        r#type: SearchType,

        /// Limit results
        #[arg(short, long, default_value_t = 10)]
        limit: u32,
    },
}

#[derive(Copy, Clone, PartialEq, Eq, PartialOrd, Ord, ValueEnum)]
enum ContentType {
    Track,
    Album,
    Playlist,
}

#[derive(Copy, Clone, PartialEq, Eq, PartialOrd, Ord, ValueEnum)]
enum SearchType {
    Track,
    Album,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();

    // Initialize Rusteer
    let mut rusteer = Rusteer::new(&cli.arl).await?;
    rusteer.set_output_dir(cli.output.clone());
    rusteer.set_quality(cli.quality.into());

    match &cli.command {
        Commands::Download { id_or_url, r#type } => {
            // Simple heuristic for ID vs URL
            let id = if id_or_url.contains("deezer.com") {
                // Extract ID from URL (very basic implementation)
                id_or_url.split('/').last().unwrap_or(id_or_url)
            } else {
                id_or_url
            };

            // Determine type if not provided
            let content_type = match r#type {
                Some(t) => *t,
                None => {
                    if id_or_url.contains("/track/") {
                        ContentType::Track
                    } else if id_or_url.contains("/album/") {
                        ContentType::Album
                    } else if id_or_url.contains("/playlist/") {
                        ContentType::Playlist
                    } else {
                        // Default to track if unsure
                        ContentType::Track
                    }
                }
            };

            println!(
                "Downloading {} (ID: {})...",
                match content_type {
                    ContentType::Track => "track",
                    ContentType::Album => "album",
                    ContentType::Playlist => "playlist",
                },
                id
            );

            match content_type {
                ContentType::Track => {
                    let result = rusteer.download_track(id).await?;
                    println!("Downloaded: {}", result.title);
                    println!("Path: {}", result.path.display());
                }
                ContentType::Album => {
                    let result = rusteer.download_album(id).await?;
                    println!("Album downloaded to: {}", result.directory.display());
                    println!("Successful: {}/{}", result.successful.len(), result.total());
                    if !result.failed.is_empty() {
                        println!("   Failed tracks:");
                        for (title, err) in result.failed {
                            println!("   - {}: {}", title, err);
                        }
                    }
                }
                ContentType::Playlist => {
                    let result = rusteer.download_playlist(id).await?;
                    println!("Playlist downloaded to: {}", result.directory.display());
                    println!("Successful: {}/{}", result.successful.len(), result.total());
                    if !result.failed.is_empty() {
                        println!("   Failed tracks:");
                        for (title, err) in result.failed {
                            println!("   - {}: {}", title, err);
                        }
                    }
                }
            }
        }
        Commands::Stream { id } => {
            println!("Streaming track {}...", id);

            let mut result = rusteer.stream_track(id).await?;
            println!(
                "Streaming started for: {} by {}",
                result.title, result.artist
            );

            // For testing, we will just pipe it to an output file
            let extension = result.quality.extension();
            let safe_title = result
                .title
                .replace(['/', '\\', ':', '*', '?', '"', '<', '>', '|'], "_");
            let file_path = cli
                .output
                .join(format!("stream_{}{}", safe_title, extension));

            std::fs::create_dir_all(&cli.output)?;
            let mut file = tokio::fs::File::create(&file_path).await?;

            println!("   Writing stream to: {}", file_path.display());
            tokio::io::copy(&mut result.stream, &mut file).await?;
            println!("   Stream completed successfully!");
        }
        Commands::Search {
            query,
            r#type,
            limit,
        } => {
            println!("Searching for '{}'...", query);
            match r#type {
                SearchType::Track => {
                    let results = rusteer.search_tracks(query, *limit).await?;
                    for (i, track) in results.iter().enumerate() {
                        println!(
                            "{}. {} - {} (ID: {})",
                            i + 1,
                            track.artists_string(", "),
                            track.title,
                            track.ids.deezer.as_deref().unwrap_or("?")
                        );
                    }
                }
                SearchType::Album => {
                    let results = rusteer.search_albums(query, *limit).await?;
                    for (i, album) in results.iter().enumerate() {
                        println!(
                            "{}. {} - {} (ID: {})",
                            i + 1,
                            album.artists_string(", "),
                            album.title,
                            album.ids.deezer.as_deref().unwrap_or("?")
                        );
                    }
                }
            }
        }
    }

    Ok(())
}
