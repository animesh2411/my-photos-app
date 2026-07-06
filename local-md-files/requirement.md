# Project build spec: "PhotoBridge" — local network Photos app

Paste this whole document into GitHub Copilot Chat (or Copilot Workspace) as
the initial prompt, then work through it section by section, asking Copilot
to implement one section at a time and testing before moving to the next.

## 1. What this app is

A local web app, called **PhotoBridge**, that runs on a Windows laptop and
lets a phone on the same WiFi network browse the laptop's photo/video folder
in an interface styled like Apple Photos: date-grouped grid, albums,
favorites, a full-screen swipeable viewer, and a "Save to Photos" button
that saves the file directly into the phone's native camera roll via the
browser share sheet.

No cloud sync. No login/auth (trusted local network only). No mobile app to
install — it's a Progressive Web App (PWA) added to the home screen via
Safari.

Importantly, the folder PhotoBridge serves is **not hardcoded** — the first
time you open the app (from your iPhone or anywhere), it shows a setup
screen where you type in the absolute path of the folder on the laptop you
want to browse. The server validates that the path exists on disk, saves it
to a small local config file, and starts serving it. You can change it later
from a Settings screen without editing any files or restarting the server
manually.

## 2. Tech stack

- **Backend**: Python 3.11+, FastAPI, served with `uvicorn`.
- **Image handling**: Pillow (`PIL`) for thumbnail resizing and EXIF date
  reading. `pillow-heif` registered as a Pillow plugin so `.heic`/`.heif`
  files (native iPhone photo format) can be opened and resized.
- **Frontend**: plain HTML/CSS/JS. No build step, no framework — served as
  static files by FastAPI. Must work in Mobile Safari on iOS.
- **Persistence**: none required server-side. Favorites are stored in the
  browser's `localStorage`. Photo/video metadata is derived by scanning the
  filesystem each time (or on demand via a `/api/rescan` call) — no
  database.

## 3. Folder structure

```
photobridge/
  app/
    main.py            # FastAPI app, routes
    scanner.py          # filesystem walk + EXIF date extraction + in-memory index
    media.py             # thumbnail generation, range-request file streaming
    config.py            # reads/writes config.json (photos_dir, port)
  static/
    index.html
    style.css
    app.js
    manifest.json
    sw.js
    icons/
      icon-180.png
      icon-512.png
  config.json              # created on first run once a folder is chosen; not committed to git
  requirements.txt
  run.py                  # entry point: starts uvicorn in a background thread
  run_app.bat             # double-clickable batch launcher for non-technical users
  gui_app.py              # desktop control center GUI app (Tkinter)
  run_control_center.bat  # double-clickable launcher for the GUI control center
  setup.bat               # firewall setup batch script (admin)
  uninstall.bat           # firewall removal batch script (admin)
  README.md                # setup + run instructions
  CONTRIBUTING.md          # contribution guidelines
  ARCHITECTURE.md          # system architecture walkthrough
  .github/
    CODEOWNERS             # github owners configuration file
```

## 4. Configuration

Configuration is stored in a `config.json` file at the project root, not in
environment variables, because the photos folder needs to be settable from
the phone at runtime rather than fixed before the server starts.

```json
{
  "photos_dir": null,
  "port": 8000
}
```

- On startup, if `config.json` doesn't exist, create it with `photos_dir`
  set to `null` and `port` set to `8000`.
- `PORT` can still be overridden by an environment variable for convenience,
  but `photos_dir` is only ever set through the app itself (see section 6.1
  below) — never through an environment variable or a hardcoded default
  folder, since the whole point is that you choose the folder yourself,
  including from your iPhone.
- If `photos_dir` is `null` or points at a path that no longer exists, the
  server should still start (so the setup screen is reachable) but
  `/api/media` should return an empty list and a flag telling the frontend
  to show the setup screen instead of the photo grid.

Print the laptop's usable URL when the server starts, and the currently
configured photos folder (or "not yet configured"), e.g.:

```
PhotoBridge running!
Local:  http://localhost:8000
Phone:  http://<this-machine-LAN-IP>:8000   (same WiFi)
Photos folder: not yet configured — open the app and complete setup
```

