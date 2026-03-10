# API Investigation: Radio & Recommendations

## Problem: Public Radio Endpoint
The public Deezer API endpoint `https://api.deezer.com/track/{id}/radio` returns a `600 InvalidQueryException` (Unknown path components). This suggests the endpoint has been deprecated or restricted in the current version of the public API.

## Solution: Gateway API (smartradio.getSongs)
The internal Deezer Gateway (Private API) provides a method called `smartradio.getSongs` which is used by the official web player to generate "Track Radio" streams.

### Gateway Method Details:
- **Method:** `smartradio.getSongs`
- **Payload:** `{"sng_id": "{track_id}"}`
- **Authentication:** Requires valid session cookies (`arl` / `sid`) and `api_token`.

### Implementation Plan:
1. Implement `get_smart_radio` in `src-tauri/src/api/gateway.rs`.
2. Update `rusteer.rs` to expose the gateway method.
3. Update `lib.rs` tauri command `get_track_radio` to switch from Public API to Gateway API.
