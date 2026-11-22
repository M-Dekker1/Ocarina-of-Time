# Ocarina of Time

## 1. Put the app online (GitHub Pages)
1. Upload everything in this folder to your GitHub repository (replace the old files) and commit. This includes the `sounds` folder, which holds the songs the logo plays.
2. New repository? **Settings → Pages → Deploy from a branch → main → / (root)**.
3. Open `https://YOUR-USERNAME.github.io/REPO/` online once, then install it:
   - **Windows:** install icon in the Edge or Chrome address bar.
   - **iPhone:** Safari → Share → **Add to Home Screen**. If an old icon is there, delete it first.

## 2. Set up syncing over your home Wi-Fi

Your PC runs a small server that keeps your songs, playlists, tags, ratings, favourites, play counts and cover art. Each device syncs with it when the app starts (or via ⋯ → Sync now) while you're on your home Wi-Fi and the PC is on. Away from home nothing syncs and the app works as normal.

### One-time setup on the PC
1. Install **Python 3.8+** from python.org (tick "Add to PATH").
2. Keep everything in this folder together on your PC (`server.py` also needs `netutil.py`, the `sounds` folder and the app files).
3. Open a terminal in the folder and run: `python setup_https.py`
   - It installs the free tool mkcert using winget if needed. If it asks you to reopen the terminal and run it again, do that.
   - Click **Yes** if Windows asks to trust the certificate.
4. Run `python server.py` (or double-click `start-server.bat`). If Windows asks about the firewall, tick **Private networks** and allow.
5. The window shows your **phone address**, **certificate page** and **access token**. They are also saved in `ocarina-data/connection-info.txt`.

To start the server automatically with Windows: press Win+R, type `shell:startup`, and put a shortcut to `start-server.bat` there. Right-click the shortcut, choose Properties, and set **Run** to **Minimized** so the window stays out of the way.

### On the PC app
⋯ → **Sync settings**: address `https://localhost:8765` and the token.

### On the iPhone (once, on your home Wi-Fi)
1. In Safari, open the **certificate page** address from the server window (like `http://192.168.1.20:8766`), tap **Download certificate**, and tap **Allow**.
2. Open **Settings → Profile Downloaded → Install**.
3. Go to **Settings → General → About → Certificate Trust Settings** and switch the new certificate on.
4. In the app: ⋯ → **Sync settings**. Enter the phone address (like `https://192.168.1.20:8765`) and the token.

You can list more than one address, separated by commas (for example the IP and the `.local` name). The app uses the first one that answers.

### Tips and troubleshooting
- Your PC's address can change. In your router's settings, reserve a fixed address for the PC (look for "DHCP reservation"). If it does change, run `python setup_https.py` again and update the address in the app.
- **Download songs to this device** (Sync settings): switch it off on a phone with limited space. Songs then show a cloud icon and stream from your PC while you're home.
- The first sync uploads everything from the device that has the music, which can take a while. Keep the app open.
- After the first sync, only what changed is sent in each direction, so syncing is quick even with a large library. If two devices ever seem out of step, use **Settings → Sync → Full resync** to compare everything again.
- Cover art is stored once per distinct picture, so an album with 60 tracks keeps one copy of its cover instead of 60. The first time you open the updated app it moves existing covers into the shared store (you'll see "Optimising cover art"), and the server tidies up its old per-song cover files on the next sync.
- Deleting a song or playlist on one device deletes it on the others at their next sync. If two devices edit the same thing, the most recent change wins.
- Treat the token like a password. Anyone on your Wi-Fi who has it could read your library.
- "Server not reachable": check the server window is running, both devices are on the same Wi-Fi, and your router isn't blocking devices from talking to each other ("client isolation" or "guest network").
- If sync works on your iPhone but your PC browser blocks it, install the app on the PC from `https://localhost:8765` instead of GitHub Pages.

## 3. Backups
⋯ → **Export backup** saves your playlists, tags, favourites, ratings and play counts. With sync on, the `ocarina-data` folder on your PC holds a full copy of everything, including the audio.
