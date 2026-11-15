# Tunebox: put it online and install it

## 1. Host it on GitHub Pages (once)
1. On github.com, create a new **public** repository (e.g. `tunebox`).
2. Click **Add file → Upload files** and drag in everything in this folder (index.html, sw.js, manifest.webmanifest, three icon PNGs). Commit.
3. Go to **Settings → Pages**. Under "Build and deployment", pick **Deploy from a branch**, branch **main**, folder **/ (root)**, then Save.
4. After a minute your app is at `https://YOUR-USERNAME.github.io/tunebox/`.

Only the app code is hosted. Your music never leaves your device.

## 2. Install
- **Windows:** open the link in Edge or Chrome, then click the install icon in the address bar (or menu → Install app).
- **iPhone:** open the link in **Safari**, tap Share → **Add to Home Screen**. Always open Tunebox from that icon.

Open the app once while online so it can save itself for offline use.

## 3. Use it
- **Add songs** picks MP3, WAV or OGG files (several at once). A yellow ! means title, artist, album or cover art is missing. Tap ⋯ on a song → Edit info.
- Songs with an album tag are grouped into collections automatically. **New** makes your own playlists or collections.
- A playlist is listed under every collection that shares a song with it.

## 4. Move your library between devices
Use ⋯ (top right) → **Export backup** on one device, then on the other: add the same audio files first, then **Import backup**. This carries playlists, collections, tags, favourites, ratings and play counts (not audio files or cover art).

## Test small first on iPhone
iOS limits web app storage. Add 20-30 songs, check they survive closing the app and a day or two, then add more.