## 5. Backend behavior

### 5.1 Filesystem scanning (`scanner.py`)

- Recursively walk `PHOTOS_DIR`.
- Accepted image extensions: `.jpg .jpeg .png .heic .heif .gif .webp`
- Accepted video extensions: `.mp4 .mov .m4v`
- Ignore all other files.
- Each top-level subfolder under `PHOTOS_DIR` becomes an "album" name; files
  directly in `PHOTOS_DIR` belong to album `"All Photos"`.
- For each image file, try to read EXIF `DateTimeOriginal` (fall back to
  `DateTime`, then to file modified time if no EXIF present at all).
- For each video file, use file modified time (no EXIF parsing needed for
  video in v1).
- Build an in-memory list of media objects:
  ```python
  {
    "id": str,            # URL-safe id derived from the relative path (e.g. base64)
    "rel_path": str,
    "filename": str,
    "album": str,
    "type": "image" | "video",
    "date_taken": str,     # ISO 8601
    "size_bytes": int
  }
  ```
- Sort newest-first by `date_taken`.
- Expose a function to rebuild this index on demand (called at startup and
  by the `/api/rescan` endpoint).
- ID encoding: base64-url-encode the relative path so it's safe to put in a
  URL, and can be decoded back to look up the file on disk. Never expose raw
  filesystem paths to the client.

### 5.2 API endpoints (`main.py`)

- `GET /api/config` → returns the current config, e.g.
  `{"photos_dir": "C:\\Users\\you\\Pictures", "configured": true}` or
  `{"photos_dir": null, "configured": false}` if nothing has been set yet.
- `POST /api/config` → body `{"photos_dir": "<absolute path>"}`. Validates
  that the path exists on the server's filesystem and is a directory
  (return `400` with a clear error message if not — e.g. "That folder
  doesn't exist on this laptop" — since a path typed on the phone must
  refer to something on the laptop's disk, not the phone's). On success,
  writes it to `config.json`, triggers a rescan, and returns
  `{"photos_dir": "...", "count": <int>}`.
- `POST /api/select-folder` → Opens the native Windows folder selection dialog
  on the server (laptop) using Tkinter and returns the selected path:
  `{"path": "<absolute path>"}` (or `{"path": null}` if cancelled). Helps
  avoid manual path typing on phones.
- `GET /api/media` → returns the full JSON list of media objects (from the
  current in-memory index). Returns an empty list if `photos_dir` isn't
  configured yet.
- `POST /api/rescan` → rebuilds the index using the currently configured
  `photos_dir`, returns `{"count": <int>}`. Returns `400` if no directory is
  configured yet.
- `GET /api/thumb/{id}?w=300` → for images, returns a JPEG thumbnail resized
  so its longer side is `w` pixels (default 300), generated with Pillow,
  with `Cache-Control: public, max-age=86400`. If Pillow fails to decode the
  file (e.g. unsupported HEIC variant), fall back to streaming the original
  file unresized rather than erroring. For videos, return `204 No Content`
  — the frontend shows a placeholder tile for videos instead of a thumbnail.
- `GET /api/full/{id}` → streams the original file with the correct
  `Content-Type`. Must support **HTTP range requests** (`Range` header) so
  videos can be scrubbed/seeked in the browser without downloading the whole
  file first — return `206 Partial Content` with `Content-Range` and
  `Accept-Ranges: bytes` when a `Range` header is present.
- `GET /api/download/{id}` → same as `/api/full/{id}` but sets
  `Content-Disposition: attachment; filename="..."` so the browser treats it
  as a download rather than an inline view. Used by the "Save to Photos"
  button.
- Serve everything under `static/` as the app's frontend (mount as static
  files, with `index.html` served at `/`).

### 5.3 Error handling

- Return `404` for unknown ids.
- Never crash the whole process on a single bad/corrupt file during
  scanning — log and skip it.

## 6. Frontend behavior (`static/app.js`, `index.html`, `style.css`)

Build a single-page app, no framework, targeting Mobile Safari:

