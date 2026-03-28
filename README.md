<h1 align="center">Deeztracker</h1>

<p align="center">
  <img src="src-tauri/icons/128x128.png" alt="Deeztracker Logo" width="120"/>
</p>

<p align="center">
  <strong>A modern, lightning-fast desktop application for streaming and downloading your favorite music offline</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Desktop-green?style=flat-square"/>
  <img src="https://img.shields.io/badge/Backend-Rust%20%7C%20Tauri-orange?style=flat-square"/>
  <img src="https://img.shields.io/badge/Frontend-Vue%203%20%7C%20TypeScript-blue?style=flat-square"/>
  <img src="https://img.shields.io/badge/UI-PrimeVue-indigo?style=flat-square"/>
</p>

---

## Overview

Welcome to **Deeztracker**! This application serves as your all-in-one destination for enjoying high-quality audio streaming while giving you the flexibility to download tracks directly to your local machine for offline listening. 

Built from the ground up prioritizing both performance and aesthetics, Deeztracker bridges the gap between top-tier playback performance and modern UI design. Whether you are discovering new music, listening to smart radio sessions, or building your local library, Deeztracker offers a seamless, premium music experience.

## Key Features

- **Seamless Streaming:** Enjoy buffer-free, high-quality audio streaming natively.
- **Fast Downloads:** Easily download individual tracks directly to your system for offline enjoyment.
- **Smart Radio:** Adaptive and continuous listening experiences dynamically curated based on artists.
- **Native Integration:** Native media controls integrated directly into your OS for seamless playback control.
- **Premium UI:** A beautiful, responsive, and thoughtfully designed interface for the ultimate user experience.

## Tech Stack

- **Frontend:** Vue 3, TypeScript, Vite, PrimeVue, and Tailwind CSS.
- **Backend:** Rust, Tauri. 
- **State Management:** Pinia.

## Configuration (Deezer ARL)

To unlock the full potential of Deeztracker, you will need to provide your Deezer ARL. This token acts as a session cookie, allowing you to access higher quality streams and track downloads.

You can easily obtain it by following these steps:

1. Log in to [Deezer](https://www.deezer.com/) from your web browser.
2. Open the Developer Tools (usually `F12` or `Ctrl+Shift+I`).
3. Navigate to the **Application** tab (Chrome/Edge) or **Storage** tab (Firefox).
4. Under **Cookies**, select `https://www.deezer.com`.
5. Find the cookie named `arl` and copy its entire value.

Paste this value directly into the application's configuration screen when prompted.

## Development

To run this project locally, ensure you have Node.js, `pnpm`, and the Rust toolchain installed on your machine.

1. **Install dependencies:**
   ```bash
   pnpm install
   ```

2. **Run the development server:**
   ```bash
   pnpm tauri dev
   ```

3. **Build the production release:**
   ```bash
   pnpm tauri build
   ```

## License

This project is licensed under the [MIT License](LICENSE).