### 6.1 Setup / Settings screen

- On load, call `GET /api/config`. If `configured` is `false`, show a
  full-screen setup view instead of the photo grid:
  - A short explanation: "Enter the full path to the folder on your laptop
    you want to browse — e.g. `C:\Users\yourname\Pictures`."
  - A text input for the path and a "Connect" button.
  - On submit, `POST /api/config`. If the server returns a `400` (path
    doesn't exist), show the error message inline and let them try again.
    On success, load the grid as normal.
- A gear icon in the top bar (visible any time, not just during setup)
  opens the same screen pre-filled with the current path, so the folder can
  be changed later — e.g. if you reorganize where photos live on the
  laptop, or want to point it at a different folder temporarily — without
  restarting the server.
- Since this path is typed on the iPhone but must resolve on the laptop's
  filesystem, the setup screen's copy should be explicit that it's the
  laptop's folder path, not anything on the phone.

- **Top bar**: three tabs — "All Photos", "Albums", "Favorites" — plus a
  text search box that filters by filename substring, live as you type.
- **Album bar**: shown only under the "Albums" tab — horizontally scrollable
  chips, one per album name, tapping one filters the grid to that album.
- **Grid**: media grouped under sticky date headers (e.g. "July 5, 2026"),
  grouped by calendar day of `date_taken`, newest first. Responsive CSS grid
  of square thumbnails (`object-fit: cover`), lazy-loaded
  (`loading="lazy"`), pointing at `/api/thumb/{id}?w=300`. Video tiles show
  a placeholder (filename + a small "play" indicator) since there's no
  video thumbnail endpoint.
- **Favorites**: a heart icon in the full-screen viewer toggles favorite
  status for the currently viewed item; favorite ids are stored as a JSON
  array in `localStorage`. The "Favorites" tab filters the grid to only
  favorited ids.
- **Full-screen viewer**: opens when a grid tile is tapped. Shows the
  full-resolution image (`/api/full/{id}`) or a native `<video>` element
  with controls for video items. Supports:
  - swipe left/right (touch events) to move to the previous/next item
  - left/right arrow keys on desktop
  - an on-screen close button
  - previous/next chevron buttons
  - a slideshow mode that auto-advances every ~3.5 seconds
- **Save to Photos button**: in the viewer, fetches
  `/api/download/{id}`, builds a `File` from the blob, and:
  - if `navigator.canShare({files:[file]})` is supported, calls
    `navigator.share({files:[file]})` — this opens iOS's native share
    sheet, where the user taps "Save Image" / "Save Video" to save directly
    into the Photos app.
  - otherwise falls back to a normal anchor-tag download and shows a toast
    telling the user to long-press the image and choose "Add to Photos".
- **Pull-to-rescan**: a simple touch-based pull gesture at the top of the
  grid (when already scrolled to the top) that calls `POST /api/rescan`
  then reloads `/api/media`, so newly-added files show up without
  restarting the server.
- **PWA**:
  - `manifest.json` with `display: standalone`, dark background/theme
    colors, and both icon sizes.
  - `sw.js` service worker that caches only the static app-shell files
    (`/`, `/style.css`, `/app.js`, `/manifest.json`) — must NOT cache
    anything under `/api/` so photo data always stays fresh.
  - `<link rel="apple-touch-icon">` and
    `<meta name="apple-mobile-web-app-capable" content="yes">` in
    `index.html` so "Add to Home Screen" on iOS gives a full-screen app
    with no browser chrome.
- **Visual style**: dark theme (black background, white text) to match the
  iOS Photos app's dark mode aesthetic. No external UI framework — plain
  CSS.

## 7. `requirements.txt`

```
fastapi
uvicorn[standard]
pillow
pillow-heif
python-multipart
```

## 8. `run.py`

A tiny entry point that reads `PORT` from the environment and starts
uvicorn against `app.main:app`, binding to `0.0.0.0` (not just `localhost`)
so the phone can reach it over LAN.

## 9. README.md — must include

1. Prerequisites: Python 3.11+ installed on Windows.
2. `pip install -r requirements.txt`.
3. How to run: Double-click `run_control_center.bat` to launch the native desktop Control Center (runs without background console popups, supports one-time firewall setup, checks status, and starts/stops the server invisibly). Day-to-day console execution can also be started with `run_app.bat` or `python run.py`.
4. Dynamic LAN IP detection and startup banner instructions.
5. How to open it on iPhone Safari, complete the one-time setup screen by entering the full path to an existing folder on the laptop (e.g. `C:\Users\you\Pictures`), configuring an optional Access PIN, and "Add to Home Screen".
6. How to change the folder or security PIN later via the gear icon settings modal in the app.
7. A short note that the laptop must stay awake and on the same WiFi network
   for the phone to reach it, and a pointer to using Task Scheduler or NSSM
   if they want it running continuously as a background service.
8. Known limitation: HEIC thumbnail generation depends on `pillow-heif`
   installing correctly; if it fails, the app still works because Mobile
   Safari can render HEIC natively — only thumbnail file size is affected,
   not functionality.
9. Note that `config.json` stores the chosen folder path between restarts,
   and should be added to `.gitignore` since it's machine-specific.

## 10. Suggested build order (do these as separate Copilot passes)

1. `config.py` — read/write `config.json`, expose `get_config()` /
   `set_photos_dir(path)` with path-exists validation.
2. `scanner.py` — filesystem walk and EXIF/id logic, working and
   unit-testable on its own, independent of any web framework.
3. `main.py` with `/api/config` (GET + POST), `/api/media`, and
   `/api/rescan` — verify with `curl`/browser that setting a folder via
   `POST /api/config` actually causes `/api/media` to populate.
4. Add `/api/thumb`, `/api/full`, `/api/download`, including range-request
   support for video — test scrubbing a video in the browser directly.
5. Static frontend shell: `index.html` + `style.css` + the setup screen
   (section 6.1) wired to `/api/config`, then basic grid rendering from
   `/api/media` once configured.
6. Full-screen viewer: image/video display, swipe/keyboard nav.
7. Favorites, search, albums tab.
8. Save-to-Photos button + Web Share API integration.
9. PWA manifest, icons, service worker, "Add to Home Screen" polish.
10. Pull-to-rescan gesture, and the gear-icon Settings screen for changing
    the folder later.
11. README + final pass on error handling (corrupt files, missing folder,
    unsupported formats, invalid paths typed into setup).

## 11. Manual test checklist before calling it done

- [ ] Server starts and prints the LAN URL, with "not yet configured" shown
      before any folder has been chosen.
- [ ] From the iPhone, typing in a valid laptop folder path on the setup
      screen successfully loads that folder's photos.
- [ ] Typing an invalid/nonexistent path shows a clear inline error instead
      of a blank screen or crash.
- [ ] Changing the folder later via the gear icon updates the grid to the
      new folder's contents.
- [ ] Adding a new file to the configured photos folder and rescanning
      shows it in the grid without restarting the server.
- [ ] Thumbnails load for JPEG, PNG, and HEIC files.
- [ ] Opening a video in the viewer plays it and allows scrubbing.
- [ ] Swipe left/right in the viewer moves between items.
- [ ] Favoriting an item and switching to the Favorites tab shows only that
      item, and it persists after a page reload.
- [ ] Search filters the grid by filename as you type.
- [ ] Tapping Save on an iPhone opens the native share sheet and "Save
      Image"/"Save Video" actually adds it to the Photos app.
- [ ] "Add to Home Screen" produces a full-screen icon with no Safari UI
      chrome.
- [ ] The whole flow works from an iPhone on the same WiFi network, not
      just from the laptop's own browser.
- [ ] **Albums Grid Redesign**: Albums tab displays as a full-screen card grid with cover photos and counts, and tapping one displays its photos with a back navigation button.
- [ ] **Viewer Controls**: Controls are circular SVG button icons with tap scale animations and an animated iOS red favorite heart.
- [ ] **LAN Security Protection**: Settings modification and folder browser calls are rejected with 403 Forbidden on remote devices, and unauthorized devices are presented with a glassmorphic PIN lock screen before receiving media.